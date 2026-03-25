# Media Processing Command Reference

> media-forge M3.5 step loads this document on demand. Common image/video processing commands, ready to copy and execute.

---

## Image Operations

### AI Super-Resolution (Real-ESRGAN)

```bash
# 2x upscale (recommended, speed/quality balance)
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2 -n realesrgan-x4plus

# 4x upscale (major enhancement, slower)
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 4 -n realesrgan-x4plus

# Anime/illustration style model
realesrgan-ncnn-vulkan -i input.jpg -o output.png -s 2 -n realesrgan-x4plus-anime
```

### Convert to WebP

```bash
# Single file (quality 85, recommended balance)
cwebp -q 85 input.png -o output.webp

# Max file size (200KB, suitable for avatars)
cwebp -size 200000 input.png -o output.webp

# Lossless conversion
cwebp -lossless input.png -o output.webp

# Via ffmpeg
ffmpeg -i input.png -quality 85 output.webp
```

### Resize

```bash
# Scale to width, auto height
ffmpeg -i input.jpg -vf "scale=800:-1" output.jpg

# Scale to exact size (may distort)
ffmpeg -i input.jpg -vf "scale=800:800" output.jpg

# Scale preserving ratio (pad with black)
ffmpeg -i input.jpg -vf "scale=800:800:force_original_aspect_ratio=decrease,pad=800:800:(ow-iw)/2:(oh-ih)/2:black" output.jpg

# ImageMagick resize
magick input.jpg -resize 800x800 output.jpg
magick input.jpg -resize 800x800^ -gravity center -extent 800x800 output.jpg  # crop fill
```

### Smart Crop

```bash
# Center crop to 1:1
ffmpeg -i input.jpg -vf "crop=min(iw\,ih):min(iw\,ih)" output.jpg

# Specific region crop (w:h:x:y)
ffmpeg -i input.jpg -vf "crop=800:600:100:50" output.jpg

# 16:9 center crop
ffmpeg -i input.jpg -vf "crop=iw:iw*9/16" output.jpg

# 4:3 center crop
ffmpeg -i input.jpg -vf "crop=ih*4/3:ih" output.jpg

# ImageMagick smart crop (auto-detect subject)
magick input.jpg -gravity center -crop 800x800+0+0 +repage output.jpg
```

### Compression

```bash
# WebP compression (most recommended, small size good quality)
cwebp -q 75 input.png -o output.webp

# JPEG quality compression
ffmpeg -i input.jpg -q:v 8 output.jpg

# ImageMagick compression
magick input.jpg -quality 80 -strip output.jpg

# PNG lossless compression
pngquant --quality=65-80 --output output.png input.png
```

### Color/Brightness Unification

```bash
# Adjust brightness and saturation
ffmpeg -i input.jpg -vf "eq=brightness=0.06:saturation=1.2" output.jpg

# Adjust contrast
ffmpeg -i input.jpg -vf "eq=contrast=1.1:brightness=0.02" output.jpg

# Warm color temperature
ffmpeg -i input.jpg -vf "colorbalance=rs=0.1:gs=0:bs=-0.1" output.jpg

# Cool color temperature
ffmpeg -i input.jpg -vf "colorbalance=rs=-0.1:gs=0:bs=0.1" output.jpg

# ImageMagick auto-levels
magick input.jpg -auto-level output.jpg

# ImageMagick match reference color tone
magick input.jpg reference.jpg -clut output.jpg
```

---

## Video Operations

### MOV to MP4

```bash
# Standard conversion (H.264 encoding, best compatibility)
ffmpeg -i input.mov -c:v libx264 -c:a aac -movflags +faststart output.mp4

# Fast conversion (no re-encoding, container swap only)
ffmpeg -i input.mov -c copy output.mp4

# Specified quality (lower CRF = higher quality, 18-28 recommended)
ffmpeg -i input.mov -c:v libx264 -crf 23 -c:a aac output.mp4
```

