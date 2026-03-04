#!/usr/bin/env python3
"""
redact_privacy.py — Draw black rectangles over PII regions in medical images.

Usage:
    python3 redact_privacy.py INPUT --regions "x1,y1,x2,y2;x1,y1,x2,y2" [--output OUTPUT]
    python3 redact_privacy.py INPUT --regions "patient_name:15,4.5,35,7;admission_id:52,4.5,72,7"
    python3 redact_privacy.py INPUT --preset cn_lab_report_v1 [--output OUTPUT]
    python3 redact_privacy.py INPUT --preset cn_ct_report_v1 --regions "..." [--output OUTPUT]

Coordinates are percentages (0–100) of image width/height.
By default, percentages are anchored to detected document content area (not full photo canvas)
to avoid over-/under-masking caused by camera borders.

Regions format:
    "x1,y1,x2,y2;x1,y1,x2,y2"                     — unlabeled (backward-compatible)
    "label:x1,y1,x2,y2;label:x1,y1,x2,y2"          — labeled (for LLM-driven precision redaction)

Output JSON:
    {"success": true, "output": "...", "image_size": [W, H], "regions_applied": N, "regions": [...]}
    {"success": false, "error": "..."}
"""

import argparse
import json
import sys
from pathlib import Path


PRESETS: dict[str, list[tuple[float, float, float, float]]] = {
    # Chinese in-patient lab forms: keep middle table visible, mask identity rows + footer signatures/contact.
    "cn_lab_report_v1": [
        (4, 4, 100, 17),       # 姓名/性别/年龄/住院号/床号等身份行
        (78, 0, 100, 20),      # 右上二维码/编号区域（如存在）
        (52, 82, 100, 100),    # 底部签名/电话（右下）
    ],
    # Chinese CT report forms: keep findings+impression area, mask identity rows + footer.
    "cn_ct_report_v1": [
        (4, 6, 100, 20),
        (78, 0, 100, 20),
        (48, 84, 100, 100),
    ],
    # Generic conservative fallback.
    "conservative_v1": [
        (0, 9, 100, 18),
        (82, 0, 100, 18),
        (0, 90, 100, 100),
    ],
}


def parse_regions(regions_str: str) -> list[dict]:
    """Parse region string into list of dicts with optional labels.

    Supports:
        "x1,y1,x2,y2;x1,y1,x2,y2"                  — unlabeled
        "label:x1,y1,x2,y2;label:x1,y1,x2,y2"       — labeled
    """
    regions: list[dict] = []
    for part in regions_str.split(";"):
        part = part.strip()
        if not part:
            continue
        label = None
        coord_str = part
        # Check for label: if first comma comes after a colon, treat pre-colon as label
        colon_idx = part.find(":")
        comma_idx = part.find(",")
        if colon_idx != -1 and (comma_idx == -1 or colon_idx < comma_idx):
            label = part[:colon_idx].strip()
            coord_str = part[colon_idx + 1:].strip()
        coords = [float(v) for v in coord_str.split(",")]
        if len(coords) != 4:
            raise ValueError(f"Region must have 4 coordinates, got: {part}")
        x1, y1, x2, y2 = coords
        if not all(0 <= v <= 100 for v in (x1, y1, x2, y2)):
            raise ValueError(f"Coordinates must be in range 0–100, got: {part}")
        regions.append({"label": label, "coords": normalize_region((x1, y1, x2, y2))})
    return regions


def normalize_region(region: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = region
    x1 = max(0.0, min(100.0, x1))
    y1 = max(0.0, min(100.0, y1))
    x2 = max(0.0, min(100.0, x2))
    y2 = max(0.0, min(100.0, y2))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


def detect_content_bbox(gray_img, threshold: int = 18) -> tuple[int, int, int, int]:
    """Detect non-black content bounding box from a grayscale image."""
    width, height = gray_img.size
    px = gray_img.load()

    xs: list[int] = []
    ys: list[int] = []
    step = max(1, min(width, height) // 400)

    for y in range(0, height, step):
        for x in range(0, width, step):
            if px[x, y] > threshold:
                xs.append(x)
                ys.append(y)

    if not xs:
        return (0, 0, width, height)

    x0 = max(0, min(xs))
    y0 = max(0, min(ys))
    x1 = min(width, max(xs))
    y1 = min(height, max(ys))

    if x1 <= x0 or y1 <= y0:
        return (0, 0, width, height)

    return (x0, y0, x1, y1)


def pct_to_pixels(
    region_pct: tuple[float, float, float, float],
    canvas: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x1_pct, y1_pct, x2_pct, y2_pct = region_pct
    cx0, cy0, cx1, cy1 = canvas
    cwidth = max(1, cx1 - cx0)
    cheight = max(1, cy1 - cy0)

    x1 = int(cx0 + x1_pct / 100 * cwidth)
    y1 = int(cy0 + y1_pct / 100 * cheight)
    x2 = int(cx0 + x2_pct / 100 * cwidth)
    y2 = int(cy0 + y2_pct / 100 * cheight)

    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


def redact_image(
    input_path: Path,
    regions: list[dict],
    output_path: Path,
    anchor: str,
) -> dict:
    from PIL import Image, ImageDraw

    img = Image.open(input_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    if anchor == "content":
        bbox = detect_content_bbox(img.convert("L"))
    else:
        bbox = (0, 0, width, height)

    region_details: list[dict] = []
    for r in regions:
        coords = r["coords"]
        pr = pct_to_pixels(coords, bbox)
        draw.rectangle([pr[0], pr[1], pr[2], pr[3]], fill="black")
        region_details.append({
            "label": r["label"],
            "pct": list(coords),
            "px": list(pr),
        })

    img.save(output_path)
    return {
        "image_size": [width, height],
        "content_bbox": list(bbox),
        "regions_applied": len(regions),
        "regions": region_details,
    }


def main():
    parser = argparse.ArgumentParser(description="Redact PII regions in medical images with black rectangles.")
    parser.add_argument("input", help="Path to input image file")
    parser.add_argument(
        "--regions",
        help='Semicolon-separated list of "x1,y1,x2,y2" percentage regions',
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        help="Use built-in redaction preset to reduce over-masking",
    )
    parser.add_argument(
        "--anchor",
        choices=["content", "image"],
        default="content",
        help="Anchor percentages to detected content bbox (default) or full image",
    )
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

    regions: list[dict] = []
    if args.preset:
        for coords in PRESETS[args.preset]:
            regions.append({"label": None, "coords": normalize_region(coords)})

    if args.regions:
        try:
            regions.extend(parse_regions(args.regions))
        except ValueError as e:
            print(json.dumps({"success": False, "error": str(e)}))
            sys.exit(1)

    if not regions:
        print(json.dumps({
            "success": False,
            "error": "No regions provided. Use --preset and/or --regions.",
        }))
        sys.exit(1)

    try:
        result = redact_image(input_path, regions, output_path, args.anchor)
        print(json.dumps({
            "success": True,
            "output": str(output_path),
            **result,
        }))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
