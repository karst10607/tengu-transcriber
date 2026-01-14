import os
import sys
from pathlib import Path

class ModelConfig:
    """
    Cross-platform model storage configuration.
    Handles model paths for Whisper, Pyannote, Sentence Transformers, and Ollama.
    """
    
    def __init__(self, use_app_directory=False, custom_path=None):
        """
        Initialize model configuration.
        
        Args:
            use_app_directory: If True, store models in app directory (portable mode)
            custom_path: Custom path for model storage (overrides all defaults)
        """
        self.platform = sys.platform
        self.use_app_directory = use_app_directory
        self.custom_path = custom_path
        
        if custom_path:
            self.base_path = Path(custom_path)
        elif use_app_directory:
            # Store models in app directory (portable)
            self.base_path = Path(__file__).parent / "models"
        else:
            # Use system default cache directories
            self.base_path = self._get_default_cache_path()
        
        self._setup_environment()
    
    def _get_default_cache_path(self):
        """Get default cache path based on platform"""
        if self.platform == "win32":
            # Windows: C:\Users\<username>\.cache
            return Path.home() / ".cache"
        else:
            # macOS/Linux: ~/.cache
            return Path.home() / ".cache"
    
    def _setup_environment(self):
        """Set up environment variables for model storage"""
        # Create directories if they don't exist
        self.whisper_path = self.base_path / "whisper"
        self.pyannote_path = self.base_path / "torch" / "pyannote"
        self.sentence_transformers_path = self.base_path / "sentence_transformers"
        self.ollama_path = self.base_path / "ollama" / "models"
        
        # Create directories
        for path in [self.whisper_path, self.pyannote_path, 
                     self.sentence_transformers_path, self.ollama_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Set environment variables
        if self.use_app_directory or self.custom_path:
            os.environ['XDG_CACHE_HOME'] = str(self.base_path)
            os.environ['TORCH_HOME'] = str(self.base_path / "torch")
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(self.sentence_transformers_path)
            os.environ['OLLAMA_MODELS'] = str(self.ollama_path)
    
    def get_model_info(self):
        """Get information about model storage locations"""
        return {
            'platform': self.platform,
            'base_path': str(self.base_path),
            'whisper': str(self.whisper_path),
            'pyannote': str(self.pyannote_path),
            'sentence_transformers': str(self.sentence_transformers_path),
            'ollama': str(self.ollama_path),
            'mode': 'portable' if self.use_app_directory else 'system_cache'
        }
    
    def get_total_size(self):
        """Calculate total size of downloaded models"""
        total_size = 0
        
        for path in [self.whisper_path, self.pyannote_path, 
                     self.sentence_transformers_path, self.ollama_path]:
            if path.exists():
                for file in path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
        
        return self._format_size(total_size)
    
    def _format_size(self, size_bytes):
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def list_downloaded_models(self):
        """List all downloaded models"""
        models = {
            'whisper': [],
            'pyannote': [],
            'sentence_transformers': [],
            'ollama': []
        }
        
        # Check Whisper models
        if self.whisper_path.exists():
            models['whisper'] = [f.name for f in self.whisper_path.iterdir() if f.is_file()]
        
        # Check Pyannote models
        if self.pyannote_path.exists():
            models['pyannote'] = [f.name for f in self.pyannote_path.rglob('*.bin')]
        
        # Check Sentence Transformers
        if self.sentence_transformers_path.exists():
            models['sentence_transformers'] = [d.name for d in self.sentence_transformers_path.iterdir() if d.is_dir()]
        
        # Check Ollama models
        if self.ollama_path.exists():
            models['ollama'] = [d.name for d in self.ollama_path.iterdir() if d.is_dir()]
        
        return models
    
    def clear_cache(self, model_type=None):
        """
        Clear cached models.
        
        Args:
            model_type: Specific model type to clear ('whisper', 'pyannote', 'sentence_transformers', 'ollama')
                       If None, clears all models
        """
        import shutil
        
        paths_to_clear = {
            'whisper': self.whisper_path,
            'pyannote': self.pyannote_path,
            'sentence_transformers': self.sentence_transformers_path,
            'ollama': self.ollama_path
        }
        
        if model_type:
            if model_type in paths_to_clear:
                path = paths_to_clear[model_type]
                if path.exists():
                    shutil.rmtree(path)
                    path.mkdir(parents=True, exist_ok=True)
                    return f"Cleared {model_type} cache"
            return f"Unknown model type: {model_type}"
        else:
            # Clear all
            for name, path in paths_to_clear.items():
                if path.exists():
                    shutil.rmtree(path)
                    path.mkdir(parents=True, exist_ok=True)
            return "Cleared all model caches"


# Usage examples:
if __name__ == "__main__":
    # Default mode (uses system cache)
    config = ModelConfig()
    print("System Cache Mode:")
    print(config.get_model_info())
    print(f"Total size: {config.get_total_size()}")
    print(f"Downloaded models: {config.list_downloaded_models()}")
    
    print("\n" + "="*60 + "\n")
    
    # Portable mode (stores in app directory)
    config_portable = ModelConfig(use_app_directory=True)
    print("Portable Mode:")
    print(config_portable.get_model_info())
    
    print("\n" + "="*60 + "\n")
    
    # Custom path mode
    config_custom = ModelConfig(custom_path="/custom/models/path")
    print("Custom Path Mode:")
    print(config_custom.get_model_info())
