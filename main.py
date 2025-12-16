import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from filters import apply_filter
import cv2

# Shared filter names used by the UI and the webcam
FILTERS = [
    "Grayscale", "Blur", "Sharpen", "Edge Detect",
    "Emboss", "Sepia", "Invert", "Threshold",
    "Brightness +", "Brightness -", "Contrast +", "Contrast -",
    "Reset"
]

class ImageFilterUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Filters - UI Skeleton")
        self.geometry("1100x650")
        self.minsize(900, 550)

        self.images = []
        self.current_index = None
        self._preview_photo = None
        self._original_pil_image = None
        self._current_pil_image = None
        self._build_layout()

    def _build_layout(self):
        
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(side="top", fill="x")

        ttk.Button(toolbar, text="Add Images", command=self.on_add_images).pack(side="left")
        ttk.Button(toolbar, text="Remove Selected", command=self.on_remove_selected).pack(side="left", padx=8)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Clear All", command=self.on_clear_all).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Export", command=self.on_export).pack(side="left")
        ttk.Button(toolbar, text="Webcam", command=self.on_webcam).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="right")

        
        main = ttk.Frame(self, padding=10)
        main.pack(side="top", fill="both", expand=True)

        main.columnconfigure(0, weight=0)  # list
        main.columnconfigure(1, weight=1)  # preview
        main.columnconfigure(2, weight=0)  # filters
        main.rowconfigure(0, weight=1)

        
        left = ttk.LabelFrame(main, text="Images", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.listbox = tk.Listbox(left, width=35, activestyle="dotbox")
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_select_image)

        
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

        
        right = ttk.LabelFrame(main, text="Filters", padding=8)
        right.grid(row=0, column=2, sticky="nsew")

        
        ttk.Label(right, text="Basic").pack(anchor="w", pady=(0, 4))
        btn_grid = ttk.Frame(right)
        btn_grid.pack(fill="x")

        # You can rename/add any filters you want
        for i, name in enumerate(FILTERS):
            b = ttk.Button(btn_grid, text=name, command=lambda n=name: self.on_filter_clicked(n))
            b.grid(row=i, column=0, sticky="ew", pady=3)
        btn_grid.columnconfigure(0, weight=1)

        self.strength = tk.DoubleVar(value=0.5)
        ttk.Label(right, text="Strength").pack(anchor="w", pady=(8, 2))

        strength_frame = ttk.Frame(right)
        strength_frame.pack(fill="x")

        self._strength_scale = ttk.Scale(
            strength_frame, from_=0.0, to=1.0, orient="horizontal",
            command=self._on_strength_change, length=200
        )
        self._strength_scale.set(self.strength.get())
        self._strength_scale.pack(side="left", fill="x", expand=True)

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

    def on_webcam(self):
        if hasattr(self, '_webcam_win') and self._webcam_win.winfo_exists():
            self._webcam_win.lift()
            return
        self._webcam_win = WebcamWindow(self, FILTERS, self.strength)

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
        try:
            v = float(value)
        except Exception:
            return
        self.strength.set(v)
        if hasattr(self, '_strength_value_label'):
            self._strength_value_label.config(text=f"{int(round(v*100))}%")

    def on_filter_clicked(self, name: str):
        if self.current_index is None or self._current_pil_image is None:
            messagebox.showwarning("No image", "Select an image first.")
            return

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

        out = self._current_pil_image.copy()
        out.thumbnail((650, 480))
        self._preview_photo = ImageTk.PhotoImage(out)
        self.preview_label.config(image=self._preview_photo, text="")
        self.status_var.set(result.info)

    # preview utility (just display, no filtering yet)

    def _show_preview(self, path: Path):
        try:
            img = Image.open(path).convert("RGB")
            self._original_pil_image = img
            self._current_pil_image = img.copy()

            preview = self._current_pil_image.copy()
            preview.thumbnail((650, 480))

            self._preview_photo = ImageTk.PhotoImage(preview)
            self.preview_label.config(image=self._preview_photo, text="")
            self.info_var.set(f"{path.name}  |  {img.size[0]}x{img.size[1]}")
            self.status_var.set(f"Selected: {path.name}")
        except Exception as e:
            messagebox.showerror("Preview error", str(e))


