# 素材加工命令参考

> media-forge M3.5 步骤按需加载本文档。收录常用图片/视频加工命令，可直接复制执行。

---

## 图片操作

### AI 超分辨率（Real-ESRGAN）

```bash
# 2x 超分（推荐，速度与质量平衡）
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2 -n realesrgan-x4plus

# 4x 超分（大幅提升，耗时更长）
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 4 -n realesrgan-x4plus

# 动漫/插画风格专用模型
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2 -n realesrgan-x4plus-anime
```

### 转换为 WebP

```bash
# 单文件转换（质量 85，推荐平衡点）
cwebp -q 85 input.png -o output.webp

# 指定最大文件大小（200KB，适合头像）
cwebp -size 200000 input.png -o output.webp

# 无损转换
cwebp -lossless input.png -o output.webp

# 用 ffmpeg 转换
ffmpeg -i input.png -quality 85 output.webp
```

### 调整尺寸

```bash
# 缩放到指定宽度，高度自适应
ffmpeg -i input.jpg -vf "scale=800:-1" output.jpg

# 缩放到指定尺寸（可能变形）
ffmpeg -i input.jpg -vf "scale=800:800" output.jpg

# 缩放并保持比例（填充黑边）
ffmpeg -i input.jpg -vf "scale=800:800:force_original_aspect_ratio=decrease,pad=800:800:(ow-iw)/2:(oh-ih)/2:black" output.jpg

# ImageMagick 调整
magick input.jpg -resize 800x800 output.jpg
magick input.jpg -resize 800x800^ -gravity center -extent 800x800 output.jpg  # 裁剪填充
```

### 智能裁剪

```bash
# 居中裁剪为 1:1
ffmpeg -i input.jpg -vf "crop=min(iw\,ih):min(iw\,ih)" output.jpg

# 指定区域裁剪（w:h:x:y）
ffmpeg -i input.jpg -vf "crop=800:600:100:50" output.jpg

# 16:9 居中裁剪
ffmpeg -i input.jpg -vf "crop=iw:iw*9/16" output.jpg

# 4:3 居中裁剪
ffmpeg -i input.jpg -vf "crop=ih*4/3:ih" output.jpg

# ImageMagick 智能裁剪（自动检测主体）
magick input.jpg -gravity center -crop 800x800+0+0 +repage output.jpg
```

### 压缩

```bash
# WebP 压缩（最推荐，体积小质量好）
cwebp -q 75 input.png -o output.webp

# JPEG 质量压缩
ffmpeg -i input.jpg -q:v 8 output.jpg

# ImageMagick 压缩
magick input.jpg -quality 80 -strip output.jpg

# PNG 无损压缩
pngquant --quality=65-80 --output output.png input.png
```

### 色调/亮度统一

```bash
# 调整亮度和饱和度
ffmpeg -i input.jpg -vf "eq=brightness=0.06:saturation=1.2" output.jpg

# 调整对比度
ffmpeg -i input.jpg -vf "eq=contrast=1.1:brightness=0.02" output.jpg

# 色温偏暖
ffmpeg -i input.jpg -vf "colorbalance=rs=0.1:gs=0:bs=-0.1" output.jpg

# 色温偏冷
ffmpeg -i input.jpg -vf "colorbalance=rs=-0.1:gs=0:bs=0.1" output.jpg

# ImageMagick 自动色阶
magick input.jpg -auto-level output.jpg

# ImageMagick 匹配参考图色调
magick input.jpg reference.jpg -clut output.jpg
```

---

## 视频操作

### MOV 转 MP4

```bash
# 标准转换（H.264 编码，兼容性最好）
ffmpeg -i input.mov -c:v libx264 -c:a aac -movflags +faststart output.mp4

# 快速转换（不重新编码，仅换容器）
ffmpeg -i input.mov -c copy output.mp4

# 指定质量（CRF 越低质量越高，18-28 推荐）
ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac output.mp4
```

