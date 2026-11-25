import os

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

POSITIONS = ("bottom-right", "bottom-left", "top-right", "top-left", "center", "tile")

FONT_CANDIDATES = (
    "arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def load_font(size):
    """Try a few common fonts, then fall back to Pillow's built-in one."""
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow 10.1+
    except TypeError:
        return ImageFont.load_default()


def text_mark(text, color):
    """Draw text onto a transparent image, sized tightly around the text."""
    font = load_font(160)  # drawn big, then scaled down so it stays sharp
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    left, top, right, bottom = probe.textbbox((0, 0), text, font=font)
    pad = 10
    mark = Image.new("RGBA", (right - left + 2 * pad, bottom - top + 2 * pad), (0, 0, 0, 0))
    fill = ImageColor.getrgb(color)[:3] + (255,)
    ImageDraw.Draw(mark).text((pad - left, pad - top), text, font=font, fill=fill)
    return mark


def fit_width(mark, target_width):
    """Resize a mark to a given width, keeping its proportions."""
    target_width = max(1, int(target_width))
    height = max(1, int(mark.height * target_width / mark.width))
    return mark.resize((target_width, height), Image.Resampling.LANCZOS)


def set_opacity(mark, opacity):
    """opacity: 0.0 (invisible) to 1.0 (solid). Keeps transparent areas transparent."""
    mark = mark.copy()
    mark.putalpha(mark.getchannel("A").point(lambda a: int(a * opacity)))
    return mark


def place(base, mark, position):
    """Paste the mark onto a transparent layer, then merge it with the photo."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    width, height = base.size
    w, h = mark.size
    margin = int(width * 0.03)

    if position == "tile":  # repeated in staggered rows, hard to crop out
        step_x, step_y = int(w * 1.8) + 1, int(h * 3) + 1
        for row, y in enumerate(range(0, height, step_y)):
            shift = step_x // 2 if row % 2 else 0
            for x in range(-shift, width, step_x):
                layer.paste(mark, (x, y), mark)
    else:
        x = {"left": margin, "right": width - w - margin}.get(position.split("-")[-1], (width - w) // 2)
        y = {"top": margin, "bottom": height - h - margin}.get(position.split("-")[0], (height - h) // 2)
        layer.paste(mark, (x, y), mark)

    return Image.alpha_composite(base, layer)


def add_watermark(image, text="", logo=None, position="bottom-right",
                  scale=0.3, opacity=0.6, color="#ffffff", angle=0):
    """Return a new image with a text or logo watermark.

    scale   - watermark width as a fraction of the photo width (0.05 - 0.8)
    opacity - 0.0 - 1.0
    angle   - rotation in degrees
    """
    base = ImageOps.exif_transpose(image).convert("RGBA")  # fixes sideways phone photos

    if logo is not None:
        mark = logo.convert("RGBA")
    elif text and text.strip():
        mark = text_mark(text.strip(), color)
    else:
        return base  # nothing to add yet

    mark = fit_width(mark, base.width * scale)
    if angle:
        mark = mark.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    mark = set_opacity(mark, opacity)
    return place(base, mark, position if position in POSITIONS else "bottom-right")


def format_for_path(path):
    return "JPEG" if os.path.splitext(path)[1].lower() in (".jpg", ".jpeg") else "PNG"


def save_image(image, target, fmt="PNG"):
    """Save to a path or file-like object. JPEG has no transparency, so convert first."""
    if fmt.upper() in ("JPEG", "JPG"):
        image.convert("RGB").save(target, "JPEG", quality=95)
    else:
        image.save(target, "PNG")
