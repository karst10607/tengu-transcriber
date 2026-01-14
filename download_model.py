#!/usr/bin/env python3
"""
Script to download Whisper models with progress reporting
"""
import os
import sys
import json
import argparse
import whisper

def get_whisper_cache_dir():
    """Get the Whisper model cache directory"""
    cache_dir = os.path.expanduser("~/.cache/whisper")
    return cache_dir

def download_model(model_name):
    """Download a Whisper model with progress reporting"""
    try:
        cache_dir = get_whisper_cache_dir()
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"Starting download of Whisper model: {model_name}")
        print(f"Download location: {cache_dir}")
        print(f"This may take a few minutes depending on your internet connection...")
        print("")
        
        # Download the model (this will show progress in stdout)
        model = whisper.load_model(model_name, download_root=cache_dir)
        
        # Whisper models can be stored with different names, search for them
        possible_names = [
            f"{model_name}.pt",
            f"{model_name}.en.pt",
        ]
        
        model_path = None
        for possible_name in possible_names:
            test_path = os.path.join(cache_dir, possible_name)
            if os.path.exists(test_path):
                model_path = test_path
                break
        
        # If not found in expected locations, search the cache directory
        if not model_path and os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                if file.startswith(model_name) and file.endswith('.pt'):
                    model_path = os.path.join(cache_dir, file)
                    break
        
        if model_path and os.path.exists(model_path):
            size_bytes = os.path.getsize(model_path)
            size_mb = size_bytes / (1024 * 1024)
            
            result = {
                "success": True,
                "model": model_name,
                "path": model_path,
                "size": f"{size_mb:.1f} MB",
                "size_bytes": size_bytes,
                "message": f"Successfully downloaded {model_name} model"
            }
        else:
            # List what's actually in the cache directory for debugging
            files_in_cache = []
            if os.path.exists(cache_dir):
                files_in_cache = os.listdir(cache_dir)
            
            result = {
                "success": False,
                "model": model_name,
                "message": f"Model download completed but file not found. Cache dir contents: {files_in_cache}"
            }
        
        print("")
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        error_result = {
            "success": False,
            "model": model_name,
            "error": str(e),
            "message": f"Failed to download model: {str(e)}"
        }
        print(json.dumps(error_result), file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(description='Download Whisper model')
    parser.add_argument('--model', required=True, help='Model name (tiny, base, small, medium, large)')
    
    args = parser.parse_args()
    
    sys.exit(download_model(args.model))

if __name__ == "__main__":
    main()
