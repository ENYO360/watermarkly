/* Drawing code for the watermark. It only touches canvases (no page elements),
   so the live preview and the final download use exactly the same logic.
   Positions, margins, tiling and rotation match watermark.py (the desktop app). */

function newCanvas(width, height) {
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(width));
  canvas.height = Math.max(1, Math.round(height));
  return canvas;
}

/* Draw text onto a transparent canvas, sized tightly around the text. */
function textMark(text, color) {
  const font = 'bold 160px system-ui, "Segoe UI", Arial, sans-serif'; // big, then scaled down
  const probe = newCanvas(1, 1).getContext("2d");
  probe.font = font;
  const m = probe.measureText(text);
  const width = m.actualBoundingBoxLeft + m.actualBoundingBoxRight;
  const height = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
  const pad = 10;

  const canvas = newCanvas(width + 2 * pad, height + 2 * pad);
  const ctx = canvas.getContext("2d");
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textBaseline = "alphabetic";
  ctx.fillText(text, pad + m.actualBoundingBoxLeft, pad + m.actualBoundingBoxAscent);
  return canvas;
}

/* Scale the mark to the wanted width and rotate it (positive angle = counter-clockwise). */
function rotatedMark(source, targetWidth, angleDeg) {
  const sw = source.naturalWidth || source.width;
  const sh = source.naturalHeight || source.height;
  const w = Math.max(1, targetWidth);
  const h = Math.max(1, (sh * w) / sw);
  const rad = (angleDeg * Math.PI) / 180;
  const cos = Math.abs(Math.cos(rad));
  const sin = Math.abs(Math.sin(rad));

  const canvas = newCanvas(w * cos + h * sin, w * sin + h * cos);
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingQuality = "high";
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(-rad);
  ctx.drawImage(source, -w / 2, -h / 2, w, h);
  return canvas;
}

/* options: { position, scale (0-1 of photo width), opacity (0-1), angle (degrees) } */
function drawWatermark(ctx, width, height, mark, options) {
  const piece = rotatedMark(mark, width * options.scale, options.angle);
  const w = piece.width;
  const h = piece.height;
  const margin = Math.floor(width * 0.03);

  ctx.save();
  ctx.globalAlpha = options.opacity;

  if (options.position === "tile") {
    const stepX = Math.floor(w * 1.8) + 1;
    const stepY = Math.floor(h * 3) + 1;
    for (let row = 0, y = 0; y < height; row++, y += stepY) {
      const shift = row % 2 ? Math.floor(stepX / 2) : 0; // stagger every other row
      for (let x = -shift; x < width; x += stepX) ctx.drawImage(piece, x, y);
    }
  } else {
    const [vertical, horizontal] = options.position.includes("-")
      ? options.position.split("-")
      : ["center", "center"];
    const x = horizontal === "left" ? margin : horizontal === "right" ? width - w - margin : (width - w) / 2;
    const y = vertical === "top" ? margin : vertical === "bottom" ? height - h - margin : (height - h) / 2;
    ctx.drawImage(piece, Math.round(x), Math.round(y));
  }
  ctx.restore();
}

/* Draw the photo, then the watermark on top. `background` fills first (used for JPEG). */
function renderPhoto(canvas, photo, mark, options, background) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (background) {
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  ctx.drawImage(photo, 0, 0, canvas.width, canvas.height);
  if (mark) drawWatermark(ctx, canvas.width, canvas.height, mark, options);
}

if (typeof module !== "undefined") module.exports = { newCanvas, textMark, renderPhoto };