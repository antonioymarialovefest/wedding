#!/usr/bin/env python3
"""Add watermark and web-optimized versions of images preserving folder structure.

Usage example:
python3 tools/add_watermark.py \
    --input assets/images/fotos \
    --output assets/images/fotos2 \
    --text "© Antonio y Maria" \
    --max-side 1600 \
    --jpeg-quality 82 \
    --manifest assets/images/fotos2/manifest.json
"""
import argparse
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

def find_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def resize_for_web(image, max_side):
    w, h = image.size
    longest = max(w, h)
    if longest <= max_side:
        return image
    ratio = max_side / float(longest)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def save_optimized(image_rgba, out_path, input_format, ext, jpeg_quality):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Keep transparency only for formats that support it.
    if ext in (".png", ".webp"):
        image_to_save = image_rgba
    else:
        image_to_save = image_rgba.convert("RGB")

    if ext in (".jpg", ".jpeg"):
        image_to_save = image_to_save.convert("RGB")
        image_to_save.save(
            out_path,
            format="JPEG",
            quality=jpeg_quality,
            optimize=True,
            progressive=True,
        )
        return

    if ext == ".webp":
        image_to_save.save(out_path, format="WEBP", quality=jpeg_quality, method=6)
        return

    if ext == ".png":
        image_to_save.save(out_path, format="PNG", optimize=True)
        return

    fmt = input_format if input_format else "PNG"
    image_rgba.convert("RGB").save(out_path, format=fmt)


def apply_watermark(
    img_path,
    out_path,
    text,
    opacity=128,
    scale=0.05,
    margin_ratio=0.02,
    max_side=1600,
    jpeg_quality=82,
    position="bottom-right",
    y_offset_ratio=0.0,
):
    with Image.open(img_path) as original:
        input_format = original.format
        base_rgb = original.convert("RGB")
        base_rgb = resize_for_web(base_rgb, max_side)
        base = base_rgb.convert("RGBA")
        w, h = base.size
        txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # estimate font size relative to image
        font_size = max(12, int(min(w, h) * scale))
        font = find_font(font_size)

        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            try:
                text_w, text_h = font.getsize(text)
            except Exception:
                text_w, text_h = (int(font_size * len(text) * 0.6), font_size)
        margin = int(min(w, h) * margin_ratio)
        if position == "center":
            x = (w - text_w) // 2
            y = (h - text_h) // 2
        else:
            x = w - text_w - margin
            y = h - text_h - margin

        y += int(h * y_offset_ratio)

        # Keep text within image bounds after applying offset.
        y = max(margin, min(y, h - text_h - margin))

        if position != "center":
            # draw outline for better contrast in corner mode
            outline_color = (0, 0, 0, int(opacity * 0.8))
            for ox, oy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((x + ox, y + oy), text, font=font, fill=outline_color)

        fill_color = (255, 255, 255, opacity)
        draw.text((x, y), text, font=font, fill=fill_color)

        combined = Image.alpha_composite(base, txt_layer)
        ext = os.path.splitext(out_path)[1].lower()
        save_optimized(combined, out_path, input_format, ext, jpeg_quality)


def generate_manifest(output_dir, manifest_path):
    manifest = {}
    supported = (".jpg", ".jpeg", ".png", ".webp")
    for entry in sorted(os.listdir(output_dir)):
        year_dir = os.path.join(output_dir, entry)
        if not os.path.isdir(year_dir):
            continue
        files = []
        for item in sorted(os.listdir(year_dir)):
            item_path = os.path.join(year_dir, item)
            if os.path.isfile(item_path) and item.lower().endswith(supported):
                files.append(item)
        if files:
            manifest[entry] = files

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input directory with images")
    parser.add_argument("--output", required=True, help="Output directory for watermarked images")
    parser.add_argument("--text", default="© Wending", help="Watermark text")
    parser.add_argument("--opacity", type=int, default=140, help="Text opacity 0-255")
    parser.add_argument("--scale", type=float, default=0.05, help="Watermark text size as ratio of shortest side")
    parser.add_argument("--max-side", type=int, default=1600, help="Maximum size of the longest side")
    parser.add_argument("--jpeg-quality", type=int, default=82, help="JPEG/WEBP quality 1-100")
    parser.add_argument("--position", choices=["bottom-right", "center"], default="bottom-right", help="Watermark position")
    parser.add_argument("--y-offset-ratio", type=float, default=0.0, help="Vertical watermark offset as ratio of image height")
    parser.add_argument("--manifest", help="Optional output manifest JSON path")
    args = parser.parse_args()

    supported = ('.jpg', '.jpeg', '.png', '.webp')
    os.makedirs(args.output, exist_ok=True)
    files = []
    for root, dirnames, filenames in os.walk(args.input):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in filenames:
            if fn.startswith('.'):
                continue
            if fn.lower().endswith(supported):
                in_path = os.path.join(root, fn)
                rel_path = os.path.relpath(in_path, args.input)
                out_path = os.path.join(args.output, rel_path)
                files.append((in_path, out_path, rel_path))

    if not files:
        print('No supported images found in', args.input)
        return

    files.sort(key=lambda x: x[2])
    for in_path, out_path, rel_path in files:
        try:
            apply_watermark(
                in_path,
                out_path,
                args.text,
                opacity=args.opacity,
                scale=args.scale,
                max_side=args.max_side,
                jpeg_quality=args.jpeg_quality,
                position=args.position,
                y_offset_ratio=args.y_offset_ratio,
            )
            print('Processed', rel_path)
        except Exception as e:
            print('Failed', rel_path, e)

    if args.manifest:
        generate_manifest(args.output, args.manifest)
        print('Manifest written to', args.manifest)

if __name__ == '__main__':
    main()
