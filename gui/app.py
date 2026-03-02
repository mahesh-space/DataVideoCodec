"""
MainWindow — GUI application entry point using CustomTkinter.

Provides the main application window with a persistent left sidebar
navigation panel and screen switching.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Dict

from core.config import load_config, save_config
from core.utils import setup_logging, get_logger

logger = get_logger("GUI")


class MainWindow(ctk.CTk):
    """Main application window with sidebar navigation.

    Contains five screens: Dashboard, Encode, Decode, Analytics, Settings.
    Screens are switched via the left sidebar navigation buttons.
    """

    def __init__(self):
        super().__init__()

        # Load config
        self.config = load_config()
        self._apply_theme()

        # Window setup
        self.title("DataVideoCodec — File ↔ Video Encoder")
        self.geometry("1200x800")
        self.minsize(1024, 768)

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Logo / title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="📹 DataVideoCodec",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text="File ↔ Video Codec",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Navigation buttons
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard", "🏠 Dashboard"),
            ("encode", "📤 Encode"),
            ("decode", "📥 Decode"),
            ("analytics", "📊 Analytics"),
            ("settings", "⚙️ Settings"),
        ]

        for i, (name, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=lambda n=name: self.switch_screen(n),
            )
            btn.grid(row=i + 2, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[name] = btn

        # Version label at bottom
        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self.version_label.grid(row=9, column=0, padx=20, pady=(0, 10))

        # --- Main content area ---
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Initialize screens (lazy loaded for performance)
        self.screens: Dict[str, ctk.CTkFrame] = {}
        self.current_screen = None

        # Show dashboard by default
        self.switch_screen("dashboard")

    def _apply_theme(self):
        """Apply theme from config."""
        theme = self.config.get("theme", "dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

    def _get_screen(self, name: str) -> ctk.CTkFrame:
        """Get or create a screen by name (lazy loading)."""
        if name not in self.screens:
            if name == "dashboard":
                from gui.dashboard import DashboardScreen
                self.screens[name] = DashboardScreen(self.content_frame, self)
            elif name == "encode":
                from gui.encode_screen import EncodeScreen
                self.screens[name] = EncodeScreen(self.content_frame, self)
            elif name == "decode":
                from gui.decode_screen import DecodeScreen
                self.screens[name] = DecodeScreen(self.content_frame, self)
            elif name == "analytics":
                from gui.analytics_screen import AnalyticsScreen
                self.screens[name] = AnalyticsScreen(self.content_frame, self)
            elif name == "settings":
                from gui.settings_screen import SettingsScreen
                self.screens[name] = SettingsScreen(self.content_frame, self)
        return self.screens[name]

    def switch_screen(self, name: str):
        """Switch to the specified screen.

        Args:
            name: Screen identifier ('dashboard', 'encode', 'decode', 'analytics', 'settings').
        """
        # Hide current screen
        if self.current_screen:
            self.current_screen.grid_forget()

        # Update nav button styles
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

        # Show new screen
        screen = self._get_screen(name)
        screen.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.current_screen = screen

        logger.info(f"Switched to screen: {name}")

    def refresh_config(self):
        """Reload configuration (called after settings change)."""
        self.config = load_config()
        self._apply_theme()


def launch_app():
    """Launch the DataVideoCodec GUI application."""
    setup_logging("INFO")
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    launch_app()
