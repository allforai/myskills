import json
import subprocess
import sys
from pathlib import Path

import pytest

from view_copy import view_copies, MAX_EDGE

PIL = pytest.importorskip('PIL')
from PIL import Image  # noqa: E402


def _png(path, w, h):
    img = Image.effect_noise((w, h), 64).convert('RGB')   # noise resists PNG compression: big files on purpose
    img.save(path)
    return path


def test_small_image_is_used_as_is(tmp_path):
    p = _png(tmp_path / 'a.png', 1440, 900)
    rec = view_copies(p, max_bytes=50_000_000)
    assert rec['action'] == 'as_is' and rec['views'][0]['path'] == str(p)
    assert not (tmp_path / 'view').exists()


def test_wide_image_is_downscaled_into_view_dir(tmp_path):
    p = _png(tmp_path / 'wide.png', 3000, 1200)
    rec = view_copies(p)
    assert rec['action'] == 'downscaled'
    v = rec['views'][0]
    assert Path(v['path']).parent == tmp_path / 'view' and max(v['size']) <= MAX_EDGE
    assert p.stat().st_size == rec['bytes']   # original untouched


def test_tall_page_is_tiled_each_tile_within_budget(tmp_path):
    p = _png(tmp_path / 'full.png', 1400, 12000)
    rec = view_copies(p, max_bytes=300_000)
    assert rec['action'] == 'tiled' and len(rec['views']) >= 7
    covered = 0
    for v in rec['views']:
        assert max(v['size']) <= MAX_EDGE and v['bytes'] <= 300_000
        x0, y0, x1, y1 = v['region']
        assert y0 == covered and x0 == 0 and x1 == 1400
        covered = y1
    assert covered == 12000
    ow, oh = rec['overview']['size']
    assert max(ow, oh) <= MAX_EDGE and rec['overview']['bytes'] <= 300_000
    assert min(ow, oh) >= MAX_EDGE // 4   # a grid of tiles, not a hairline strip of the whole page


def test_oversized_bytes_alone_triggers_downscale(tmp_path):
    p = _png(tmp_path / 'noisy.png', 1500, 1500)
    rec = view_copies(p, max_bytes=100_000)
    assert rec['action'] == 'downscaled' and rec['views'][0]['bytes'] <= 100_000


def test_cli_prints_json(tmp_path):
    p = _png(tmp_path / 'a.png', 100, 100)
    out = subprocess.run([sys.executable, str(Path(__file__).parent / 'view_copy.py'), str(p)],
                         capture_output=True, text=True, check=True).stdout
    assert json.loads(out)[0]['action'] == 'as_is'
