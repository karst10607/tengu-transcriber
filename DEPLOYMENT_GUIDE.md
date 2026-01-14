# Cross-Platform Deployment Guide

## 📦 Model Storage Locations by Platform

### Default System Cache Locations

| Platform | Whisper | Pyannote | Sentence Transformers | Ollama |
|----------|---------|----------|----------------------|--------|
| **macOS** | `~/.cache/whisper/` | `~/.cache/torch/pyannote/` | `~/.cache/sentence_transformers/` | `~/.ollama/models/` |
| **Linux** | `~/.cache/whisper/` | `~/.cache/torch/pyannote/` | `~/.cache/sentence_transformers/` | `~/.ollama/models/` |
| **Windows** | `C:\Users\<user>\.cache\whisper\` | `C:\Users\<user>\.cache\torch\pyannote\` | `C:\Users\<user>\.cache\sentence_transformers\` | `C:\Users\<user>\.ollama\models\` |

### Model Sizes

| Model | Size | Required |
|-------|------|----------|
| **Whisper tiny** | 39 MB | ✅ One required |
| **Whisper base** | 74 MB | ✅ One required |
| **Whisper small** | 244 MB | ✅ One required |
| **Whisper medium** | 769 MB | ✅ Recommended |
| **Whisper large** | 1.5 GB | ✅ One required |
| **Pyannote diarization** | 17 MB | ✅ Required |
| **Sentence Transformers** | 120 MB | ⚠️ Optional (for semantic search) |
| **Ollama Llama3** | 4.7 GB | ⚠️ Optional (for LLM features) |

---

## 🚀 Deployment Strategies

### Strategy 1: System Cache (Default) - Recommended for Development

**How it works:**
- Models download to user's cache directory on first use
- Each user has their own copy
- Standard cross-platform behavior

**Pros:**
- ✅ Zero configuration
- ✅ Works out of the box
- ✅ Per-user isolation
- ✅ Follows platform conventions

**Cons:**
- ❌ Each user downloads separately (~1-6 GB per user)
- ❌ Slower first run

**Setup:**
```bash
# No setup needed - just install dependencies
pip install -r requirements.txt
```

---

### Strategy 2: Portable App Bundle - Recommended for Distribution

**How it works:**
- Package models with your app
- All models in app directory
- Single download for users

**Pros:**
- ✅ One-time download
- ✅ Offline ready
- ✅ Predictable paths
- ✅ Easy to distribute

**Cons:**
- ❌ Large app bundle (~2-6 GB)
- ❌ Requires pre-downloading models

**Setup:**

1. **Use the ModelConfig class:**
```python
# In your Python scripts, add at the top:
from model_config import ModelConfig

# Initialize portable mode
config = ModelConfig(use_app_directory=True)
```

2. **Pre-download models:**
```bash
# Create models directory
mkdir -p models/whisper
mkdir -p models/torch/pyannote
mkdir -p models/sentence_transformers
mkdir -p models/ollama/models

# Download Whisper models
python -c "import whisper; whisper.load_model('medium', download_root='./models/whisper')"

# Download Sentence Transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', cache_folder='./models/sentence_transformers')"

# For Ollama (if using)
export OLLAMA_MODELS=./models/ollama/models
ollama pull llama3
```

3. **Package structure:**
```
TranscriptionApp/
├── app/
│   ├── main.js
│   ├── renderer.js
│   ├── batch_processor.py
│   ├── model_config.py
│   └── ...
├── models/              # Pre-downloaded models
│   ├── whisper/
│   ├── torch/
│   ├── sentence_transformers/
│   └── ollama/
└── node_modules/
```

---

### Strategy 3: Shared System Directory - Recommended for Enterprise

**How it works:**
- Store models in shared location
- All users access same models
- Requires admin setup

**Pros:**
- ✅ Single copy for all users
- ✅ Saves disk space
- ✅ Centralized management

**Cons:**
- ❌ Requires admin privileges
- ❌ Platform-specific paths

**Setup:**

**macOS/Linux:**
```bash
# Create shared directory
sudo mkdir -p /opt/transcription-app/models
sudo chmod 755 /opt/transcription-app/models

# Set environment variables in app
export XDG_CACHE_HOME=/opt/transcription-app/models
export SENTENCE_TRANSFORMERS_HOME=/opt/transcription-app/models/sentence_transformers
export OLLAMA_MODELS=/opt/transcription-app/models/ollama
```

**Windows:**
```powershell
# Create shared directory
New-Item -Path "C:\ProgramData\TranscriptionApp\models" -ItemType Directory

# Set environment variables in app
$env:XDG_CACHE_HOME="C:\ProgramData\TranscriptionApp\models"
$env:SENTENCE_TRANSFORMERS_HOME="C:\ProgramData\TranscriptionApp\models\sentence_transformers"
$env:OLLAMA_MODELS="C:\ProgramData\TranscriptionApp\models\ollama"
```

**In Python:**
```python
from model_config import ModelConfig

