# 📹 DataVideoCodec

**Robust Data Encoding and Recovery Through Lossy Video Compression Channels**

DataVideoCodec encodes arbitrary digital files into video frames, transmits them through lossy compression channels (H.264/MP4), and recovers the original files using Reed-Solomon error correction. It ships with a full CLI, a desktop GUI, and an automated performance analysis suite.

---

## ✨ Features

- **Encode any file to video** — PDFs, images, executables, archives — any binary file becomes an MP4 video.
- **Reed-Solomon ECC** — Configurable error-correction overhead (10%, 20%, 40%) enables data recovery even after lossy video compression.
- **Decode & recover** — Extract and reconstruct the original file from the encoded video with SHA-256 integrity verification.
- **Performance analysis** — Automated 18-condition parameter sweep across resolutions, block sizes, and ECC levels with CSV export and publication-ready plots.
- **Desktop GUI** — Modern CustomTkinter interface with Dashboard, Encode, Decode, Analytics, and Settings screens.
- **Multi-file support** — Encode multiple files into a single video stream with per-file boundary tracking.

---

## 🏗️ Architecture

```
┌─────────────────── ENCODING PIPELINE ───────────────────┐
│                                                         │
│  File → FileReader → BitstreamConverter → ECCEncoder    │
│       → FrameGenerator → VideoAssembler → .mp4 + .json  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────── DECODING PIPELINE ───────────────────┐
│                                                         │
│  .mp4 → FrameExtractor → SyncDetector → BitExtractor    │
│       → ECCDecoder → FileReconstructor → Recovered File │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Project Structure

```
codec/
├── main.py                 # CLI entry point
├── config.json             # User configuration
├── requirements.txt        # Python dependencies
├── core/                   # Shared models, constants, config, utilities
│   ├── config.py           # JSON config load/save
│   ├── constants.py        # Luma values, sync patterns, resolution presets
│   ├── models.py           # EncodingParams, RecoveryResult, Manifest
│   └── utils.py            # SHA-256 hashing, logging, directory helpers
├── encoder/                # File → Video encoding pipeline
│   ├── controller.py       # EncoderController (orchestrates pipeline)
│   ├── file_reader.py      # Reads input file bytes + metadata
│   ├── bitstream.py        # Header construction & byte↔bit conversion
│   ├── ecc_encoder.py      # Reed-Solomon forward error correction
│   ├── frame_generator.py  # Maps bit array to YUV video frames
│   └── video_assembler.py  # FFmpeg-based MP4 assembly
├── decoder/                # Video → File decoding pipeline
│   ├── controller.py       # DecoderController (orchestrates pipeline)
│   ├── frame_extractor.py  # Extracts YUV frames from video via FFmpeg
│   ├── sync_detector.py    # Detects sync marker rows for frame alignment
│   ├── bit_extractor.py    # Extracts bits from pixel blocks
│   ├── ecc_decoder.py      # Reed-Solomon error correction & decoding
│   └── file_reconstructor.py  # Reconstructs original file from bytes
├── gui/                    # Desktop GUI (CustomTkinter)
│   ├── app.py              # Main window & sidebar navigation
│   ├── dashboard.py        # Dashboard overview screen
│   ├── encode_screen.py    # Encode file interface
│   ├── decode_screen.py    # Decode video interface
│   ├── analytics_screen.py # Performance analysis interface
│   └── settings_screen.py  # Configuration settings
├── analysis/               # Performance analysis module
│   ├── analyzer.py         # 18-condition parameter sweep engine
│   └── plots.py            # BER, recovery rate, throughput charts
└── tests/                  # Unit & integration tests
    ├── test_encoder.py     # Encoder pipeline tests
    ├── test_decoder.py     # Decoder pipeline tests
    └── test_roundtrip.py   # End-to-end encode→decode tests
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **FFmpeg** — must be installed and accessible on your `PATH`  
  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu / Debian
  sudo apt install ffmpeg

  # Windows (via Chocolatey)
  choco install ffmpeg
  ```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd codec

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 📖 Usage

### CLI

```bash
# Encode a file into a video
python main.py encode -i document.pdf -o ./output

