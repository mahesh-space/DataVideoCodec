"""
VideoAssembler module for the DataVideoCodec Encoder.

Assembles a sequence of video frames into an MP4 video file
using FFmpeg via subprocess calls.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path

import cv2
import numpy as np

from core.constants import DEFAULT_CRF
from core.utils import get_logger, ensure_dir

logger = get_logger("VideoAssembler")


class VideoAssembler:
    """Assembles frames into an MP4 video using FFmpeg.

    Writes frames as PNG images to a temporary directory, then invokes
    FFmpeg to encode them into an H.264 MP4 video with yuv420p pixel format.
    """

    @staticmethod
    def assemble(
        frames: list,
        output_path: Path,
        fps: int = 30,
        resolution: tuple = (1280, 720),
        ffmpeg_path: str = "ffmpeg",
        crf: int = DEFAULT_CRF,
    ) -> Path:
        """Assemble frames into an MP4 video file using piping.

        Args:
            frames: List of numpy arrays (height, width, 3) in YCbCr color space.
            output_path: Path for the output MP4 file.
            fps: Frames per second (default 30).
            resolution: Video resolution as (width, height).
            ffmpeg_path: Path to FFmpeg executable.
            crf: Constant Rate Factor for H.264 encoding quality.

        Returns:
            Path to the generated video file.

        Raises:
            RuntimeError: If FFmpeg fails.
        """
        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        width, height = resolution

        # FFmpeg command for reading raw BGR24 frames from stdin
        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",               # Overwrite output
            "-f", "rawvideo",   # Input format is raw video
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "bgr24", # We'll feed it BGR24
            "-framerate", str(fps),
            "-i", "-",          # Read from stdin
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(crf),
            "-preset", "medium",
            str(output_path),
        ]

        logger.info(f"Running FFmpeg via pipe: {' '.join(ffmpeg_cmd)}")

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8, # Large buffer for performance
        )

        try:
            for i, frame in enumerate(frames):
                # Convert YCbCr -> BGR for FFmpeg
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_YCrCb2BGR)
                process.stdin.write(frame_bgr.tobytes())

                if (i + 1) % 50 == 0:
                    logger.info(f"  Piped {i + 1}/{len(frames)} frames to FFmpeg")

            # Finalize encoding
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg piping failed: {stderr.decode()}")
                raise RuntimeError(f"FFmpeg failed (code {process.returncode})")

        except Exception as e:
            process.kill()
            logger.error(f"Error during FFmpeg piping: {e}")
            raise RuntimeError(f"Video assembly failed: {e}")

        logger.info(f"Video assembled successfully: {output_path}")
        return output_path