# Use custom shared path
if sys.platform == "win32":
    shared_path = "C:\\ProgramData\\TranscriptionApp\\models"
else:
    shared_path = "/opt/transcription-app/models"

config = ModelConfig(custom_path=shared_path)
```

---

## 🔧 Environment Variables Reference

### Whisper
```bash
export XDG_CACHE_HOME=/custom/path  # Models go to /custom/path/whisper/
```

### Pyannote (Speaker Diarization)
```bash
export TORCH_HOME=/custom/path      # Models go to /custom/path/pyannote/
export HUGGINGFACE_TOKEN=hf_xxxxx  # Required for diarization
```

### Sentence Transformers
```bash
export SENTENCE_TRANSFORMERS_HOME=/custom/path
```

### Ollama
```bash
export OLLAMA_MODELS=/custom/path
```

---

## 📋 Integration with Your App

### Update batch_processor.py

Add at the top:
```python
from model_config import ModelConfig

# Initialize model config (choose mode)
# config = ModelConfig()                              # Default system cache
# config = ModelConfig(use_app_directory=True)        # Portable mode
# config = ModelConfig(custom_path="/custom/path")    # Custom path

# For portable distribution:
config = ModelConfig(use_app_directory=True)
```

### Update main.js

Add model info to IPC:
```javascript
ipcMain.handle('get-model-info', async () => {
  const { spawn } = require('child_process');
  const pythonScript = path.join(__dirname, 'model_config.py');
  
  return new Promise((resolve) => {
    const process = spawn('python3', [pythonScript]);
    let output = '';
    
    process.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    process.on('close', () => {
      resolve(JSON.parse(output));
    });
  });
});
```

---

## 🎯 Recommended Setup by Use Case

### For Development/Testing
- **Strategy:** System Cache (Default)
- **Why:** Easy setup, no configuration needed

### For Distribution to End Users
- **Strategy:** Portable App Bundle
- **Why:** Single download, offline ready, predictable

### For Enterprise/Multi-User Systems
- **Strategy:** Shared System Directory
- **Why:** Saves space, centralized management

---

## 📊 Disk Space Requirements

### Minimum (Whisper only)
- Whisper tiny + Pyannote: ~60 MB
- **Use case:** Quick transcription, English only

### Recommended (Full features without LLM)
- Whisper medium + Pyannote + Sentence Transformers: ~900 MB
- **Use case:** Japanese/English, semantic search

### Full (All features with local LLM)
- Whisper medium + Pyannote + Sentence Transformers + Ollama Llama3: ~5.7 GB
- **Use case:** Complete offline functionality

---

## 🔒 Security Considerations

### API Keys
Store API keys securely:

**macOS/Linux:**
```bash
# In ~/.bashrc or ~/.zshrc
export HUGGINGFACE_TOKEN=hf_xxxxx
export OPENAI_API_KEY=sk-xxxxx
export GOOGLE_API_KEY=xxxxx
```

**Windows:**
```powershell
# In PowerShell profile or System Environment Variables
$env:HUGGINGFACE_TOKEN="hf_xxxxx"
$env:OPENAI_API_KEY="sk-xxxxx"
```

**In Electron App:**
Use electron-store or keytar for secure storage.

---

## 🧪 Testing Model Paths

Run the model_config.py script:
```bash
python model_config.py
```

This will show:
- Current platform
- Model storage paths
- Downloaded models
- Total disk usage

---

## 📦 Building Distributable Packages

### macOS (.dmg)
```bash
npm install electron-builder
npm run build:mac
```

### Windows (.exe)
```bash
npm run build:win
```

### Linux (.AppImage)
```bash
npm run build:linux
```

Add to package.json:
```json
{
  "build": {
    "appId": "com.transcription.app",
    "files": [
      "**/*",
      "models/**/*"
    ],
    "extraResources": [
      {
        "from": "models",
        "to": "models"
      }
    ]
  }
}
```

---

## 🆘 Troubleshooting

### Models not found
```bash
# Check environment variables
echo $XDG_CACHE_HOME
echo $SENTENCE_TRANSFORMERS_HOME

# List downloaded models
python -c "from model_config import ModelConfig; print(ModelConfig().list_downloaded_models())"
```

### Disk space issues
```bash
# Check model sizes
python -c "from model_config import ModelConfig; print(ModelConfig().get_total_size())"

# Clear cache
python -c "from model_config import ModelConfig; ModelConfig().clear_cache()"
```

### Permission errors
```bash
# Fix permissions (macOS/Linux)
chmod -R 755 ~/.cache/whisper
chmod -R 755 ~/.cache/torch

# Windows: Run as Administrator
```
