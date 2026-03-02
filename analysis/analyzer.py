"""
PerformanceAnalyzer module for the DataVideoCodec System.

Systematically evaluates system performance across variable encoding
parameters using an automated 18-condition parameter sweep.
"""

import time
import csv
from pathlib import Path
from typing import Callable, List, Optional
from itertools import product

import numpy as np

from core.models import EncodingParams, RecoveryResult
from core.constants import VALID_BLOCK_SIZES, VALID_ECC_OVERHEADS, RESOLUTION_MAP
from core.utils import get_logger, ensure_dir, compute_hash
from encoder.controller import EncoderController
from decoder.controller import DecoderController

logger = get_logger("PerformanceAnalyzer")


class PerformanceAnalyzer:
    """Manages batch parameter sweep testing across encoding configurations.

    Tests all combinations of:
      - Resolution: 720p, 1080p
      - Block size: 2×2, 4×4, 8×8
      - ECC overhead: 10%, 20%, 40%
    
    Total: 2 × 3 × 3 = 18 conditions.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.encoder = EncoderController(ffmpeg_path=ffmpeg_path)
        self.decoder = DecoderController(ffmpeg_path=ffmpeg_path)

    def run_sweep(
        self,
        test_file: str,
        output_dir: str,
        conditions: Optional[List[dict]] = None,
        progress_cb: Optional[Callable[[float, str], None]] = None,
    ) -> List[dict]:
        """Run a complete parameter sweep.

        Args:
            test_file: Path to the test input file.
            output_dir: Base output directory for all test results.
            conditions: Optional list of condition dicts. If None, uses the
                        full 18-condition matrix.
            progress_cb: Optional progress callback(percent, message).

        Returns:
            List of result dictionaries, one per condition.
        """
        test_file = Path(test_file)
        output_dir = Path(output_dir)
        ensure_dir(output_dir)

        if conditions is None:
            conditions = self._generate_conditions()

        total = len(conditions)
        results = []
        original_hash = compute_hash(test_file)

        for i, cond in enumerate(conditions):
            pct = (i / total) * 100
            label = (
                f"Condition {i+1}/{total}: "
                f"{cond['resolution_name']}, "
                f"block={cond['block_size']}, "
                f"ecc={cond['ecc_overhead']*100:.0f}%"
            )

            if progress_cb:
                progress_cb(pct, label)
            logger.info(f"--- {label} ---")

            cond_dir = output_dir / f"cond_{i+1:02d}"
            ensure_dir(cond_dir)

            params = EncodingParams(
                resolution=cond["resolution"],
                block_size=cond["block_size"],
                ecc_overhead=cond["ecc_overhead"],
            )

            try:
                result = self._run_single(
                    test_file, cond_dir, params, original_hash
                )
                result["condition_id"] = i + 1
                result["resolution"] = cond["resolution_name"]
                result["block_size"] = cond["block_size"]
                result["ecc_overhead"] = cond["ecc_overhead"]
                results.append(result)
            except Exception as e:
                logger.error(f"Condition {i+1} failed: {e}")
                results.append({
                    "condition_id": i + 1,
                    "resolution": cond["resolution_name"],
                    "block_size": cond["block_size"],
                    "ecc_overhead": cond["ecc_overhead"],
                    "status": "ERROR",
                    "error": str(e),
                })

        # Export CSV
        csv_path = output_dir / "sweep_results.csv"
        self._export_csv(results, csv_path)

        if progress_cb:
            progress_cb(100, f"Sweep complete: {len(results)} conditions tested")

        return results

    def _run_single(
        self, test_file: Path, output_dir: Path, params: EncodingParams,
        original_hash: str,
    ) -> dict:
        """Run encode-decode for a single parameter condition."""
        # Encode
        t_start_enc = time.time()
        video_path, manifest_path = self.encoder.run_encode(
            str(test_file), str(output_dir), params
        )
        encode_time = time.time() - t_start_enc

        # Decode
        t_start_dec = time.time()
        recovery = self.decoder.run_decode(
            str(video_path), str(output_dir / "recovered"),
            manifest_path=str(manifest_path),
        )
        decode_time = time.time() - t_start_dec

        filesize_kb = test_file.stat().st_size / 1024

        return {
            "status": recovery.status,
            "hash_match": recovery.hash_match,
            "ber_before_ecc": recovery.ber_before_ecc,
            "ber_after_ecc": recovery.ber_after_ecc,
            "errors_corrected": recovery.errors_corrected,
            "errors_uncorrectable": recovery.errors_uncorrectable,
            "encode_time_s": round(encode_time, 2),
            "decode_time_s": round(decode_time, 2),
            "encode_throughput_kbps": round(filesize_kb / encode_time, 2) if encode_time > 0 else 0,
            "decode_throughput_kbps": round(filesize_kb / decode_time, 2) if decode_time > 0 else 0,
        }

    @staticmethod
    def _generate_conditions() -> List[dict]:
        """Generate the full 18-condition parameter matrix."""
        conditions = []
        for res_name, res in RESOLUTION_MAP.items():
            for bs in VALID_BLOCK_SIZES:
                for ecc in VALID_ECC_OVERHEADS:
                    conditions.append({
                        "resolution_name": res_name,
                        "resolution": res,
                        "block_size": bs,
                        "ecc_overhead": ecc,
                    })
        return conditions

    @staticmethod
    def _export_csv(results: List[dict], csv_path: Path) -> None:
        """Export sweep results to CSV."""
        if not results:
            return
        fieldnames = results[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Results exported to {csv_path}")
