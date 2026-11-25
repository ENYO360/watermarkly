"""Day 85 - Image Watermarker (desktop app built with Tkinter + Pillow)."""

import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

import watermark

PREVIEW_MAX = (640, 520)  # the preview uses a smaller copy so sliders feel instant


class WatermarkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Watermarker")
        self.minsize(940, 640)

        self.original = None      # full-size photo (used when saving)
        self.preview_base = None  # small copy (used for the live preview)
        self.logo = None
        self.color = "#ffffff"
        self.photo = None         # keep a reference or Tk will discard the image
        self._job = None

        self.text_var = tk.StringVar(value="© yourwebsite.com")
        self.position_var = tk.StringVar(value="bottom-right")
        self.size_var = tk.IntVar(value=30)
        self.opacity_var = tk.IntVar(value=60)
        self.angle_var = tk.IntVar(value=0)
        for var in (self.text_var, self.position_var, self.size_var, self.opacity_var, self.angle_var):
            var.trace_add("write", self.schedule_preview)  # redraw whenever a setting changes

        self.build_ui()

    # ---------- layout ----------
    def build_ui(self):
        controls = ttk.Frame(self, padding=14)
        controls.grid(row=0, column=0, sticky="ns")
        stage = ttk.Frame(self, padding=14)
        stage.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        ttk.Button(controls, text="1. Open image…", command=self.open_image).pack(fill="x")

        ttk.Label(controls, text="2. Watermark text").pack(anchor="w", pady=(16, 2))
        ttk.Entry(controls, textvariable=self.text_var, width=32).pack(fill="x")
        colour_row = ttk.Frame(controls)
        colour_row.pack(fill="x", pady=6)
        ttk.Button(colour_row, text="Text colour…", command=self.pick_color).pack(side="left")
        self.swatch = tk.Label(colour_row, width=4, bg=self.color, relief="sunken")
        self.swatch.pack(side="left", padx=8)

        ttk.Label(controls, text="Or use a logo (replaces the text)").pack(anchor="w", pady=(10, 2))
        logo_row = ttk.Frame(controls)
        logo_row.pack(fill="x")
        ttk.Button(logo_row, text="Choose logo…", command=self.choose_logo).pack(side="left")
        ttk.Button(logo_row, text="Remove", command=self.remove_logo).pack(side="left", padx=6)
        self.logo_label = ttk.Label(controls, text="No logo chosen", foreground="#666")
        self.logo_label.pack(anchor="w")

        ttk.Label(controls, text="3. Position").pack(anchor="w", pady=(16, 2))
        ttk.Combobox(controls, textvariable=self.position_var, values=watermark.POSITIONS,
                     state="readonly").pack(fill="x")

        self.add_slider(controls, "Size (% of photo width)", self.size_var, 5, 80)
        self.add_slider(controls, "Opacity (%)", self.opacity_var, 5, 100)
        self.add_slider(controls, "Rotation (degrees)", self.angle_var, -90, 90)

        self.save_btn = ttk.Button(controls, text="4. Save watermarked image…", command=self.save_image)
        self.save_btn.pack(fill="x", pady=(22, 0))
        self.save_btn.state(["disabled"])

        self.preview_label = ttk.Label(stage, text="Open an image to start", anchor="center")
        self.preview_label.pack(expand=True, fill="both")

    def add_slider(self, parent, label, var, low, high):
        ttk.Label(parent, text=label).pack(anchor="w", pady=(12, 0))
        tk.Scale(parent, from_=low, to=high, orient="horizontal", variable=var).pack(fill="x")

    # ---------- actions ----------
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Choose a photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            image = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
        except Exception:
            messagebox.showerror("Can't open image", "That file isn't a supported image. Try a PNG or JPG.")
            return
        self.original = image
        self.preview_base = image.copy()
        self.preview_base.thumbnail(PREVIEW_MAX)
        self.save_btn.state(["!disabled"])
        self.update_preview()

    def choose_logo(self):
        path = filedialog.askopenfilename(
            title="Choose a logo (PNG with a transparent background works best)",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.logo = Image.open(path).convert("RGBA")
        except Exception:
            messagebox.showerror("Can't open logo", "That file isn't a supported image.")
            return
        self.logo_label.config(text=os.path.basename(path))
        self.schedule_preview()

    def remove_logo(self):
        self.logo = None
        self.logo_label.config(text="No logo chosen")
        self.schedule_preview()

    def pick_color(self):
        chosen = colorchooser.askcolor(color=self.color, title="Text colour")[1]
        if chosen:
            self.color = chosen
            self.swatch.config(bg=chosen)
            self.schedule_preview()

    def render(self, base):
        return watermark.add_watermark(
            base,
            text=self.text_var.get(),
            logo=self.logo,
            position=self.position_var.get(),
            scale=self.size_var.get() / 100,
            opacity=self.opacity_var.get() / 100,
            color=self.color,
            angle=self.angle_var.get(),
        )

    def schedule_preview(self, *_):
        """Wait a moment so dragging a slider doesn't redraw hundreds of times."""
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self.update_preview)

    def update_preview(self):
        self._job = None
        if self.preview_base is None:
            return
        self.photo = ImageTk.PhotoImage(self.render(self.preview_base))
        self.preview_label.configure(image=self.photo, text="")

    def save_image(self):
        path = filedialog.asksaveasfilename(
            title="Save watermarked image",
            defaultextension=".png",
            initialfile="watermarked.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg")],
        )
        if not path:
            return
        try:  # the full-size photo is watermarked here, not the small preview
            watermark.save_image(self.render(self.original), path, watermark.format_for_path(path))
        except Exception as error:
            messagebox.showerror("Couldn't save", str(error))
            return
        messagebox.showinfo("Saved", f"Your image was saved to:\n{path}")


if __name__ == "__main__":
    WatermarkApp().mainloop()
