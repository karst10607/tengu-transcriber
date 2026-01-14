import os
import sys
import json
import argparse
import whisper
import torch
import subprocess
import time
from moviepy import VideoFileClip
from pyannote.audio import Pipeline
from pyannote.core import Segment
from llm_processor import LLMProcessor
from transcript_formatter import TranscriptFormatter
import warnings
warnings.filterwarnings("ignore")

def get_file_size(file_path):
    """Get human-readable file size"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def convert_video_to_mp3(video_path, output_folder, bitrate='128k'):
    """Convert video file to MP3"""
    try:
        start_time = time.time()
        video_size = get_file_size(video_path)
        print(f"  📹 Input video size: {video_size}")
        
        video = VideoFileClip(video_path)
        duration = video.duration
        print(f"  ⏱️  Video duration: {int(duration // 60)}m {int(duration % 60)}s")
        
        filename = os.path.splitext(os.path.basename(video_path))[0]
        mp3_path = os.path.join(output_folder, f"{filename}.mp3")
        
        print(f"  🔄 Converting video to MP3 (bitrate: {bitrate})...")
        # moviepy 2.x doesn't support verbose/logger parameters
        video.audio.write_audiofile(mp3_path, bitrate=bitrate)
        video.close()
        
        elapsed = time.time() - start_time
        mp3_size = get_file_size(mp3_path)
        print(f"  ✓ MP3 conversion complete: {os.path.basename(mp3_path)}")
        print(f"  📦 MP3 size: {mp3_size}")
        print(f"  ⏱️  Time taken: {elapsed:.1f}s")
        return mp3_path
    except Exception as e:
        raise Exception(f"Error converting video to MP3: {str(e)}")

def load_whisper_model(model_size="medium"):
    """Load Whisper model with GPU acceleration if available"""
    model_sizes = {
        'tiny': '39 MB',
        'base': '74 MB',
        'small': '244 MB',
        'medium': '769 MB',
        'large': '2.9 GB'
    }
    
    print(f"  Loading Whisper '{model_size}' model ({model_sizes.get(model_size, 'unknown size')})...")
    sys.stdout.flush()
    
    # Check for available acceleration: CUDA (NVIDIA), MPS (Apple Silicon), or CPU
    if torch.cuda.is_available():
        device = "cuda"
        device_name = "NVIDIA GPU (CUDA)"
    elif torch.backends.mps.is_available():
        # MPS available but may have compatibility issues with some operations
        device = "mps"
        device_name = "Apple Silicon GPU (Metal)"
    else:
        device = "cpu"
        device_name = "CPU"
    
    print(f"  🖥️  Attempting to load on: {device_name}")
    sys.stdout.flush()
    
    # Try loading on preferred device, fall back to CPU if it fails
    try:
        model = whisper.load_model(model_size, device=device)
        print(f"  ✓ Model loaded successfully on {device.upper()}")
        sys.stdout.flush()
        return model
    except Exception as e:
        if device != "cpu":
            print(f"  ⚠️  {device.upper()} loading failed: {str(e)[:100]}...")
            print(f"  🔄 Falling back to CPU...")
            sys.stdout.flush()
            model = whisper.load_model(model_size, device="cpu")
            print(f"  ✓ Model loaded successfully on CPU")
            sys.stdout.flush()
            return model
        else:
            raise

def load_diarization_pipeline():
    """Load speaker diarization pipeline"""
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=os.environ.get("HUGGINGFACE_TOKEN")
        )
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
        return pipeline
    except Exception as e:
        print(f"  ⚠ Speaker diarization not available: {str(e)}")
        print(f"  Continuing without speaker identification...")
        return None

def transcribe_audio_with_whisper(audio_path, output_folder, whisper_model, diarization_pipeline, output_format='txt'):
    """Transcribe audio using Whisper with speaker diarization"""
    wav_path = None
    
    try:
        if audio_path.lower().endswith('.mp3'):
            start_time = time.time()
            wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
            print(f"  🔄 Converting MP3 to WAV for Whisper (16kHz mono)...")
            # Use ffmpeg directly to convert MP3 to WAV
            subprocess.run([
                'ffmpeg', '-i', audio_path, 
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',       # Mono
                '-y',             # Overwrite output
                wav_path
            ], check=True, capture_output=True)
            elapsed = time.time() - start_time
            wav_size = get_file_size(wav_path)
            print(f"  ✓ WAV conversion complete: {wav_size}")
            print(f"  ⏱️  Time taken: {elapsed:.1f}s")
            audio_file_path = wav_path
        else:
            audio_file_path = audio_path
        
        print(f"  🎤 Starting Whisper transcription...")
        start_time = time.time()
        result = whisper_model.transcribe(
            audio_file_path,
            language=None,
            task="transcribe",
            verbose=True
        )
        elapsed = time.time() - start_time
        print(f"  ✓ Transcription complete")
        print(f"  ⏱️  Time taken: {elapsed:.1f}s")
        
        language = result.get('language', 'unknown')
        full_text = result['text']
        
        segments_with_speakers = []
        
        if diarization_pipeline:
            try:
                print(f"  👥 Running speaker diarization...")
                start_time = time.time()
                diarization = diarization_pipeline(audio_file_path)
                elapsed = time.time() - start_time
                print(f"  ✓ Diarization complete")
                print(f"  ⏱️  Time taken: {elapsed:.1f}s")
                
                for segment, _, speaker in diarization.itertracks(yield_label=True):
                    segment_start = segment.start
                    segment_end = segment.end
                    
                    segment_text = ""
                    for whisper_segment in result['segments']:
                        whisper_start = whisper_segment['start']
                        whisper_end = whisper_segment['end']
                        
                        if whisper_start >= segment_start and whisper_end <= segment_end:
                            segment_text += whisper_segment['text'] + " "
                    
                    if segment_text.strip():
                        segments_with_speakers.append({
                            'start': format_timestamp(segment_start),
                            'end': format_timestamp(segment_end),
                            'speaker': speaker,
                            'text': segment_text.strip()
                        })
            except Exception as e:
                print(f"Warning: Speaker diarization failed: {str(e)}")
                for segment in result['segments']:
                    segments_with_speakers.append({
                        'start': format_timestamp(segment['start']),
                        'end': format_timestamp(segment['end']),
                        'speaker': 'SPEAKER_00',
                        'text': segment['text'].strip()
                    })
        else:
            for segment in result['segments']:
                segments_with_speakers.append({
                    'start': format_timestamp(segment['start']),
                    'end': format_timestamp(segment['end']),
                    'speaker': 'SPEAKER_00',
                    'text': segment['text'].strip()
                })
        
        filename = os.path.splitext(os.path.basename(audio_path))[0]
        if filename.endswith('_temp'):
            filename = filename[:-5]
        
        video_filename = os.path.basename(audio_path).replace('.mp3', '')
        duration = format_timestamp(result['segments'][-1]['end']) if result.get('segments') else "00:00:00"
        
        transcript_paths = []
        
        # Save in requested format(s)
        if output_format in ['txt', 'both']:
            transcript_path_txt = os.path.join(output_folder, f"{filename}_transcript.txt")
            txt_content = TranscriptFormatter.format_txt(
                video_filename, language, duration, segments_with_speakers, full_text
            )
            with open(transcript_path_txt, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            transcript_paths.append(transcript_path_txt)
        
        if output_format in ['md', 'both']:
            transcript_path_md = os.path.join(output_folder, f"{filename}_transcript.md")
            md_content = TranscriptFormatter.format_md(
                video_filename, language, duration, segments_with_speakers, full_text
            )
            with open(transcript_path_md, 'w', encoding='utf-8') as f:
                f.write(md_content)
            transcript_paths.append(transcript_path_md)
        
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        
        preview = full_text[:100] if len(full_text) > 100 else full_text
        return transcript_paths[0], preview, language
        
    except Exception as e:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        raise Exception(f"Error transcribing {audio_path}: {str(e)}")

def format_timestamp(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def process_video(video_path, output_folder, index, total, whisper_model, diarization_pipeline, llm_processor=None, output_format='txt', mp3_bitrate='128k'):
    """Process a single video file"""
    print(f"\n{'='*60}")
    print(f"PROGRESS: {index}/{total}")
    print(f"📹 Processing {index}/{total}: {os.path.basename(video_path)}")
    print(f"{'='*60}")
    
    overall_start = time.time()
    
    try:
        print(f"\n[STEP 1/3] VIDEO → MP3 CONVERSION")
        mp3_path = convert_video_to_mp3(video_path, output_folder, mp3_bitrate)
        
        print(f"\n[STEP 2/3] AUDIO TRANSCRIPTION")
        transcript_path, preview, language = transcribe_audio_with_whisper(
            mp3_path, output_folder, whisper_model, diarization_pipeline, output_format
        )
        
        transcript_size = get_file_size(transcript_path)
        print(f"  ✓ Transcript saved: {os.path.basename(transcript_path)}")
        print(f"  📦 Transcript size: {transcript_size}")
        print(f"  🌐 Detected language: {language}")
        print(f"  📝 Preview: {preview[:100]}...")
        
        if llm_processor and llm_processor.provider != "none":
            print(f"\n[STEP 3/3] LLM ENHANCEMENT")
            print(f"  🤖 Processing with LLM ({llm_processor.provider})...")
            start_time = time.time()
            
            with open(transcript_path, 'r', encoding='utf-8') as f:
                raw_transcript = f.read()
            
            enhanced_text = llm_processor.process(raw_transcript, llm_processor.template, language)
            elapsed = time.time() - start_time
            print(f"  ⏱️  LLM processing time: {elapsed:.1f}s")
            
            if enhanced_text:
                filename = os.path.splitext(os.path.basename(video_path))[0]
                video_filename = os.path.basename(video_path)
                
                # Save in requested format(s)
                if output_format in ['txt', 'both']:
                    enhanced_path_txt = os.path.join(output_folder, f"{filename}_enhanced.txt")
                    txt_content = TranscriptFormatter.format_enhanced_txt(
                        video_filename, llm_processor.provider, llm_processor.template, enhanced_text
                    )
                    with open(enhanced_path_txt, 'w', encoding='utf-8') as f:
                        f.write(txt_content)
                    enhanced_size = get_file_size(enhanced_path_txt)
                    print(f"  ✓ Enhanced transcript saved: {os.path.basename(enhanced_path_txt)}")
                    print(f"  📦 Enhanced size: {enhanced_size}")
                
                if output_format in ['md', 'both']:
                    enhanced_path_md = os.path.join(output_folder, f"{filename}_enhanced.md")
                    md_content = TranscriptFormatter.format_enhanced_md(
                        video_filename, llm_processor.provider, llm_processor.template, enhanced_text
                    )
                    with open(enhanced_path_md, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                    enhanced_size = get_file_size(enhanced_path_md)
                    print(f"  ✓ Enhanced transcript saved: {os.path.basename(enhanced_path_md)}")
                    print(f"  📦 Enhanced size: {enhanced_size}")
            else:
                print(f"  ⚠ LLM processing failed or returned empty")
        
        overall_elapsed = time.time() - overall_start
        print(f"\n{'='*60}")
        print(f"✅ COMPLETED: {os.path.basename(video_path)}")
        print(f"⏱️  Total time: {int(overall_elapsed // 60)}m {int(overall_elapsed % 60)}s")
        print(f"{'='*60}\n")
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}", file=sys.stderr)
        return False

def main():
    # Ensure output is not buffered
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("="*60)
    print("BATCH VIDEO PROCESSOR STARTED")
    print("="*60)
    sys.stdout.flush()
    
    parser = argparse.ArgumentParser(description='Batch process videos to MP3 and transcriptions')
    parser.add_argument('--videos', required=True, help='JSON array of video file paths')
    parser.add_argument('--output', required=True, help='Output folder path')
    parser.add_argument('--model', default='medium', help='Whisper model size (tiny, base, small, medium, large)')
    parser.add_argument('--llm-config', default=None, help='LLM configuration JSON')
    parser.add_argument('--format', default='txt', choices=['txt', 'md', 'both'], help='Output format for transcripts')
    parser.add_argument('--mp3-bitrate', default='128k', help='MP3 audio bitrate (64k, 96k, 128k, 192k, 320k)')
    
    args = parser.parse_args()
    
    try:
        video_files = json.loads(args.videos)
    except json.JSONDecodeError:
        print("Error: Invalid video files JSON", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)
    
    output_folder = args.output
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    total = len(video_files)
    successful = 0
    failed = 0
    
    model_name = args.model
    
    print(f"Starting batch processing of {total} video(s)...")
    print(f"Output folder: {output_folder}")
    print(f"Whisper model: {model_name}")
    print("-" * 60)
    sys.stdout.flush()
    
    print("Initializing Whisper model...")
    sys.stdout.flush()
    whisper_model = load_whisper_model(model_name)
    sys.stdout.flush()
    
    print("Initializing speaker diarization...")
    sys.stdout.flush()
    diarization_pipeline = load_diarization_pipeline()
    if diarization_pipeline:
        print("✓ Speaker diarization loaded")
        sys.stdout.flush()
    
    llm_processor = None
    if args.llm_config:
        try:
            llm_config = json.loads(args.llm_config)
            if llm_config.get('enabled'):
                print(f"Initializing LLM post-processor ({llm_config.get('provider')})...")
                sys.stdout.flush()
                llm_processor = LLMProcessor(
                    provider=llm_config.get('provider', 'none'),
                    api_key=llm_config.get('apiKey'),
                    model=llm_config.get('model')
                )
                llm_processor.template = llm_config.get('template', 'clean')
                if llm_processor.provider != "none":
                    print(f"✓ LLM processor loaded: {llm_config.get('template')} template")
                    sys.stdout.flush()
        except Exception as e:
            print(f"Warning: Failed to initialize LLM processor: {str(e)}")
            sys.stdout.flush()
    
    print("-" * 60)
    sys.stdout.flush()
    
    for index, video_path in enumerate(video_files, 1):
        if not os.path.exists(video_path):
            print(f"Skipping {index}/{total}: File not found - {video_path}", file=sys.stderr)
            failed += 1
            continue
        
        if process_video(video_path, output_folder, index, total, whisper_model, diarization_pipeline, llm_processor, args.format, args.mp3_bitrate):
            successful += 1
        else:
            failed += 1
        
        print("-" * 60)
    
    print(f"\nProcessing complete!")
    print(f"Successful: {successful}/{total}")
    print(f"Failed: {failed}/{total}")
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
