#!/usr/bin/env python3
"""
DataVideoCodec System — CLI Entry Point

Provides command-line interface for encoding files to video,
decoding video to files, running performance analysis,
and launching the GUI.

Usage:
    python main.py encode --input file.pdf --output ./out
    python main.py decode --input encoded.mp4 --output ./recovered
    python main.py analyze --input test.txt --output ./results
    python main.py gui
"""

import argparse
import sys
from pathlib import Path

from core.models import EncodingParams
from core.constants import RESOLUTION_MAP, VALID_BLOCK_SIZES, VALID_ECC_OVERHEADS
from core.config import load_config
from core.utils import setup_logging


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="DataVideoCodec",
        description="Robust Data Encoding and Recovery Through Lossy Video Compression Channels",
    )
    parser.add_argument(
        "--log-level", default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Encode command ---
    encode_parser = subparsers.add_parser("encode", help="Encode a file into a video")
    encode_parser.add_argument("--input", "-i", required=True, help="Path to input file")
    encode_parser.add_argument("--output", "-o", required=True, help="Output directory")
    encode_parser.add_argument(
        "--resolution", "-r", default="720p",
        choices=list(RESOLUTION_MAP.keys()),
        help="Video resolution (default: 720p)",
    )
    encode_parser.add_argument(
        "--block-size", "-b", type=int, default=4,
        choices=VALID_BLOCK_SIZES,
        help="Pixel block size (default: 4)",
    )
    encode_parser.add_argument(
        "--ecc", "-e", type=float, default=0.2,
        choices=VALID_ECC_OVERHEADS,
        help="ECC overhead fraction (default: 0.2)",
    )
    encode_parser.add_argument(
        "--fps", type=int, default=30,
        help="Video frame rate (default: 30)",
    )

    # --- Decode command ---
    decode_parser = subparsers.add_parser("decode", help="Decode a video back to file")
    decode_parser.add_argument("--input", "-i", required=True, help="Path to encoded video")
    decode_parser.add_argument("--output", "-o", required=True, help="Output directory")
    decode_parser.add_argument(
        "--manifest", "-m", default=None,
        help="Path to encoding manifest JSON (auto-detected if not specified)",
    )
    decode_parser.add_argument(
        "--resolution", "-r", default=None,
        choices=list(RESOLUTION_MAP.keys()),
        help="Video resolution (required if no manifest)",
    )
    decode_parser.add_argument(
        "--block-size", "-b", type=int, default=None,
        choices=VALID_BLOCK_SIZES,
        help="Pixel block size (required if no manifest)",
    )
    decode_parser.add_argument(
        "--ecc", "-e", type=float, default=None,
        choices=VALID_ECC_OVERHEADS,
        help="ECC overhead fraction (required if no manifest)",
    )

    # --- Analyze command ---
    analyze_parser = subparsers.add_parser("analyze", help="Run performance analysis sweep")
    analyze_parser.add_argument("--input", "-i", required=True, help="Path to test file")
    analyze_parser.add_argument("--output", "-o", required=True, help="Output directory for results")

    # --- GUI command ---
    subparsers.add_parser("gui", help="Launch the graphical user interface")

    return parser.parse_args()


def cmd_encode(args):
    """Handle the encode command."""
    from encoder.controller import EncoderController

    config = load_config()
    params = EncodingParams(
        resolution=RESOLUTION_MAP[args.resolution],
        block_size=args.block_size,
        ecc_overhead=args.ecc,
        fps=args.fps,
    )

    controller = EncoderController(ffmpeg_path=config.get("ffmpeg_path", "ffmpeg"))
    video_path, manifest_path = controller.run_encode(
        input_path=args.input,
        output_dir=args.output,
        params=params,
    )

    print(f"\n✅ Encoding complete!")
    print(f"   Video:    {video_path}")
    print(f"   Manifest: {manifest_path}")


def cmd_decode(args):
    """Handle the decode command."""
    from decoder.controller import DecoderController

    config = load_config()

    # Auto-detect manifest
    manifest_path = args.manifest
    if manifest_path is None:
        auto_manifest = Path(args.input).with_suffix(".json")
        if auto_manifest.exists():
            manifest_path = str(auto_manifest)
            print(f"📄 Auto-detected manifest: {manifest_path}")

    # Build params if no manifest
    params = None
    if manifest_path is None and args.resolution and args.block_size and args.ecc:
        params = EncodingParams(
            resolution=RESOLUTION_MAP[args.resolution],
            block_size=args.block_size,
            ecc_overhead=args.ecc,
        )

    controller = DecoderController(ffmpeg_path=config.get("ffmpeg_path", "ffmpeg"))
    result = controller.run_decode(
        video_path=args.input,
        output_dir=args.output,
        params=params,
        manifest_path=manifest_path,
    )

    status_emoji = {"FULL_RECOVERY": "✅", "PARTIAL_RECOVERY": "⚠️", "RECOVERY_FAILURE": "❌"}
    print(f"\n{status_emoji.get(result.status, '❓')} {result.status}")
    print(f"   Output:     {result.output_path}")
    print(f"   Hash match: {result.hash_match}")
    print(f"   Errors corrected: {result.errors_corrected}")
    if result.errors_uncorrectable > 0:
        print(f"   Uncorrectable blocks: {result.errors_uncorrectable}")


def cmd_analyze(args):
    """Handle the analyze command."""
    from analysis.analyzer import PerformanceAnalyzer
    from analysis.plots import generate_ber_plot, generate_recovery_plot, generate_throughput_plot

    config = load_config()
    analyzer = PerformanceAnalyzer(ffmpeg_path=config.get("ffmpeg_path", "ffmpeg"))

    print("🔬 Starting performance analysis sweep (18 conditions)...")
    results = analyzer.run_sweep(
        test_file=args.input,
        output_dir=args.output,
    )

    # Generate plots
    output_dir = Path(args.output)
    generate_ber_plot(results, output_dir)
    generate_recovery_plot(results, output_dir)
    generate_throughput_plot(results, output_dir)

    print(f"\n📊 Analysis complete!")
    print(f"   Results CSV: {output_dir / 'sweep_results.csv'}")
    print(f"   Plots:       {output_dir}/*.png")


def cmd_gui():
    """Handle the GUI launch command."""
    from gui.app import launch_app
    launch_app()


def main():
    """Main entry point."""
    args = parse_args()

    if args.command is None:
        print("No command specified. Use --help for usage information.")
        sys.exit(1)

    # Set up logging
    config = load_config()
    log_level = args.log_level or config.get("log_level", "INFO")
    setup_logging(log_level)

    if args.command == "encode":
        cmd_encode(args)
    elif args.command == "decode":
        cmd_decode(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "gui":
        cmd_gui()
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