class WebcamWindow(tk.Toplevel):
    def __init__(self, parent: ImageFilterUI, filter_names, shared_strength_var: tk.DoubleVar | None = None):
        super().__init__(parent)
        self.title("Webcam")
        self.geometry("720x560")
        self.resizable(False, False)

        self.parent = parent
        self.filter_names = list(filter_names)
        self.shared_strength_var = shared_strength_var

        self._running = False
        self._cap = None
        self._last_frame_pil = None

        top = ttk.Frame(self, padding=8)
        top.pack(fill="both", expand=True)

        self.video_label = ttk.Label(top, text="Webcam not started", anchor="center")
        self.video_label.pack(fill="both", expand=True)

        ctrl = ttk.Frame(top)
        ctrl.pack(fill="x", pady=(6, 0))

        ttk.Label(ctrl, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value=self.filter_names[0])
        self.filter_combo = ttk.Combobox(ctrl, values=self.filter_names, textvariable=self.filter_var, state="readonly", width=18)
        self.filter_combo.pack(side="left", padx=(6, 12))

        ttk.Label(ctrl, text="Strength:").pack(side="left")
        self.local_strength = tk.DoubleVar(value=shared_strength_var.get() if shared_strength_var else 0.5)
        self.str_scale = ttk.Scale(ctrl, from_=0.0, to=1.0, orient="horizontal", command=self._on_strength_change, length=140)
        self.str_scale.set(self.local_strength.get())
        self.str_scale.pack(side="left", padx=(6, 8))

        self._str_label = ttk.Label(ctrl, text=f"{int(self.local_strength.get()*100)}%")
        self._str_label.pack(side="left")

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill="x", pady=(8, 0))

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.toggle)
        self.start_btn.pack(side="left")

        ttk.Button(btn_frame, text="Snapshot", command=self.snapshot).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self.close)

    def _on_strength_change(self, value):
        try:
            v = float(value)
        except Exception:
            return
        self.local_strength.set(v)
        self._str_label.config(text=f"{int(round(v*100))}%")
        if self.shared_strength_var is not None:
            self.shared_strength_var.set(v)

    def toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            import cv2
        except Exception as e:
            messagebox.showerror("Webcam error", f"OpenCV not available: {e}\nInstall with: pip install opencv-python")
            return

        try:
            self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        except Exception:
            self._cap = cv2.VideoCapture(0)

        if not self._cap or not self._cap.isOpened():
            messagebox.showerror("Webcam error", "Unable to open the webcam.")
            return

        self._running = True
        self.start_btn.config(text="Stop")
        self._update_frame()

    def _stop(self):
        self._running = False
        self.start_btn.config(text="Start")
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def _update_frame(self):
        if not self._running or not self._cap:
            return
        try:
            ret, frame = self._cap.read()
            if not ret:
                self.after(30, self._update_frame)
                return

            import cv2
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            from PIL import Image
            img = Image.fromarray(frame)

            w, h = img.size
            max_w, max_h = 640, 480
            if w > max_w or h > max_h:
                img = img.copy()
                img.thumbnail((max_w, max_h))

            fname = self.filter_var.get()
            strength = self.local_strength.get()
            if fname and fname != "Reset":
                try:
                    res = apply_filter(img.convert("RGB"), fname, strength)
                    img = res.image
                except Exception:
                    pass

            self._last_frame_pil = img
            imgtk = ImageTk.PhotoImage(img)
            self.video_label.config(image=imgtk, text="")
            self.video_label.image = imgtk
        finally:
            self.after(30, self._update_frame)

    def snapshot(self):
        if self._last_frame_pil is None:
            messagebox.showwarning("Snapshot", "No frame available.")
            return
        target = filedialog.asksaveasfilename(title="Save snapshot", defaultextension=".png", filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg"),("All files","*.*")])
        if not target:
            return
        try:
            self._last_frame_pil.save(target)
            messagebox.showinfo("Snapshot", f"Saved: {target}")
        except Exception as e:
            messagebox.showerror("Snapshot error", str(e))

    def close(self):
        self._stop()
        try:
            self.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    # pip install pillow
    ImageFilterUI().mainloop()
