"""
Constants for the DataVideoCodec System.

Defines pixel intensity values, sync patterns, resolution presets,
and valid parameter ranges used across encoder and decoder modules.
"""

# --- Luma Channel Intensity Values ---
# ITU-R BT.601 legal range: 16-235
LUMA_HIGH = 235      # Represents binary 1
LUMA_LOW = 16        # Represents binary 0
CHROMA_NEUTRAL = 128 # Neutral chroma value (no color)

# --- Decision Threshold ---
THRESHOLD = 128  # Midpoint for bit extraction decision boundary

# --- Sync Marker ---
# Alternating pattern used in the first rows of each frame for alignment.
# Pattern repeats across the frame width. Values chosen to be clearly
# distinguishable even after compression.
SYNC_PATTERN = [LUMA_LOW, LUMA_HIGH] * 4  # 8-pixel alternating pattern
SYNC_ROWS = 2  # Number of rows reserved for the sync marker

# --- Resolution Presets ---
RES_720P = (1280, 720)
RES_1080P = (1920, 1080)

RESOLUTION_MAP = {
    "720p": RES_720P,
    "1080p": RES_1080P,
}

# --- Valid Parameter Ranges ---
VALID_BLOCK_SIZES = [2, 4, 8]
VALID_ECC_OVERHEADS = [0.1, 0.2, 0.4]
DEFAULT_FPS = 30
DEFAULT_CRF = 18  # FFmpeg CRF for encoding quality

# --- Header Format ---
HEADER_MAGIC = b"DVCD"          # 4 bytes - magic identifier
HEADER_FILESIZE_BYTES = 4       # 4 bytes - uint32 big-endian file size
HEADER_FILENAME_BYTES = 256     # 256 bytes - filename (UTF-8, null-padded)
HEADER_TOTAL_BYTES = 4 + 4 + 256  # 264 bytes total header

# --- Reed-Solomon Parameters ---
# RS(255, k) codeword size
RS_CODEWORD_SIZE = 255
