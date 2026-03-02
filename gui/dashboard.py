"""
Dashboard Screen for the DataVideoCodec GUI.

Displays system status, recent operations overview,
and quick-access buttons for primary workflows.
"""

import customtkinter as ctk
from core.utils import get_logger

logger = get_logger("Dashboard")


class DashboardScreen(ctk.CTkFrame):
    """Dashboard screen showing system overview and quick actions."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Header ---
        header = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Robust Data Encoding & Recovery Through Lossy Video Compression",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="w")

        # --- Quick Action Cards ---
        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=2, column=0, columnspan=2, padx=25, pady=10, sticky="ew")
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._create_action_card(
            actions_frame, 0, "📤", "Encode File",
            "Transform any file into a video",
            lambda: app.switch_screen("encode"),
        )
        self._create_action_card(
            actions_frame, 1, "📥", "Decode Video",
            "Recover original file from video",
            lambda: app.switch_screen("decode"),
        )
        self._create_action_card(
            actions_frame, 2, "📊", "Run Analysis",
            "Performance sweep across parameters",
            lambda: app.switch_screen("analytics"),
        )

        # --- Status Cards ---
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=3, column=0, padx=(25, 10), pady=10, sticky="nsew")
        status_frame.grid_columnconfigure(0, weight=1)

        status_title = ctk.CTkLabel(
            status_frame,
            text="📈 System Status",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        status_title.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        self.status_items = {}
        status_data = [
            ("FFmpeg", "✅ Available"),
            ("Last BER", "—"),
            ("Last Recovery", "—"),
            ("Operations", "0 encode / 0 decode"),
        ]
        for i, (label, value) in enumerate(status_data):
            row_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
            row_frame.grid(row=i + 1, column=0, padx=15, pady=2, sticky="ew")
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row_frame, text=label, font=ctk.CTkFont(size=12),
                text_color="gray", anchor="w",
            ).grid(row=0, column=0, sticky="w")

            val_label = ctk.CTkLabel(
                row_frame, text=value, font=ctk.CTkFont(size=12, weight="bold"),
                anchor="e",
            )
            val_label.grid(row=0, column=1, sticky="e")
            self.status_items[label] = val_label

        # --- Info Card ---
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=3, column=1, padx=(10, 25), pady=10, sticky="nsew")
        info_frame.grid_columnconfigure(0, weight=1)

        info_title = ctk.CTkLabel(
            info_frame,
            text="ℹ️ About",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        info_title.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        about_text = (
            "This system encodes arbitrary files into video frames "
            "using pixel-level bit encoding in the Y (Luma) channel. "
            "Reed-Solomon ECC protects against compression errors.\n\n"
            "Designed to survive lossy compression channels including "
            "YouTube H.264/H.265 processing."
        )
        info_label = ctk.CTkLabel(
            info_frame,
            text=about_text,
            font=ctk.CTkFont(size=12),
            wraplength=350,
            justify="left",
            anchor="nw",
        )
        info_label.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nw")

        # Pipeline diagram
        pipeline_text = "📄 File → 🔢 Bits → 🛡️ ECC → 🖼️ Frames → 🎬 Video"
        pipeline_label = ctk.CTkLabel(
            info_frame,
            text=pipeline_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("dodgerblue", "deepskyblue"),
        )
        pipeline_label.grid(row=2, column=0, padx=15, pady=(5, 15))

        self.grid_rowconfigure(3, weight=1)

    def _create_action_card(self, parent, col, icon, title, desc, command):
        """Create a quick-action card widget."""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=0, column=col, padx=8, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        icon_label = ctk.CTkLabel(
            card, text=icon, font=ctk.CTkFont(size=36),
        )
        icon_label.grid(row=0, column=0, padx=15, pady=(15, 5))

        title_label = ctk.CTkLabel(
            card, text=title, font=ctk.CTkFont(size=15, weight="bold"),
        )
        title_label.grid(row=1, column=0, padx=15, pady=2)

        desc_label = ctk.CTkLabel(
            card, text=desc, font=ctk.CTkFont(size=11),
            text_color="gray", wraplength=200,
        )
        desc_label.grid(row=2, column=0, padx=15, pady=(0, 8))

        btn = ctk.CTkButton(
            card, text="Open →", command=command,
            height=32, corner_radius=8,
        )
        btn.grid(row=3, column=0, padx=15, pady=(5, 15))
