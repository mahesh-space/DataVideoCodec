"""
Plot generation for performance analysis results.

Creates matplotlib figures for BER, recovery rate, and throughput
comparisons across encoding parameter configurations.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for GUI embedding
import matplotlib.pyplot as plt
import numpy as np

from core.utils import get_logger, ensure_dir

logger = get_logger("Plots")


def generate_ber_plot(results: List[dict], output_dir: Optional[Path] = None):
    """Generate BER comparison plot.

    Args:
        results: List of sweep result dictionaries.
        output_dir: Optional directory to save the plot as PNG.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Group by block_size
    block_sizes = sorted(set(r.get("block_size", 4) for r in results if "block_size" in r))
    ecc_overheads = sorted(set(r.get("ecc_overhead", 0.2) for r in results if "ecc_overhead" in r))

    x = np.arange(len(ecc_overheads))
    width = 0.25

    for i, bs in enumerate(block_sizes):
        ber_values = []
        for ecc in ecc_overheads:
            matching = [
                r.get("ber_after_ecc", 0)
                for r in results
                if r.get("block_size") == bs and r.get("ecc_overhead") == ecc
            ]
            ber_values.append(np.mean(matching) if matching else 0)

        ax.bar(x + i * width, ber_values, width, label=f"Block {bs}×{bs}")

    ax.set_xlabel("ECC Overhead (%)")
    ax.set_ylabel("Bit Error Rate (after ECC)")
    ax.set_title("BER vs. ECC Overhead by Block Size")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"{int(e*100)}%" for e in ecc_overheads])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    if output_dir:
        ensure_dir(Path(output_dir))
        fig.savefig(Path(output_dir) / "ber_plot.png", dpi=150)
        logger.info(f"BER plot saved to {output_dir}/ber_plot.png")

    return fig


def generate_recovery_plot(results: List[dict], output_dir: Optional[Path] = None):
    """Generate recovery rate comparison plot.

    Args:
        results: List of sweep result dictionaries.
        output_dir: Optional directory to save the plot as PNG.

    Returns:
        matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    block_sizes = sorted(set(r.get("block_size", 4) for r in results if "block_size" in r))
    ecc_overheads = sorted(set(r.get("ecc_overhead", 0.2) for r in results if "ecc_overhead" in r))

    x = np.arange(len(ecc_overheads))
    width = 0.25

    for i, bs in enumerate(block_sizes):
        recovery_rates = []
        for ecc in ecc_overheads:
            matching = [
                1.0 if r.get("hash_match", False) else 0.0
                for r in results
                if r.get("block_size") == bs and r.get("ecc_overhead") == ecc
            ]
            recovery_rates.append(np.mean(matching) * 100 if matching else 0)

        ax.bar(x + i * width, recovery_rates, width, label=f"Block {bs}×{bs}")

    ax.set_xlabel("ECC Overhead (%)")
    ax.set_ylabel("Recovery Rate (%)")
    ax.set_title("File Recovery Rate vs. ECC Overhead by Block Size")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"{int(e*100)}%" for e in ecc_overheads])
    ax.legend()
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    if output_dir:
        ensure_dir(Path(output_dir))
        fig.savefig(Path(output_dir) / "recovery_plot.png", dpi=150)
        logger.info(f"Recovery plot saved to {output_dir}/recovery_plot.png")

    return fig


def generate_throughput_plot(results: List[dict], output_dir: Optional[Path] = None):
    """Generate encoding/decoding throughput comparison plot.

    Args:
        results: List of sweep result dictionaries.
        output_dir: Optional directory to save the plot as PNG.

    Returns:
        matplotlib Figure object.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    resolutions = sorted(set(r.get("resolution", "720p") for r in results if "resolution" in r))
    block_sizes = sorted(set(r.get("block_size", 4) for r in results if "block_size" in r))

    x = np.arange(len(block_sizes))
    width = 0.35

    for ax_idx, (metric, title) in enumerate([
        ("encode_throughput_kbps", "Encoding Throughput"),
        ("decode_throughput_kbps", "Decoding Throughput"),
    ]):
        ax = axes[ax_idx]
        for i, res in enumerate(resolutions):
            values = []
            for bs in block_sizes:
                matching = [
                    r.get(metric, 0)
                    for r in results
                    if r.get("resolution") == res and r.get("block_size") == bs
                ]
                values.append(np.mean(matching) if matching else 0)

            ax.bar(x + i * width, values, width, label=res)

        ax.set_xlabel("Block Size")
        ax.set_ylabel("Throughput (KB/s)")
        ax.set_title(title)
        ax.set_xticks(x + width / 2)
        ax.set_xticklabels([f"{bs}×{bs}" for bs in block_sizes])
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()

    if output_dir:
        ensure_dir(Path(output_dir))
        fig.savefig(Path(output_dir) / "throughput_plot.png", dpi=150)
        logger.info(f"Throughput plot saved to {output_dir}/throughput_plot.png")

    return fig
