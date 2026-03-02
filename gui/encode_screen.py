"""
Encode Screen for the DataVideoCodec GUI.

Provides file selection, parameter configuration, real-time progress
tracking, and encoding status messages.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.models import EncodingParams
from core.constants import RESOLUTION_MAP, VALID_BLOCK_SIZES, VALID_ECC_OVERHEADS
from core.config import load_config
from encoder.controller import EncoderController
from core.utils import get_logger

logger = get_logger("EncodeScreen")


class EncodeScreen(ctk.CTkFrame):
    """Encode workflow screen with file picker, parameters, and progress."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.encoding = False

        self.grid_columnconfigure(0, weight=1)

        # --- Header ---
        header = ctk.CTkLabel(
            self, text="📤 Encode File to Video",
            font=ctk.CTkFont(size=28, weight="bold"), anchor="w",
        )
        header.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self, text="Select a file and configure encoding parameters",
            font=ctk.CTkFont(size=13), text_color="gray", anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="w")

        # --- File Selection ---
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=2, column=0, padx=25, pady=8, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            file_frame, text="Input File:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.file_path_var = ctk.StringVar(value="No file selected")
        self.file_label = ctk.CTkLabel(
            file_frame, textvariable=self.file_path_var,
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self.file_label.grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        self.browse_btn = ctk.CTkButton(
            file_frame, text="Browse...", width=100, command=self._browse_file,
        )
        self.browse_btn.grid(row=0, column=2, padx=15, pady=12)

        # --- Parameters ---
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=3, column=0, padx=25, pady=8, sticky="ew")
        params_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            params_frame, text="⚙️ Encoding Parameters",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 8), sticky="w")

        # Resolution
        ctk.CTkLabel(params_frame, text="Resolution:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, padx=15, pady=5, sticky="w",
        )
        self.resolution_var = ctk.StringVar(value="720p")
        self.resolution_menu = ctk.CTkOptionMenu(
            params_frame, values=list(RESOLUTION_MAP.keys()),
            variable=self.resolution_var, width=140,
        )
        self.resolution_menu.grid(row=2, column=0, padx=15, pady=(0, 12))

        # Block size
        ctk.CTkLabel(params_frame, text="Block Size:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=1, padx=15, pady=5, sticky="w",
        )
        self.block_size_var = ctk.StringVar(value="4")
        self.block_size_menu = ctk.CTkSegmentedButton(
            params_frame, values=["2", "4", "8"],
            variable=self.block_size_var, width=140,
        )
        self.block_size_menu.grid(row=2, column=1, padx=15, pady=(0, 12))

        # ECC Overhead
        ctk.CTkLabel(params_frame, text="ECC Overhead:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=2, padx=15, pady=5, sticky="w",
        )
        self.ecc_var = ctk.StringVar(value="20%")
        self.ecc_menu = ctk.CTkOptionMenu(
            params_frame, values=["10%", "20%", "40%"],
            variable=self.ecc_var, width=140,
        )
        self.ecc_menu.grid(row=2, column=2, padx=15, pady=(0, 12))

        # FPS
        ctk.CTkLabel(params_frame, text="FPS:", font=ctk.CTkFont(size=12)).grid(
            row=1, column=3, padx=15, pady=5, sticky="w",
        )
        self.fps_var = ctk.StringVar(value="30")
        self.fps_entry = ctk.CTkEntry(params_frame, textvariable=self.fps_var, width=80)
        self.fps_entry.grid(row=2, column=3, padx=15, pady=(0, 12))

        # --- Output ---
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=4, column=0, padx=25, pady=8, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            output_frame, text="Output Dir:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        config = load_config()
        default_output = config.get("output_dir", "") or str(Path.home() / "DataVideoCodec_output")
        self.output_var = ctk.StringVar(value=default_output)
        self.output_entry = ctk.CTkEntry(output_frame, textvariable=self.output_var)
        self.output_entry.grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        self.output_browse_btn = ctk.CTkButton(
            output_frame, text="Browse...", width=100,
            command=self._browse_output,
        )
        self.output_browse_btn.grid(row=0, column=2, padx=15, pady=12)

        # --- Progress ---
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=5, column=0, padx=25, pady=8, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_var = ctk.StringVar(value="Ready to encode")
        self.status_label = ctk.CTkLabel(
            progress_frame, textvariable=self.status_var,
            font=ctk.CTkFont(size=12), text_color="gray",
        )
        self.status_label.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="w")

        # --- Encode Button ---
        self.encode_btn = ctk.CTkButton(
            self, text="▶ Start Encoding", font=ctk.CTkFont(size=16, weight="bold"),
            height=50, corner_radius=10, command=self._start_encode,
        )
        self.encode_btn.grid(row=6, column=0, padx=25, pady=15, sticky="ew")

    def _browse_file(self):
        path = filedialog.askopenfilename(title="Select Input File")
        if path:
            self.file_path_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_var.set(path)

    def _get_ecc_value(self) -> float:
        text = self.ecc_var.get().replace("%", "")
        return float(text) / 100

    def _start_encode(self):
        if self.encoding:
            return

        input_path = self.file_path_var.get()
        if input_path == "No file selected" or not Path(input_path).exists():
            self.status_var.set("❌ Please select a valid input file")
            return

        output_dir = self.output_var.get()
        if not output_dir:
            self.status_var.set("❌ Please specify an output directory")
            return

        params = EncodingParams(
            resolution=RESOLUTION_MAP[self.resolution_var.get()],
            block_size=int(self.block_size_var.get()),
            ecc_overhead=self._get_ecc_value(),
            fps=int(self.fps_var.get()),
        )

        self.encoding = True
        self.encode_btn.configure(state="disabled", text="Encoding...")

        thread = threading.Thread(
            target=self._encode_worker,
            args=(input_path, output_dir, params),
            daemon=True,
        )
        thread.start()

    def _encode_worker(self, input_path, output_dir, params):
        """Run encoding in a background thread."""
        try:
            config = load_config()
            controller = EncoderController(
                ffmpeg_path=config.get("ffmpeg_path", "ffmpeg")
            )

            def on_progress(pct, msg):
                self.after(0, lambda: self._update_progress(pct, msg))

            video_path, manifest_path = controller.run_encode(
                input_path=input_path,
                output_dir=output_dir,
                params=params,
                progress_cb=on_progress,
            )

            self.after(0, lambda: self._encode_complete(video_path, manifest_path))

        except Exception as e:
            self.after(0, lambda: self._encode_error(str(e)))

    def _update_progress(self, pct, msg):
        self.progress_bar.set(pct / 100)
        self.status_var.set(msg)

    def _encode_complete(self, video_path, manifest_path):
        self.encoding = False
        self.encode_btn.configure(state="normal", text="▶ Start Encoding")
        self.progress_bar.set(1.0)
        self.status_var.set(f"✅ Done! Video: {Path(video_path).name}")

    def _encode_error(self, error_msg):
        self.encoding = False
        self.encode_btn.configure(state="normal", text="▶ Start Encoding")
        self.progress_bar.set(0)
        self.status_var.set(f"❌ Error: {error_msg}")