### 裁剪片段

```bash
# 从第 5 秒开始，截取 30 秒（不重编码，速度快）
ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4

# 精确裁剪（重编码，帧精确）
ffmpeg -i input.mp4 -ss 00:00:05 -to 00:00:35 -c:v libx264 -c:a aac output.mp4

# 截取最后 15 秒
ffmpeg -sseof -15 -i input.mp4 -c copy output.mp4
```

### 压缩视频

```bash
# 降低码率（目标 1Mbps）
ffmpeg -i input.mp4 -b:v 1M -c:a aac output.mp4

# CRF 压缩（推荐，质量恒定）
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac output.mp4

# 降低分辨率到 720p
ffmpeg -i input.mp4 -vf "scale=-2:720" -c:v libx264 -crf 23 -c:a aac output.mp4

# 两遍编码（最佳质量/体积比）
ffmpeg -i input.mp4 -c:v libx264 -b:v 1M -pass 1 -f null /dev/null
ffmpeg -i input.mp4 -c:v libx264 -b:v 1M -pass 2 -c:a aac output.mp4
```

### 提取缩略图

```bash
# 提取第 3 秒的帧作为封面
ffmpeg -i input.mp4 -ss 00:00:03 -vframes 1 thumbnail.jpg

# 提取多帧（每 10 秒一帧）
ffmpeg -i input.mp4 -vf "fps=1/10" thumb_%03d.jpg

# 提取并调整尺寸
ffmpeg -i input.mp4 -ss 00:00:03 -vframes 1 -vf "scale=400:-1" thumbnail.jpg
```

### 视频静音 / 替换音轨

```bash
# 移除音轨
ffmpeg -i input.mp4 -an -c:v copy output.mp4

# 替换音轨
ffmpeg -i input.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
```

---

## 批量操作

### 批量转 WebP

```bash
# 当前目录所有 PNG 转 WebP
for f in *.png; do cwebp -q 85 "$f" -o "${f%.png}.webp"; done

# 当前目录所有 JPG 转 WebP
for f in *.jpg; do cwebp -q 85 "$f" -o "${f%.jpg}.webp"; done

# 递归处理子目录
find assets/ -name "*.png" -exec sh -c 'cwebp -q 85 "$1" -o "${1%.png}.webp"' _ {} \;
```

### 批量调整尺寸

```bash
# 所有图片缩放到最大 800px 宽
for f in assets/covers/*.jpg; do
  ffmpeg -i "$f" -vf "scale='min(800,iw)':-1" "${f%.jpg}_resized.jpg" -y
done

# ImageMagick 批量
magick mogrify -resize 800x800 assets/avatars/*.jpg
```

### 批量超分辨率

```bash
# 目录内所有图片 2x 超分
for f in assets/details/*.jpg; do
  realesrgan-ncnn-vulkan -i "$f" -o "${f%.jpg}_2x.png" -s 2
done
```

### 批量重命名（符合命名规范）

```bash
# 将目录内文件按序重命名为 IMG-001.webp, IMG-002.webp ...
cd assets/covers
i=1
for f in *.webp; do
  mv "$f" "$(printf 'IMG-%03d.webp' $i)"
  i=$((i + 1))
done
```

---

## 工具安装（macOS）

```bash
# ffmpeg（视频/图片全能工具）
brew install ffmpeg

# cwebp（WebP 编码器）
brew install webp

# ImageMagick（图片处理）
brew install imagemagick

# Real-ESRGAN（AI 超分辨率）
# 从 GitHub 下载预编译二进制：
# https://github.com/xinntao/Real-ESRGAN/releases
# 解压后将 realesrgan-ncnn-vulkan 放入 PATH

# pngquant（PNG 压缩）
brew install pngquant
```

## 工具安装（Linux / Ubuntu）

```bash
sudo apt install ffmpeg webp imagemagick pngquant

# Real-ESRGAN 同上，下载 Linux 预编译版本
```
