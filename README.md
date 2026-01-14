# Video to MP3 & Transcription Tool

A beautiful Electron-based desktop application that batch converts video files to MP3 audio and generates text transcriptions with speaker identification.

## Features

- 🎥 **Batch Processing**: Select an entire folder of videos to process at once
- 🎵 **MP3 Conversion**: Extracts audio from videos and saves as MP3 files
- 🤖 **AI Transcription**: Uses OpenAI's Whisper for state-of-the-art transcription
- 🗣️ **Speaker Diarization**: Automatically identifies and labels different speakers
- 🌏 **Multi-Language**: Excellent support for Japanese, English, and mixed audio
- 🎯 **Offline Processing**: Runs locally on your machine, no API keys needed
- 🎨 **Modern UI**: Clean, intuitive interface with real-time progress tracking
- 📊 **Live Logs**: Monitor processing status with detailed console output

## Supported Video Formats

- MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V

## Transcription Quality

This tool uses **OpenAI Whisper (medium model)** which provides:
- ✅ **Superior accuracy** compared to cloud APIs
- ✅ **Excellent Japanese support** (handles Kanji, Hiragana, Katakana)
- ✅ **Mixed language detection** (auto-detects Japanese/English)
- ✅ **Background noise handling**
- ✅ **Accent recognition**
- ✅ **99+ languages supported**

## Prerequisites

### System Requirements

1. **Node.js** (v14 or higher)
   - Download from: https://nodejs.org/

2. **Python 3** (v3.6 or higher)
   - macOS: Usually pre-installed, or install via Homebrew: `brew install python3`
   - Windows: Download from https://www.python.org/
   - Linux: `sudo apt-get install python3`

3. **FFmpeg** (required for audio processing)
   - macOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/ and add to PATH
   - Linux: `sudo apt-get install ffmpeg`

## Installation

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Or install individually:
```bash
pip3 install moviepy pydub ffmpeg-python openai-whisper pyannote.audio torch torchaudio
```

### 3. (Optional) Setup Speaker Diarization

For speaker identification to work, you need a Hugging Face token:

1. Create a free account at https://huggingface.co/
2. Accept the terms for the model at: https://huggingface.co/pyannote/speaker-diarization-3.1
3. Generate an access token at: https://huggingface.co/settings/tokens
4. Set the environment variable:
   ```bash
   export HUGGINGFACE_TOKEN="your_token_here"
   ```

**Note**: The app will work without this token, but speaker identification will be disabled.

## Usage

### Start the Application

```bash
npm start
```

### Using the App

1. **Select Input Folder**: Click "Select Video Folder" and choose a folder containing your video files
2. **Select Output Folder**: Click "Select Output Folder" and choose where to save the MP3s and transcriptions
3. **Start Processing**: Click "Start Processing" to begin batch conversion
4. **Monitor Progress**: Watch the real-time progress bar and logs

### Output Files

For each video file, the app creates:
- `filename.mp3` - The extracted audio
- `filename_transcript.txt` - The transcribed text with:
  - Detected language
  - Timestamped segments with speaker labels
  - Full transcript text

**Example transcript format:**
```
Detected Language: ja
================================================================================

[00:00:05 -> 00:00:08] SPEAKER_00: こんにちは、今日は良い天気ですね。
[00:00:09 -> 00:00:12] SPEAKER_01: Yes, it's a beautiful day!
[00:00:13 -> 00:00:16] SPEAKER_00: Let's start the meeting.

================================================================================
FULL TRANSCRIPT:
================================================================================
こんにちは、今日は良い天気ですね。Yes, it's a beautiful day! Let's start the meeting.
```

## Project Structure

```
windsurf-project/
├── main.js                 # Electron main process
├── preload.js             # Electron preload script (IPC bridge)
├── index.html             # Main UI
├── styles.css             # Application styling
├── renderer.js            # UI logic and event handlers
├── batch_processor.py     # Python backend for video processing
├── video_to_transcript.py # Single video processing script
├── package.json           # Node.js dependencies
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## How It Works

1. **Electron Frontend**: Provides the GUI and handles folder selection
2. **IPC Communication**: Bridges the Electron UI with the Python backend
3. **Python Backend**: Processes videos using:
   - `moviepy` for video/audio extraction
   - `pydub` for audio format conversion
   - `OpenAI Whisper` for AI-powered transcription
   - `pyannote.audio` for speaker diarization (identification)
   - `PyTorch` for deep learning model execution

## Troubleshooting

### "FFmpeg not found" error
- Make sure FFmpeg is installed and accessible in your PATH
- Test by running `ffmpeg -version` in terminal

### "No module named 'moviepy'" or "No module named 'whisper'" error
- Install Python dependencies: `pip3 install -r requirements.txt`
- For M1/M2 Macs, you may need to install PyTorch separately first:
  ```bash
  pip3 install torch torchaudio
  ```

### First run is slow
- Whisper downloads the model (~1.5GB for medium) on first use
- Subsequent runs will be much faster
- The model is cached in `~/.cache/whisper/`

### Speaker diarization not working
- Make sure you've set the `HUGGINGFACE_TOKEN` environment variable
- Accept the model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
- The app will still transcribe without speaker labels if this fails

### Out of memory errors
- The medium model requires ~5GB RAM
- For lower-end machines, edit `batch_processor.py` and change `"medium"` to `"small"` or `"base"`
- Small model: ~2GB RAM, Base model: ~1GB RAM

### "python3: command not found"
- Edit `main.js` line 67 and change `python3` to `python`

### Mixed language transcription issues
- Whisper auto-detects language by default
- For better Japanese/English mixing, the medium model is recommended
- Large model provides even better accuracy but requires ~10GB RAM

## Development

Run in development mode:
```bash
npm run dev
```

## Notes

- **Offline Processing**: Whisper runs completely offline after initial model download
- **Processing Time**: First video takes longer due to model loading; subsequent videos are faster
- **GPU Acceleration**: Automatically uses CUDA if available for faster processing
- **Sequential Processing**: Videos are processed one at a time to manage memory usage
- **Model Selection**: Medium model balances accuracy and speed for Japanese/English
- **Speaker Labels**: Speakers are labeled as SPEAKER_00, SPEAKER_01, etc.

## License

MIT
