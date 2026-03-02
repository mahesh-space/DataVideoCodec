"""
Analytics Screen for the DataVideoCodec GUI.

Displays interactive performance charts and supports running
parameter sweep analysis with results export.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from core.config import load_config
from analysis.analyzer import PerformanceAnalyzer
from analysis.plots import generate_ber_plot, generate_recovery_plot, generate_throughput_plot
from core.utils import get_logger

logger = get_logger("AnalyticsScreen")


class AnalyticsScreen(ctk.CTkFrame):
    """Analytics screen with embedded matplotlib charts and sweep controls."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.running = False
        self.results = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Header ---
        header = ctk.CTkLabel(
            self, text="📊 Performance Analytics",
            font=ctk.CTkFont(size=28, weight="bold"), anchor="w",
        )
        header.grid(row=0, column=0, padx=30, pady=(25, 5), sticky="w")

        # --- Controls ---
        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, padx=25, pady=8, sticky="ew")
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            controls, text="Test File:", font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.file_var = ctk.StringVar(value="No file selected")
        ctk.CTkLabel(
            controls, textvariable=self.file_var, font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        ctk.CTkButton(
            controls, text="Browse...", width=100, command=self._browse_file,
        ).grid(row=0, column=2, padx=5, pady=12)

        self.run_btn = ctk.CTkButton(
            controls, text="▶ Run Sweep", width=120, command=self._start_sweep,
            fg_color="green", hover_color="darkgreen",
        )
        self.run_btn.grid(row=0, column=3, padx=5, pady=12)

        self.export_btn = ctk.CTkButton(
            controls, text="📁 Export CSV", width=120,
            command=self._export_csv, state="disabled",
        )
        self.export_btn.grid(row=0, column=4, padx=15, pady=12)

        # --- Progress ---
        self.progress_var = ctk.StringVar(value="Select a test file and run the 18-condition sweep")
        ctk.CTkLabel(
            self, textvariable=self.progress_var,
            font=ctk.CTkFont(size=12), text_color="gray",
        ).grid(row=2, column=0, padx=30, pady=5, sticky="w")

        # --- Chart Area ---
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.grid(row=3, column=0, padx=25, pady=10, sticky="nsew")
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)

        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="📈 Charts will appear here after running the analysis sweep",
            font=ctk.CTkFont(size=14), text_color="gray",
        )
        self.placeholder.grid(row=0, column=0, padx=20, pady=40)

        # Chart tabs
        self.chart_tabs = None
        self.canvas_widgets = []

    def _browse_file(self):
        path = filedialog.askopenfilename(title="Select Test File")
        if path:
            self.file_var.set(path)

    def _start_sweep(self):
        if self.running:
            return

        file_path = self.file_var.get()
        if file_path == "No file selected" or not Path(file_path).exists():
            self.progress_var.set("❌ Please select a valid test file")
            return

        self.running = True
        self.run_btn.configure(state="disabled", text="Running...")

        output_dir = Path(file_path).parent / "analysis_results"

        thread = threading.Thread(
            target=self._sweep_worker, args=(file_path, str(output_dir)),
            daemon=True,
        )
        thread.start()

    def _sweep_worker(self, file_path, output_dir):
        try:
            config = load_config()
            analyzer = PerformanceAnalyzer(
                ffmpeg_path=config.get("ffmpeg_path", "ffmpeg")
            )

            def on_progress(pct, msg):
                self.after(0, lambda: self.progress_var.set(f"[{pct:.0f}%] {msg}"))

            results = analyzer.run_sweep(
                test_file=file_path, output_dir=output_dir, progress_cb=on_progress,
            )

            self.results = results
            self.after(0, lambda: self._display_results(results, output_dir))

        except Exception as e:
            self.after(0, lambda: self._sweep_error(str(e)))

    def _display_results(self, results, output_dir):
        self.running = False
        self.run_btn.configure(state="normal", text="▶ Run Sweep")
        self.export_btn.configure(state="normal")
        self.progress_var.set(f"✅ Sweep complete: {len(results)} conditions tested")

        # Remove placeholder
        self.placeholder.grid_forget()

        # Clear previous charts
        for w in self.canvas_widgets:
            w.destroy()
        self.canvas_widgets = []

        # Create tabview for charts
        if self.chart_tabs:
            self.chart_tabs.destroy()

        self.chart_tabs = ctk.CTkTabview(self.chart_frame)
        self.chart_tabs.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # BER Plot
        tab_ber = self.chart_tabs.add("BER")
        fig_ber = generate_ber_plot(results)
        self._embed_figure(fig_ber, tab_ber)

        # Recovery Rate Plot
        tab_rec = self.chart_tabs.add("Recovery Rate")
        fig_rec = generate_recovery_plot(results)
        self._embed_figure(fig_rec, tab_rec)

        # Throughput Plot
        tab_tp = self.chart_tabs.add("Throughput")
        fig_tp = generate_throughput_plot(results)
        self._embed_figure(fig_tp, tab_tp)

    def _embed_figure(self, fig, parent):
        """Embed a matplotlib figure in a CustomTkinter frame."""
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)
        self.canvas_widgets.append(widget)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()
        self.canvas_widgets.append(toolbar)

    def _sweep_error(self, error_msg):
        self.running = False
        self.run_btn.configure(state="normal", text="▶ Run Sweep")
        self.progress_var.set(f"❌ Error: {error_msg}")

    def _export_csv(self):
        if not self.results:
            return
        path = filedialog.asksaveasfilename(
            title="Export Results as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if path:
            import csv
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
            self.progress_var.set(f"📁 Exported to {Path(path).name}")
