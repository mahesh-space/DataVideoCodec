"""
FrameExtractor module for the DataVideoCodec Decoder.

Extracts individual frames from a video file using FFmpeg
and reads them as NumPy arrays via OpenCV.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List

import cv2
import numpy as np

from core.utils import get_logger, ensure_dir

logger = get_logger("FrameExtractor")


class FrameExtractor:
    """Extracts frames from a video file using FFmpeg.

    Invokes FFmpeg to decompose a video into individual PNG frames,
    then reads each frame with OpenCV and converts to YCbCr color space.
    """

    @staticmethod
    def get_video_info(video_path: Path) -> dict:
        """Get video metadata (resolution and frame count) using ffprobe.

        Args:
            video_path: Path to the video file.

        Returns:
            Dictionary with 'width', 'height', and 'frame_count'.
        """
        # Get resolution
        ffprobe_res_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0",
            str(video_path)
        ]
        # Get frame count (sometimes 'nb_frames' is unavailable, so we use a more robust way)
        ffprobe_frames_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames", "-of", "csv=p=0",
            str(video_path)
        ]

        try:
            res_out = subprocess.run(
                ffprobe_res_cmd, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
            ).stdout.strip()
            width, height = map(int, res_out.split(","))
            
            frames_out = subprocess.run(
                ffprobe_frames_cmd, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL
            ).stdout.strip()
            # Handle cases where nb_frames is "N/A"
            try:
                frame_count = int(frames_out)
            except (ValueError, TypeError):
                frame_count = 0  # Unknown
                
            return {"width": width, "height": height, "frame_count": frame_count}
        except Exception as e:
            logger.error(f"Failed to probe video: {e}")
            raise RuntimeError(f"Could not probe video metadata: {e}")

    @staticmethod
    def extract(
        video_path: Path,
        ffmpeg_path: str = "ffmpeg",
    ):
        """Streaming generator to extract frames from a video file using FFmpeg piping.

        Yields:
            Each frame as a numpy array (height, width, 3) in YCbCr color space.

        Raises:
            FileNotFoundError: If video file doesn't exist.
            RuntimeError: If FFmpeg fails.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        info = FrameExtractor.get_video_info(video_path)
        width, height = info["width"], info["height"]

        # FFmpeg command to output raw bgr24 frames to stdout
        ffmpeg_cmd = [
            ffmpeg_path,
            "-nostdin",
            "-i", str(video_path),
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-",
        ]

        logger.info(f"Starting streaming extraction: {video_path} ({width}x{height})")
        
        # CRITICAL: Use DEVNULL for stderr to prevent pipe deadlock.
        # Use DEVNULL for stdin to prevent SIGTTIN hangs in background processes.
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8,
        )

        frame_size = width * height * 3
        frame_count = 0
        
        try:
            while True:
                raw_frame = process.stdout.read(frame_size)
                if len(raw_frame) < frame_size:
                    break
                
                bgr_frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
                ycrcb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2YCrCb)
                frame_count += 1
                yield ycrcb_frame

        except GeneratorExit:
            # Generator was closed early (e.g. caller stopped iterating)
            pass
        finally:
            process.stdout.close()
            process.terminate()
            process.wait()
            logger.info(f"Streaming extraction finished: {frame_count} frames yielded")