# Encode with custom parameters
python main.py encode -i photo.png -o ./output -r 1080p -b 8 -e 0.4 --fps 24

# Decode a video back to the original file
python main.py decode -i ./output/document_encoded.mp4 -o ./recovered

# Decode with explicit manifest
python main.py decode -i encoded.mp4 -o ./recovered -m encoded.json

# Run performance analysis sweep (18 conditions)
python main.py analyze -i testfile.txt -o ./results

# Launch the GUI
python main.py gui
```

### GUI

```bash
python main.py gui
```

The GUI provides five screens accessible via the sidebar:

| Screen | Description |
|---|---|
| **🏠 Dashboard** | Overview and quick-start actions |
| **📤 Encode** | Select file, configure parameters, encode to video |
| **📥 Decode** | Select video, decode and verify recovered file |
| **📊 Analytics** | Run parameter sweeps and visualize performance |
| **⚙️ Settings** | Configure FFmpeg path, theme, defaults |

---

## ⚙️ Configuration

Settings are stored in `config.json`:

| Key | Default | Description |
|---|---|---|
| `default_resolution` | `"720p"` | Video resolution (`720p` or `1080p`) |
| `default_block_size` | `4` | Pixel block size (`2`, `4`, or `8`) |
| `default_ecc_overhead` | `0.2` | ECC redundancy fraction (`0.1`, `0.2`, `0.4`) |
| `default_fps` | `30` | Video frame rate |
| `ffmpeg_path` | `"ffmpeg"` | Path to FFmpeg executable |
| `theme` | `"dark"` | GUI theme (`dark` or `light`) |
| `log_level` | `"INFO"` | Logging verbosity |

---

## 🔬 How It Works

### Encoding

1. **Read** the input file and compute its SHA-256 hash.
2. **Build a header** containing a magic identifier (`DVCD`), file size, and filename.
3. **Apply Reed-Solomon ECC** encoding over the header + payload data.
4. **Convert** the ECC-encoded bytes to a bit array.
5. **Generate video frames** — each bit maps to a `block_size × block_size` pixel block (luma high = 1, luma low = 0). Sync marker rows are added for frame alignment.
6. **Assemble** frames into an H.264 MP4 video using FFmpeg.
7. **Save a manifest** (JSON) with all parameters needed for decoding.

### Decoding

1. **Extract frames** from the MP4 video via FFmpeg.
2. **Detect sync markers** to align each frame.
3. **Extract bits** from pixel blocks using a threshold decision boundary.
4. **Apply Reed-Solomon ECC** decoding to correct errors introduced by lossy compression.
5. **Parse the header** and **reconstruct** the original file.
6. **Verify integrity** via SHA-256 hash comparison.

---

## 📊 Performance Analysis

The analyzer tests all 18 combinations of:

| Parameter | Values |
|---|---|
| Resolution | 720p, 1080p |
| Block Size | 2×2, 4×4, 8×8 |
| ECC Overhead | 10%, 20%, 40% |

**Outputs:**
- `sweep_results.csv` — full metrics for every condition
- `ber_plot.png` — Bit Error Rate before/after ECC
- `recovery_plot.png` — Recovery success rates
- `throughput_plot.png` — Encode/decode throughput (KB/s)

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_encoder.py -v
python -m pytest tests/test_decoder.py -v
python -m pytest tests/test_roundtrip.py -v
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `numpy` | Numerical operations & array handling |
| `opencv-python` | Frame image processing |
| `reedsolo` | Reed-Solomon error correction |
| `matplotlib` | Performance analysis plots |
| `customtkinter` | Modern desktop GUI |
| `Pillow` | Image processing support |
| `pandas` | Data analysis & CSV handling |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📋 Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md) code of conduct. By participating, you are expected to uphold this code.
