from datetime import datetime
from typing import List, Dict

class TranscriptFormatter:
    """Format transcripts in different output formats (txt, md)"""
    
    @staticmethod
    def format_txt(video_filename: str, language: str, duration: str, segments: List[Dict], full_text: str) -> str:
        """Format transcript as plain text"""
        output = []
        output.append(f"Detected Language: {language}")
        output.append(f"Total Duration: {duration}")
        output.append("")
        output.append("TRANSCRIPT WITH SPEAKERS:")
        output.append("=" * 80)
        output.append("")
        
        for segment in segments:
            output.append(f"[{segment['start']} -> {segment['end']}] {segment['speaker']}: {segment['text']}")
        
        output.append("")
        output.append("=" * 80)
        output.append("FULL TRANSCRIPT:")
        output.append("=" * 80)
        output.append("")
        output.append(full_text)
        
        return "\n".join(output)
    
    @staticmethod
    def format_md(video_filename: str, language: str, duration: str, segments: List[Dict], full_text: str) -> str:
        """Format transcript as Markdown"""
        output = []
        
        # Header
        output.append(f"# Transcript: {video_filename}")
        output.append("")
        output.append(f"**Language:** {language}  ")
        output.append(f"**Duration:** {duration}  ")
        output.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append("---")
        output.append("")
        
        # Transcript with speakers
        output.append("## Transcript with Speakers")
        output.append("")
        
        for segment in segments:
            output.append(f"### {segment['start']} → {segment['end']}")
            output.append(f"**{segment['speaker']}:** {segment['text']}")
            output.append("")
        
        output.append("---")
        output.append("")
        
        # Full transcript
        output.append("## Full Transcript")
        output.append("")
        output.append(full_text)
        
        return "\n".join(output)
    
    @staticmethod
    def format_enhanced_txt(video_filename: str, provider: str, template: str, enhanced_text: str) -> str:
        """Format LLM-enhanced transcript as plain text"""
        output = []
        output.append(f"LLM Provider: {provider}")
        output.append(f"Template: {template}")
        output.append("=" * 80)
        output.append("")
        output.append(enhanced_text)
        
        return "\n".join(output)
    
    @staticmethod
    def format_enhanced_md(video_filename: str, provider: str, template: str, enhanced_text: str) -> str:
        """Format LLM-enhanced transcript as Markdown"""
        output = []
        
        # Header
        output.append(f"# Enhanced Transcript: {video_filename}")
        output.append("")
        output.append(f"**LLM Provider:** {provider}  ")
        output.append(f"**Template:** {template}  ")
        output.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append("---")
        output.append("")
        
        # Enhanced content
        output.append(enhanced_text)
        
        return "\n".join(output)
