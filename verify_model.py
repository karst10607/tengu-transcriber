#!/usr/bin/env python3
"""
Script to verify if Whisper model is downloaded
"""
import os
import sys
import json
import argparse

def get_whisper_cache_dir():
    """Get the Whisper model cache directory"""
    # Whisper uses torch hub cache by default
    cache_dir = os.path.expanduser("~/.cache/whisper")
    return cache_dir

def check_model_exists(model_name):
    """Check if a specific Whisper model is downloaded"""
    cache_dir = get_whisper_cache_dir()
    
    if not os.path.exists(cache_dir):
        return {
            "exists": False,
            "path": None,
            "size": None,
            "message": f"Whisper cache directory not found: {cache_dir}"
        }
    
    # Whisper model filenames - check multiple possible names
    # Models can be named: large.pt, large-v2.pt, large-v3.pt, etc.
    possible_names = [
        f"{model_name}.pt",
        f"{model_name}-v1.pt",
        f"{model_name}-v2.pt",
        f"{model_name}-v3.pt",
        f"{model_name}.en.pt",
    ]
    
    # First check exact matches
    for possible_name in possible_names:
        model_path = os.path.join(cache_dir, possible_name)
        if os.path.exists(model_path):
            size_bytes = os.path.getsize(model_path)
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                "exists": True,
                "path": model_path,
                "cache_dir": cache_dir,
                "size": f"{size_mb:.1f} MB",
                "size_bytes": size_bytes,
                "message": f"Model '{model_name}' is downloaded"
            }
    
    # Search for any file starting with model name
    for file in os.listdir(cache_dir):
        if file.startswith(model_name) and file.endswith('.pt'):
            model_path = os.path.join(cache_dir, file)
            size_bytes = os.path.getsize(model_path)
            size_mb = size_bytes / (1024 * 1024)
            
            return {
                "exists": True,
                "path": model_path,
                "cache_dir": cache_dir,
                "size": f"{size_mb:.1f} MB",
                "size_bytes": size_bytes,
                "message": f"Model '{model_name}' is downloaded ({file})"
            }
    
    return {
        "exists": False,
        "path": os.path.join(cache_dir, f"{model_name}.pt"),
        "cache_dir": cache_dir,
        "size": None,
        "message": f"Model '{model_name}' is not downloaded yet. Click 'Download Model' to download it."
    }

def main():
    parser = argparse.ArgumentParser(description='Verify Whisper model status')
    parser.add_argument('--model', required=True, help='Model name (tiny, base, small, medium, large)')
    
    args = parser.parse_args()
    
    result = check_model_exists(args.model)
    
    # Output as JSON for easy parsing
    print(json.dumps(result))
    
    # Exit code: 0 if exists, 1 if not
    sys.exit(0 if result["exists"] else 1)

if __name__ == "__main__":
    main()
