"""
Settings Screen for the DataVideoCodec GUI.

Allows configuration of default parameters, paths, theme,
and log verbosity with persistence to config.json.
"""

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.config import load_config, save_config
from core.constants import RESOLUTION_MAP, VALID_BLOCK_SIZES, VALID_ECC_OVERHEADS
from core.utils import get_logger

logger = get_logger("SettingsScreen")


class SettingsScreen(ctk.CTkFrame):
    """Settings panel for configuring application defaults."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        config = load_config()

        # --- Header ---
        header = ctk.CTkLabel(
            self, text="⚙️ Settings",
            font=ctk.CTkFont(size=28, weight="bold"), anchor="w",
        )
        header.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self, text="Configure application defaults and preferences",
            font=ctk.CTkFont(size=13), text_color="gray", anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="w")

        # --- Paths Section ---
        paths_frame = ctk.CTkFrame(self)
        paths_frame.grid(row=2, column=0, padx=25, pady=8, sticky="ew")
        paths_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            paths_frame, text="📂 Paths",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 8), sticky="w")

        # Output directory
        ctk.CTkLabel(paths_frame, text="Default Output Dir:").grid(
            row=1, column=0, padx=15, pady=8, sticky="w",
        )
        self.output_dir_var = ctk.StringVar(
            value=config.get("output_dir", str(Path.home() / "DataVideoCodec_output"))
        )
        ctk.CTkEntry(paths_frame, textvariable=self.output_dir_var).grid(
            row=1, column=1, padx=10, pady=8, sticky="ew",
        )
        ctk.CTkButton(
            paths_frame, text="Browse", width=80,
            command=lambda: self._browse_dir(self.output_dir_var),
        ).grid(row=1, column=2, padx=15, pady=8)

        # FFmpeg path
        ctk.CTkLabel(paths_frame, text="FFmpeg Path:").grid(
            row=2, column=0, padx=15, pady=8, sticky="w",
        )
        self.ffmpeg_var = ctk.StringVar(value=config.get("ffmpeg_path", "ffmpeg"))
        ctk.CTkEntry(paths_frame, textvariable=self.ffmpeg_var).grid(
            row=2, column=1, padx=10, pady=(8, 15), sticky="ew",
        )

        # --- Default Encoding Parameters ---
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=3, column=0, padx=25, pady=8, sticky="ew")
        params_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            params_frame, text="🔧 Default Encoding Parameters",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 8), sticky="w")

        # Resolution
        ctk.CTkLabel(params_frame, text="Resolution:").grid(
            row=1, column=0, padx=15, pady=5, sticky="w",
        )
        self.resolution_var = ctk.StringVar(value=config.get("default_resolution", "720p"))
        ctk.CTkOptionMenu(
            params_frame, values=list(RESOLUTION_MAP.keys()),
            variable=self.resolution_var, width=140,
        ).grid(row=2, column=0, padx=15, pady=(0, 12))

        # Block size
        ctk.CTkLabel(params_frame, text="Block Size:").grid(
            row=1, column=1, padx=15, pady=5, sticky="w",
        )
        self.block_size_var = ctk.StringVar(
            value=str(config.get("default_block_size", 4))
        )
        ctk.CTkSegmentedButton(
            params_frame, values=["2", "4", "8"],
            variable=self.block_size_var, width=140,
        ).grid(row=2, column=1, padx=15, pady=(0, 12))

        # ECC
        ctk.CTkLabel(params_frame, text="ECC Overhead:").grid(
            row=1, column=2, padx=15, pady=5, sticky="w",
        )
        ecc_pct = int(config.get("default_ecc_overhead", 0.2) * 100)
        self.ecc_var = ctk.StringVar(value=f"{ecc_pct}%")
        ctk.CTkOptionMenu(
            params_frame, values=["10%", "20%", "40%"],
            variable=self.ecc_var, width=140,
        ).grid(row=2, column=2, padx=15, pady=(0, 12))

        # --- Appearance ---
        appearance_frame = ctk.CTkFrame(self)
        appearance_frame.grid(row=4, column=0, padx=25, pady=8, sticky="ew")
        appearance_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            appearance_frame, text="🎨 Appearance",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")

        ctk.CTkLabel(appearance_frame, text="Theme:").grid(
            row=1, column=0, padx=15, pady=5, sticky="w",
        )
        self.theme_var = ctk.StringVar(value=config.get("theme", "dark"))
        ctk.CTkSegmentedButton(
            appearance_frame, values=["dark", "light", "system"],
            variable=self.theme_var, width=200,
            command=self._preview_theme,
        ).grid(row=2, column=0, padx=15, pady=(0, 12))

        ctk.CTkLabel(appearance_frame, text="Log Level:").grid(
            row=1, column=1, padx=15, pady=5, sticky="w",
        )
        self.log_level_var = ctk.StringVar(value=config.get("log_level", "INFO"))
        ctk.CTkOptionMenu(
            appearance_frame, values=["DEBUG", "INFO", "WARNING", "ERROR"],
            variable=self.log_level_var, width=140,
        ).grid(row=2, column=1, padx=15, pady=(0, 12))

        # --- Save Button ---
        self.save_btn = ctk.CTkButton(
            self, text="💾 Save Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50, corner_radius=10,
            command=self._save_settings,
        )
        self.save_btn.grid(row=5, column=0, padx=25, pady=15, sticky="ew")

        # --- Status ---
        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self, textvariable=self.status_var,
            font=ctk.CTkFont(size=12), text_color="gray",
        ).grid(row=6, column=0, padx=30, pady=(0, 10), sticky="w")

    def _browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _preview_theme(self, value):
        ctk.set_appearance_mode(value)

    def _save_settings(self):
        ecc_text = self.ecc_var.get().replace("%", "")
        config = {
            "output_dir": self.output_dir_var.get(),
            "ffmpeg_path": self.ffmpeg_var.get(),
            "default_resolution": self.resolution_var.get(),
            "default_block_size": int(self.block_size_var.get()),
            "default_ecc_overhead": float(ecc_text) / 100,
            "default_fps": 30,
            "theme": self.theme_var.get(),
            "log_level": self.log_level_var.get(),
        }
        save_config(config)
        self.app.refresh_config()
        self.status_var.set("✅ Settings saved successfully")
        logger.info("Settings saved")
