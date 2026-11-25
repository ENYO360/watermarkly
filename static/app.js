/* Page wiring: reads the controls and redraws the preview on every change. */
(() => {
  const $ = (id) => document.getElementById(id);
  const MAX_PREVIEW_WIDTH = 1000;      // preview is drawn smaller so sliders stay smooth
  const MAX_EXPORT_PIXELS = 16000000;  // phones can't make bigger canvases than this

  const state = { photo: null, name: "photo", logo: null, frame: 0 };
  let textCache = { key: "", mark: null };
  let photoUrl = null;
  let logoUrl = null;
  const preview = $("preview");

  function say(message, isError = false) {
    $("status").textContent = message;
    $("status").classList.toggle("error", isError);
  }

  function loadImage(file, onLoad) {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => onLoad(img, url);
    img.onerror = () => {
      URL.revokeObjectURL(url);
      say("That file isn’t a supported image. Choose a PNG, JPG or WebP.", true);
    };
    img.src = url;
  }

  /* ---------- reading the controls ---------- */
  function currentOptions() {
    return {
      position: $("position").value,
      scale: $("size").value / 100,
      opacity: $("opacity").value / 100,
      angle: Number($("angle").value),
    };
  }

  function currentMark() {
    if (state.logo) return state.logo;
    const text = $("text").value.trim();
    if (!text) return null;
    const color = $("color").value;
    const key = text + "|" + color;
    if (textCache.key !== key) textCache = { key, mark: textMark(text, color) };
    return textCache.mark;
  }

  function updateLabels() {
    $("sizeOut").textContent = $("size").value + "%";
    $("opacityOut").textContent = $("opacity").value + "%";
    $("angleOut").textContent = $("angle").value + "°";
  }

  /* ---------- drawing ---------- */
  function draw() {
    if (!state.photo) return;
    const nw = state.photo.naturalWidth;
    const nh = state.photo.naturalHeight;
    const w = Math.min(nw, MAX_PREVIEW_WIDTH);
    const h = Math.round((nh * w) / nw);
    if (preview.width !== w || preview.height !== h) {
      preview.width = w;
      preview.height = h;
    }
    const mark = currentMark();
    renderPhoto(preview, state.photo, mark, currentOptions());
    $("hint").textContent = mark ? "" : "Enter watermark text or choose a logo to see it on your photo.";
  }

  function scheduleDraw() { // at most one redraw per screen refresh, however fast the slider moves
    if (state.frame) return;
    state.frame = requestAnimationFrame(() => {
      state.frame = 0;
      draw();
    });
  }

  /* ---------- photo and logo ---------- */
  function setPhoto(file) {
    if (!file) return;
    loadImage(file, (img, url) => {
      if (photoUrl) URL.revokeObjectURL(photoUrl);
      photoUrl = url;
      state.photo = img;
      state.name = file.name.replace(/\.[^.]+$/, "") || "photo";
      $("format").value = file.type === "image/jpeg" ? "image/jpeg" : "image/png";
      $("drop").hidden = true;
      preview.hidden = false;
      $("download").disabled = false;
      say("");
      draw();
    });
  }

  function setLogo(file) {
    if (!file) return;
    loadImage(file, (img, url) => {
      if (logoUrl) URL.revokeObjectURL(logoUrl);
      logoUrl = url;
      state.logo = img;
      $("logoName").textContent = file.name;
      $("removeLogo").hidden = false;
      $("text").disabled = $("color").disabled = true; // the logo replaces the text
      scheduleDraw();
    });
  }

  $("removeLogo").addEventListener("click", () => {
    state.logo = null;
    if (logoUrl) URL.revokeObjectURL(logoUrl);
    logoUrl = null;
    $("logoName").textContent = "No logo chosen";
    $("removeLogo").hidden = true;
    $("text").disabled = $("color").disabled = false;
    scheduleDraw();
  });

  $("photo").addEventListener("change", (e) => { setPhoto(e.target.files[0]); e.target.value = ""; });
  $("logo").addEventListener("change", (e) => { setLogo(e.target.files[0]); e.target.value = ""; });

  const stage = $("stage");
  stage.addEventListener("dragover", (e) => { e.preventDefault(); stage.classList.add("over"); });
  stage.addEventListener("dragleave", () => stage.classList.remove("over"));
  stage.addEventListener("drop", (e) => {
    e.preventDefault();
    stage.classList.remove("over");
    setPhoto(e.dataTransfer.files[0]);
  });

  /* every control redraws the preview as you type or drag */
  $("controls").addEventListener("input", () => { updateLabels(); scheduleDraw(); });

  /* ---------- download (full-size photo, same drawing code) ---------- */
  $("download").addEventListener("click", () => {
    if (!state.photo) return;
    const nw = state.photo.naturalWidth;
    const nh = state.photo.naturalHeight;
    const shrink = Math.min(1, Math.sqrt(MAX_EXPORT_PIXELS / (nw * nh)));
    const canvas = newCanvas(nw * shrink, nh * shrink);
    const type = $("format").value;
    renderPhoto(canvas, state.photo, currentMark(), currentOptions(), type === "image/jpeg" ? "#ffffff" : null);

    canvas.toBlob((blob) => {
      if (!blob) return say("Couldn’t create the image. Try a smaller photo.", true);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = state.name + "-watermarked." + (type === "image/jpeg" ? "jpg" : "png");
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
      say("Saved. Check your downloads folder.");
    }, type, 0.95);
  });

  updateLabels();
})();