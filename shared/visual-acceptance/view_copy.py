"""看图副本：把超出模型看图预算的原图变成模型能打开的副本，原图不动。

原图是证据（摘要、探测窗口都绑它）；模型看的是副本。超预算的图直接送进模型，API 会整轮拒收
（`Downloaded image content cannot exceed 30MB` 一类），token 照扣，重试只会再扣一次。
预算是两条：单张字节数、长边像素。长边超出模型分辨率的图会被服务端缩到同样的尺寸，先缩再送只省不亏；
很长的整页截图缩到长边预算会把小字压没，所以按长轴切片，每片自己都在预算内，另给一张把切片按阅读顺序排成网格的总览：
看图先看总览，问题要读小字或局部时才开对应切片——够用就停，每多开一张都是 token。

用法：python3 view_copy.py <原图>... [--max-edge 1568] [--max-bytes 4000000] [--out-dir DIR]
stdout 是 JSON 数组，每张原图一条：{original, bytes, size, action: as_is|downscaled|tiled, views: [{path, bytes, size, region}],
overview?: {path, bytes, size}}（仅 tiled 有 overview）。
副本默认写到原图旁的 `view/` 子目录，永远不覆盖原图；as_is 的图不写副本，views 指向原图本身。
"""
import argparse
import json
import sys
from pathlib import Path

MAX_EDGE = 1568          # 长边像素预算：常见视觉模型的输入分辨率上限，再大也会被服务端缩到这里
MAX_BYTES = 2_000_000    # 单张字节预算：长边 1568 的 JPEG 通常远低于此；它是上限不是目标
TILE_ASPECT = 3          # 长宽比超过它的图按切片处理，而不是整体缩小
QUALITIES = (85, 70, 55)


def _open(path):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = 400_000_000   # 全页截图合法地超过 Pillow 的默认炸弹阈值
    img = Image.open(path)
    img.load()
    return img.convert('RGB') if img.mode not in ('RGB', 'L') else img


def _save(img, dest, max_bytes):
    """先降质量，仍超字节预算就缩边长；边长缩到 256 以下还超就放弃（返回的 bytes 说明一切）。"""
    while True:
        for quality in QUALITIES:
            img.save(dest, 'JPEG', quality=quality, optimize=True)
            if dest.stat().st_size <= max_bytes:
                return {'path': str(dest), 'bytes': dest.stat().st_size, 'size': list(img.size)}
        if max(img.size) < 256:
            return {'path': str(dest), 'bytes': dest.stat().st_size, 'size': list(img.size)}
        img = img.resize((max(1, round(img.width * 0.7)), max(1, round(img.height * 0.7))))


def _fit(img, max_edge):
    from PIL import Image
    scale = max_edge / max(img.size)
    if scale >= 1:
        return img
    return img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)


def _contact_sheet(img, regions, max_edge):
    """整体缩到长边预算的超长图只剩一条细线，看不出任何东西；把切片按阅读顺序排成网格才是可看的总览。"""
    import math
    from PIL import Image
    n = len(regions)
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)
    x0, y0, x1, y1 = regions[0]
    tw, th = x1 - x0, y1 - y0
    cell_w = max_edge // cols
    cell_h = max(1, round(cell_w * th / tw))
    if cell_h * rows > max_edge:
        cell_h = max_edge // rows
        cell_w = max(1, round(cell_h * tw / th))
    sheet = Image.new('RGB', (cell_w * cols, cell_h * rows), 'white')
    for i, box in enumerate(regions):
        tile = img.crop(box).resize((cell_w, max(1, round(cell_w * (box[3] - box[1]) / (box[2] - box[0])))), Image.LANCZOS)
        sheet.paste(tile, ((i % cols) * cell_w, (i // cols) * cell_h))
    return sheet


def view_copies(path, max_edge=MAX_EDGE, max_bytes=MAX_BYTES, out_dir=None):
    path = Path(path)
    size = path.stat().st_size
    img = _open(path)
    record = {'original': str(path), 'bytes': size, 'size': list(img.size)}
    if size <= max_bytes and max(img.size) <= max_edge:
        record.update(action='as_is', views=[{'path': str(path), 'bytes': size, 'size': list(img.size),
                                              'region': [0, 0, img.width, img.height]}])
        return record
    out = Path(out_dir) if out_dir else path.parent / 'view'
    out.mkdir(parents=True, exist_ok=True)
    w, h = img.size
    if max(w, h) / min(w, h) > TILE_ASPECT and max(w, h) > max_edge:
        # 先把短边压进预算，再沿长轴切成每片都在预算内的段
        scale = min(1.0, max_edge / min(w, h))
        views = []
        step = int(max_edge / scale)   # 原图坐标下每片的长度
        for n, start in enumerate(range(0, max(w, h), step), 1):
            end = min(start + step, max(w, h))
            box = (0, start, w, end) if h >= w else (start, 0, end, h)
            tile = _fit(img.crop(box), max_edge)
            view = _save(tile, out / f'{path.stem}.view-{n:02d}.jpg', max_bytes)
            view['region'] = list(box)
            views.append(view)
        overview = _save(_contact_sheet(img, [v['region'] for v in views], max_edge),
                         out / f'{path.stem}.overview.jpg', max_bytes)
        record.update(action='tiled', views=views, overview=overview)
        return record
    view = _save(_fit(img, max_edge), out / f'{path.stem}.view.jpg', max_bytes)
    view['region'] = [0, 0, w, h]
    record.update(action='downscaled', views=[view])
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('images', nargs='+')
    parser.add_argument('--max-edge', type=int, default=MAX_EDGE)
    parser.add_argument('--max-bytes', type=int, default=MAX_BYTES)
    parser.add_argument('--out-dir')
    args = parser.parse_args(argv)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print('需要 Pillow：pip install Pillow', file=sys.stderr)
        return 2
    records = [view_copies(p, args.max_edge, args.max_bytes, args.out_dir) for p in args.images]
    json.dump(records, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
