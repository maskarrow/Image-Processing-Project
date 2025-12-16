import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk  # pip install pillow
from pathlib import Path
from filters import apply_filter

class ImageFilterUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Filters - UI Skeleton")
        self.geometry("1100x650")
        self.minsize(900, 550)

        self.images = []          # list[Path]
        self.current_index = None # int | None
        self._preview_photo = None
        self._original_pil_image = None
        self._current_pil_image = None
        self._build_layout()

    def _build_layout(self):
        # ----- top toolbar -----
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(side="top", fill="x")

        ttk.Button(toolbar, text="Add Images", command=self.on_add_images).pack(side="left")
        ttk.Button(toolbar, text="Remove Selected", command=self.on_remove_selected).pack(side="left", padx=8)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Clear All", command=self.on_clear_all).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Export", command=self.on_export).pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        # ----- main area (left list, center preview, right filters) -----
        main = ttk.Frame(self, padding=10)
        main.pack(side="top", fill="both", expand=True)

        main.columnconfigure(0, weight=0)  # list
        main.columnconfigure(1, weight=1)  # preview
        main.columnconfigure(2, weight=0)  # filters
        main.rowconfigure(0, weight=1)

        # left: image list
        left = ttk.LabelFrame(main, text="Images", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.listbox = tk.Listbox(left, width=35, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        # center: preview
        center = ttk.LabelFrame(main, text="Preview", padding=8)
        center.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)

        self.preview_label = ttk.Label(center, text="Add images to start.", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        info_bar = ttk.Frame(center)
        info_bar.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        info_bar.columnconfigure(0, weight=1)

        self.info_var = tk.StringVar(value="No image selected.")
        ttk.Label(info_bar, textvariable=self.info_var).grid(row=0, column=0, sticky="w")

        nav = ttk.Frame(info_bar)
        nav.grid(row=0, column=1, sticky="e")
        ttk.Button(nav, text="◀ Prev", command=self.on_prev).pack(side="left")
        ttk.Button(nav, text="Next ▶", command=self.on_next).pack(side="left", padx=(6, 0))

        # right: filters panel
        right = ttk.LabelFrame(main, text="Filters", padding=8)
        right.grid(row=0, column=2, sticky="nsew")

        # optional: categories
        ttk.Label(right, text="Basic").pack(anchor="w", pady=(0, 4))
        btn_grid = ttk.Frame(right)
        btn_grid.pack(fill="x")

        # You can rename/add any filters you want
        filters = [
            "Grayscale", "Blur", "Sharpen", "Edge Detect",
            "Emboss", "Sepia", "Invert", "Threshold",
            "Brightness +", "Brightness -", "Contrast +", "Contrast -",
            "Reset"
        ]

        for i, name in enumerate(filters):
            b = ttk.Button(btn_grid, text=name, command=lambda n=name: self.on_filter_clicked(n))
            b.grid(row=i, column=0, sticky="ew", pady=3)
        btn_grid.columnconfigure(0, weight=1)

        # Strength control for filters (0.0 .. 1.0) — prettier UI using ttk.Scale
        self.strength = tk.DoubleVar(value=0.5)
        ttk.Label(right, text="Strength").pack(anchor="w", pady=(8, 2))

        strength_frame = ttk.Frame(right)
        strength_frame.pack(fill="x")

        # Use ttk.Scale for a modern look; range 0.0..1.0 and update `self.strength`
        self._strength_scale = ttk.Scale(
            strength_frame, from_=0.0, to=1.0, orient="horizontal",
            command=self._on_strength_change, length=200
        )
        self._strength_scale.set(self.strength.get())
        self._strength_scale.pack(side="left", fill="x", expand=True)

        # Percent label to the right of the slider
        self._strength_value_label = ttk.Label(strength_frame, text=f"{int(self.strength.get()*100)}%")
        self._strength_value_label.pack(side="left", padx=(8, 0))

        ttk.Separator(right).pack(fill="x", pady=10)

    def on_add_images(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            initialdir=r"C:\Users\Asus\Desktop\imagini_IOM",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")]
        )
        if not paths:
            return

        added = 0
        for p in paths:
            path = Path(p)
            if path not in self.images:
                self.images.append(path)
                self.listbox.insert("end", path.name)
                added += 1

        self.status_var.set(f"Added {added} image(s). Total: {len(self.images)}")
        if self.current_index is None and self.images:
            self._select_index(0)

    def on_remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.images.pop(idx)
        self.listbox.delete(idx)

        if not self.images:
            self.current_index = None
            self.preview_label.config(text="Add images to start.", image="")
            self.info_var.set("No image selected.")
            return

        new_idx = min(idx, len(self.images) - 1)
        self._select_index(new_idx)

    def on_clear_all(self):
        self.images.clear()
        self.listbox.delete(0, "end")
        self.current_index = None
        self.preview_label.config(text="Add images to start.", image="")
        self.info_var.set("No image selected.")
        self.status_var.set("Cleared all images.")

    def on_export(self):
        # Export the currently selected image (with applied filters) to a file.
        if not self.images:
            messagebox.showwarning("Export", "No images to export.")
            return

        if self.current_index is None:
            messagebox.showwarning("Export", "Select an image first.")
            return

        # Suggest a default filename based on the original name
        src_path = self.images[self.current_index]
        default_name = f"{src_path.stem}_filtered"

        target = filedialog.asksaveasfilename(
            title="Export image",
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg"), ("BMP", "*.bmp"), ("All files", "*.*")]
        )
        if not target:
            return

        try:
            img = self._current_pil_image or self._original_pil_image
            if img is None:
                raise RuntimeError("No image data available to export.")

            # Save using PIL; format inferred from file extension
            img.save(target)
            self.status_var.set(f"Exported: {Path(target).name}")
            messagebox.showinfo("Export", f"Saved to: {target}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def on_select_image(self, _evt=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._select_index(sel[0])

    def _select_index(self, idx: int):
        if idx < 0 or idx >= len(self.images):
            return
        self.current_index = idx
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
        self._show_preview(self.images[idx])

    def on_prev(self):
        if self.current_index is None or not self.images:
            return
        self._select_index((self.current_index - 1) % len(self.images))

    def on_next(self):
        if self.current_index is None or not self.images:
            return
        self._select_index((self.current_index + 1) % len(self.images))

    def _on_strength_change(self, value):
        # Called with the scale value (string), update DoubleVar and percent label
        try:
            v = float(value)
        except Exception:
            return
        # keep internal 0.0..1.0 value
        self.strength.set(v)
        if hasattr(self, '_strength_value_label'):
            self._strength_value_label.config(text=f"{int(round(v*100))}%")

    def on_filter_clicked(self, name: str):
        if self.current_index is None or self._current_pil_image is None:
            messagebox.showwarning("No image", "Select an image first.")
            return

        # Reset should restore original
        if name == "Reset":
            self._current_pil_image = self._original_pil_image.copy()
            out = self._current_pil_image.copy()
            out.thumbnail((650, 480))
            self._preview_photo = ImageTk.PhotoImage(out)
            self.preview_label.config(image=self._preview_photo, text="")
            self.status_var.set("Reset to original.")
            return

        result = apply_filter(self._current_pil_image, name, self.strength.get())
        self._current_pil_image = result.image

        # Show preview (resized copy)
        out = self._current_pil_image.copy()
        out.thumbnail((650, 480))
        self._preview_photo = ImageTk.PhotoImage(out)
        self.preview_label.config(image=self._preview_photo, text="")
        self.status_var.set(result.info)

    # preview utility (just display, no filtering yet)

    def _show_preview(self, path: Path):
        try:
            # Load as PIL (keep full-res internally)
            img = Image.open(path).convert("RGB")
            self._original_pil_image = img
            self._current_pil_image = img.copy()

            # Create a resized copy only for display
            preview = self._current_pil_image.copy()
            preview.thumbnail((650, 480))

            self._preview_photo = ImageTk.PhotoImage(preview)
            self.preview_label.config(image=self._preview_photo, text="")
            self.info_var.set(f"{path.name}  |  {img.size[0]}x{img.size[1]}")
            self.status_var.set(f"Selected: {path.name}")
        except Exception as e:
            messagebox.showerror("Preview error", str(e))


if __name__ == "__main__":
    # pip install pillow
    ImageFilterUI().mainloop()
