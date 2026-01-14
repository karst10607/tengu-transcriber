import os
import sys
import whisper
import torch
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pyannote.audio import Pipeline
import warnings
warnings.filterwarnings("ignore")

def convert_video_to_mp3(video_path, output_mp3):
    """Convert video file to MP3"""
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_mp3, verbose=False, logger=None)
        video.close()
        print(f"Successfully converted to MP3: {output_mp3}")
        return True
    except Exception as e:
        print(f"Error converting video to MP3: {str(e)}")
        return False

def transcribe_audio(audio_path):
    """Transcribe audio file using Whisper with speaker diarization"""
    wav_path = None
    
    try:
        if audio_path.lower().endswith('.mp3'):
            sound = AudioSegment.from_mp3(audio_path)
            wav_path = audio_path.rsplit('.', 1)[0] + '_temp.wav'
            sound.export(wav_path, format="wav")
            audio_file_path = wav_path
        else:
            audio_file_path = audio_path
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model on {device}...")
        model = whisper.load_model("medium", device=device)
        
        print("Transcribing audio...")
        result = model.transcribe(
            audio_file_path,
            language=None,
            task="transcribe",
            verbose=True
        )
        
        print("\nLoading speaker diarization...")
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=os.environ.get("HUGGINGFACE_TOKEN")
            )
            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
            diarization = pipeline(audio_file_path)
        except Exception as e:
            print(f"Speaker diarization not available: {str(e)}")
            diarization = None
        
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        
        return result, diarization
        
    except Exception as e:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
        print(f"Error during transcription: {str(e)}")
        return None, None

def format_timestamp(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python video_to_transcript.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: File '{video_path}' not found")
        sys.exit(1)
    
    # Create output filenames
    base_name = os.path.splitext(video_path)[0]
    mp3_path = f"{base_name}.mp3"
    txt_path = f"{base_name}_transcript.txt"
    
    # Step 1: Convert video to MP3
    print("Converting video to MP3...")
    if not convert_video_to_mp3(video_path, mp3_path):
        sys.exit(1)
    
    # Step 2: Transcribe audio to text
    print("\nTranscribing audio...")
    result, diarization = transcribe_audio(mp3_path)
    
    if result:
        segments = result["segments"]
        detected_language = result.get("language", "unknown")
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Detected Language: {detected_language}\n")
            f.write("=" * 80 + "\n\n")
            
            for segment in segments:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"].strip()
                
                speaker = "Unknown"
                if diarization:
                    segment_midpoint = (start_time + end_time) / 2
                    for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                        if turn.start <= segment_midpoint <= turn.end:
                            speaker = speaker_label
                            break
                
                timestamp = f"[{format_timestamp(start_time)} -> {format_timestamp(end_time)}]"
                f.write(f"{timestamp} {speaker}: {text}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("FULL TRANSCRIPT:\n")
            f.write("=" * 80 + "\n")
            f.write(result["text"])
        
        print(f"\nTranscription complete!")
        print(f"Detected language: {detected_language}")
        print(f"MP3 saved as: {mp3_path}")
        print(f"Transcript saved as: {txt_path}")
        print("\nTranscript preview:")
        print("-" * 80)
        preview = result["text"][:500] if len(result["text"]) > 500 else result["text"]
        print(preview)
        if len(result["text"]) > 500:
            print("...")
        print("-" * 80)
    else:
        print("Failed to transcribe audio")

if __name__ == "__main__":
    main()