### Trim Segment

```bash
# From 5s, take 30s (no re-encoding, fast)
ffmpeg -i input.mp4 -ss 00:00:05 -t 00:00:30 -c copy output.mp4

# Precise trim (re-encoding, frame accurate)
ffmpeg -i input.mp4 -ss 00:00:05 -to 00:00:35 -c:v libx264 -c:a aac output.mp4

# Last 15 seconds
ffmpeg -sseof -15 -i input.mp4 -c copy output.mp4
```

### Compress Video

```bash
# Lower bitrate (target 1Mbps)
ffmpeg -i input.mp4 -b:v 1M -c:a aac output.mp4

# CRF compression (recommended, constant quality)
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac output.mp4

# Downscale to 720p
ffmpeg -i input.mp4 -vf "scale=-2:720" -c:v libx264 -crf 23 -c:a aac output.mp4

# Two-pass encoding (best quality/size ratio)
ffmpeg -i input.mp4 -c:v libx264 -b:v 1M -pass 1 -f null /dev/null
ffmpeg -i input.mp4 -c:v libx264 -b:v 1M -pass 2 -c:a aac output.mp4
```

### Extract Thumbnail

```bash
# Extract frame at 3s as cover
ffmpeg -i input.mp4 -ss 00:00:03 -vframes 1 thumbnail.jpg

# Extract multiple frames (one per 10s)
ffmpeg -i input.mp4 -vf "fps=1/10" thumb_%03d.jpg

# Extract and resize
ffmpeg -i input.mp4 -ss 00:00:03 -vframes 1 -vf "scale=400:-1" thumbnail.jpg
```

### Video Mute / Replace Audio

```bash
# Remove audio track
ffmpeg -i input.mp4 -an -c:v copy output.mp4

# Replace audio track
ffmpeg -i input.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
```

---

## Batch Operations

### Batch Convert to WebP

```bash
# All PNG in current directory to WebP
for f in *.png; do cwebp -q 85 "$f" -o "${f%.png}.webp"; done

# All JPG in current directory to WebP
for f in *.jpg; do cwebp -q 85 "$f" -o "${f%.jpg}.webp"; done

# Recursive subdirectories
find assets/ -name "*.png" -exec sh -c 'cwebp -q 85 "$1" -o "${1%.png}.webp"' _ {} \;
```

### Batch Resize

```bash
# All images to max 800px width
for f in assets/covers/*.jpg; do
  ffmpeg -i "$f" -vf "scale='min(800,iw)':-1" "${f%.jpg}_resized.jpg" -y
done

# ImageMagick batch
magick mogrify -resize 800x800 assets/avatars/*.jpg
```

### Batch Super-Resolution

```bash
# All images in directory 2x upscale
for f in assets/details/*.jpg; do
  realesrgan-ncnn-vulkan -i "$f" -o "${f%.jpg}_2x.png" -s 2
done
```

### Batch Rename (naming convention)

```bash
# Rename files sequentially as IMG-001.webp, IMG-002.webp ...
cd assets/covers
i=1
for f in *.webp; do
  mv "$f" "$(printf 'IMG-%03d.webp' $i)"
  i=$((i + 1))
done
```

---

## Tool Installation (macOS)

```bash
# ffmpeg (video/image all-purpose tool)
brew install ffmpeg

# cwebp (WebP encoder)
brew install webp

# ImageMagick (image processing)
brew install imagemagick

# Real-ESRGAN (AI super-resolution)
# Download prebuilt binary from GitHub:
# https://github.com/xinntao/Real-ESRGAN/releases
# Extract and place realesrgan-ncnn-vulkan in PATH

# pngquant (PNG compression)
brew install pngquant
```

## Tool Installation (Linux / Ubuntu)

```bash
sudo apt install ffmpeg webp imagemagick pngquant

# Real-ESRGAN: same as above, download Linux prebuilt version
```
