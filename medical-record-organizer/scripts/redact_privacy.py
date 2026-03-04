#!/usr/bin/env python3
"""
redact_privacy.py — Draw black rectangles over PII regions in images.

Usage:
    python3 redact_privacy.py INPUT --regions "x1,y1,x2,y2;x1,y1,x2,y2" [--output OUTPUT]

Coordinates are percentages (0–100) of image width/height.

Output JSON:
    {"success": true, "output": "path/to/file_redacted.jpg", "regions_applied": 3}
    {"success": false, "error": "..."}
"""

import argparse
import json
import sys
from pathlib import Path


def parse_regions(regions_str: str) -> list[tuple[float, float, float, float]]:
    regions = []
    for part in regions_str.split(";"):
        part = part.strip()
        if not part:
            continue
        coords = [float(v) for v in part.split(",")]
        if len(coords) != 4:
            raise ValueError(f"Region must have 4 coordinates, got: {part}")
        x1, y1, x2, y2 = coords
        if not all(0 <= v <= 100 for v in (x1, y1, x2, y2)):
            raise ValueError(f"Coordinates must be in range 0–100, got: {part}")
        regions.append((x1, y1, x2, y2))
    return regions


def redact_image(input_path: Path, regions: list[tuple[float, float, float, float]], output_path: Path) -> int:
    from PIL import Image, ImageDraw

    img = Image.open(input_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size

    for x1_pct, y1_pct, x2_pct, y2_pct in regions:
        x1 = int(x1_pct / 100 * width)
        y1 = int(y1_pct / 100 * height)
        x2 = int(x2_pct / 100 * width)
        y2 = int(y2_pct / 100 * height)
        draw.rectangle([x1, y1, x2, y2], fill="black")

    img.save(output_path)
    return len(regions)


def main():
    parser = argparse.ArgumentParser(description="Redact PII regions in images with black rectangles.")
    parser.add_argument("input", help="Path to input image file")
    parser.add_argument("--regions", required=True, help='Semicolon-separated list of "x1,y1,x2,y2" percentage regions')
    parser.add_argument("--output", help="Output file path (default: [name]_redacted.[ext])")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(json.dumps({"success": False, "error": f"Input file not found: {input_path}"}))
        sys.exit(1)

    suffix = input_path.suffix.lower()
    supported = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    if suffix not in supported:
        print(json.dumps({"success": False, "error": f"Unsupported file type: {suffix}. Supported: {', '.join(supported)}"}))
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = input_path.parent / f"{input_path.stem}_redacted{input_path.suffix}"

    try:
        regions = parse_regions(args.regions)
    except ValueError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

    if not regions:
        print(json.dumps({"success": False, "error": "No valid regions provided"}))
        sys.exit(1)

    try:
        count = redact_image(input_path, regions, output_path)
        print(json.dumps({"success": True, "output": str(output_path), "regions_applied": count}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
