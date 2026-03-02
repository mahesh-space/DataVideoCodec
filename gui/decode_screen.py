"""
Decode Screen for the DataVideoCodec GUI.

Provides video file selection, manifest auto-detection,
real-time decoding progress, and recovery status display.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.models import EncodingParams
from core.constants import RESOLUTION_MAP, VALID_BLOCK_SIZES, VALID_ECC_OVERHEADS
from core.config import load_config
from decoder.controller import DecoderController
from core.utils import get_logger

logger = get_logger("DecodeScreen")


class DecodeScreen(ctk.CTkFrame):
    """Decode workflow screen with video picker, auto-manifest, and progress."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.decoding = False

        self.grid_columnconfigure(0, weight=1)

        # --- Header ---
        header = ctk.CTkLabel(
            self, text="📥 Decode Video to File",
            font=ctk.CTkFont(size=28, weight="bold"), anchor="w",
        )
        header.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self, text="Select an encoded video to recover the original file",
            font=ctk.CTkFont(size=13), text_color="gray", anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="w")

        # --- Video File Selection ---
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=2, column=0, padx=25, pady=8, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame, text="Video File:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.video_path_var = ctk.StringVar(value="No video selected")
        ctk.CTkLabel(
            file_frame, textvariable=self.video_path_var,
            font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        ctk.CTkButton(
            file_frame, text="Browse...", width=100, command=self._browse_video,
        ).grid(row=0, column=2, padx=15, pady=12)

        # --- Manifest ---
        manifest_frame = ctk.CTkFrame(self)
        manifest_frame.grid(row=3, column=0, padx=25, pady=8, sticky="ew")
        manifest_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            manifest_frame, text="Manifest:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.manifest_var = ctk.StringVar(value="Auto-detect")
        ctk.CTkLabel(
            manifest_frame, textvariable=self.manifest_var,
            font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        ctk.CTkButton(
            manifest_frame, text="Browse...", width=100, command=self._browse_manifest,
        ).grid(row=0, column=2, padx=15, pady=12)

        # --- Manual Parameters (if no manifest) ---
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=4, column=0, padx=25, pady=8, sticky="ew")
        params_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            params_frame, text="Manual Parameters (if no manifest):",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 8), sticky="w")

        ctk.CTkLabel(params_frame, text="Resolution:").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        self.resolution_var = ctk.StringVar(value="720p")
        ctk.CTkOptionMenu(
            params_frame, values=list(RESOLUTION_MAP.keys()),
            variable=self.resolution_var, width=140,
        ).grid(row=2, column=0, padx=15, pady=(0, 12))

        ctk.CTkLabel(params_frame, text="Block Size:").grid(row=1, column=1, padx=15, pady=5, sticky="w")
        self.block_size_var = ctk.StringVar(value="4")
        ctk.CTkSegmentedButton(
            params_frame, values=["2", "4", "8"],
            variable=self.block_size_var, width=140,
        ).grid(row=2, column=1, padx=15, pady=(0, 12))

        ctk.CTkLabel(params_frame, text="ECC Overhead:").grid(row=1, column=2, padx=15, pady=5, sticky="w")
        self.ecc_var = ctk.StringVar(value="20%")
        ctk.CTkOptionMenu(
            params_frame, values=["10%", "20%", "40%"],
            variable=self.ecc_var, width=140,
        ).grid(row=2, column=2, padx=15, pady=(0, 12))

        # --- Output ---
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=5, column=0, padx=25, pady=8, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            output_frame, text="Output Dir:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        config = load_config()
        default_output = config.get("output_dir", "") or str(Path.home() / "DataVideoCodec_recovered")
        self.output_var = ctk.StringVar(value=default_output)
        ctk.CTkEntry(output_frame, textvariable=self.output_var).grid(
            row=0, column=1, padx=10, pady=12, sticky="ew",
        )
        ctk.CTkButton(
            output_frame, text="Browse...", width=100, command=self._browse_output,
        ).grid(row=0, column=2, padx=15, pady=12)

        # --- Progress ---
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=6, column=0, padx=25, pady=8, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_var = ctk.StringVar(value="Ready to decode")
        self.status_label = ctk.CTkLabel(
            progress_frame, textvariable=self.status_var,
            font=ctk.CTkFont(size=12), text_color="gray",
        )
        self.status_label.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

        # Recovery result
        self.result_var = ctk.StringVar(value="")
        self.result_label = ctk.CTkLabel(
            progress_frame, textvariable=self.result_var,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.result_label.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="w")

        # --- Decode Button ---
        self.decode_btn = ctk.CTkButton(
            self, text="▶ Start Decoding", font=ctk.CTkFont(size=16, weight="bold"),
            height=50, corner_radius=10, command=self._start_decode,
        )
        self.decode_btn.grid(row=7, column=0, padx=25, pady=15, sticky="ew")

    def _browse_video(self):
        path = filedialog.askopenfilename(
            title="Select Encoded Video",
            filetypes=[("Video files", "*.mp4 *.avi *.mkv"), ("All files", "*.*")],
        )
        if path:
            self.video_path_var.set(path)
            # Auto-detect manifest
            manifest = Path(path).with_suffix(".json")
            if manifest.exists():
                self.manifest_var.set(str(manifest))
            else:
                self.manifest_var.set("Not found — using manual parameters")

    def _browse_manifest(self):
        path = filedialog.askopenfilename(
            title="Select Manifest JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.manifest_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_var.set(path)

    def _start_decode(self):
        if self.decoding:
            return

        video_path = self.video_path_var.get()
        if video_path == "No video selected" or not Path(video_path).exists():
            self.status_var.set("❌ Please select a valid video file")
            return

        self.decoding = True
        self.decode_btn.configure(state="disabled", text="Decoding...")
        self.result_var.set("")

        # Determine manifest
        manifest_path = self.manifest_var.get()
        if manifest_path in ("Auto-detect", "Not found — using manual parameters"):
            manifest_path = None

        # Build manual params
        params = None
        if manifest_path is None:
            ecc_text = self.ecc_var.get().replace("%", "")
            params = EncodingParams(
                resolution=RESOLUTION_MAP[self.resolution_var.get()],
                block_size=int(self.block_size_var.get()),
                ecc_overhead=float(ecc_text) / 100,
            )

        thread = threading.Thread(
            target=self._decode_worker,
            args=(video_path, self.output_var.get(), params, manifest_path),
            daemon=True,
        )
        thread.start()

    def _decode_worker(self, video_path, output_dir, params, manifest_path):
        try:
            config = load_config()
            controller = DecoderController(
                ffmpeg_path=config.get("ffmpeg_path", "ffmpeg")
            )

            def on_progress(pct, msg):
                self.after(0, lambda: self._update_progress(pct, msg))

            result = controller.run_decode(
                video_path=video_path,
                output_dir=output_dir,
                params=params,
                manifest_path=manifest_path,
                progress_cb=on_progress,
            )

            self.after(0, lambda: self._decode_complete(result))

        except Exception as e:
            self.after(0, lambda: self._decode_error(str(e)))

    def _update_progress(self, pct, msg):
        self.progress_bar.set(pct / 100)
        self.status_var.set(msg)

    def _decode_complete(self, result):
        self.decoding = False
        self.decode_btn.configure(state="normal", text="▶ Start Decoding")
        self.progress_bar.set(1.0)

        status_display = {
            "FULL_RECOVERY": ("✅ FULL RECOVERY — File recovered perfectly!", "green"),
            "PARTIAL_RECOVERY": ("⚠️ PARTIAL RECOVERY — Some errors remain", "orange"),
            "RECOVERY_FAILURE": ("❌ RECOVERY FAILURE — Could not recover file", "red"),
        }
        text, color = status_display.get(result.status, ("❓ Unknown", "gray"))
        self.result_var.set(text)
        self.result_label.configure(text_color=color)

        details = f"Errors corrected: {result.errors_corrected}"
        if result.output_path:
            details += f" | Output: {Path(result.output_path).name}"
        self.status_var.set(details)

    def _decode_error(self, error_msg):
        self.decoding = False
        self.decode_btn.configure(state="normal", text="▶ Start Decoding")
        self.progress_bar.set(0)
        self.status_var.set(f"❌ Error: {error_msg}")
        self.result_var.set("")
