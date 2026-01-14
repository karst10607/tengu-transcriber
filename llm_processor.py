import os
import sys
from typing import Optional, Dict, Any
import json

class LLMProcessor:
    """
    Flexible LLM post-processor supporting multiple providers:
    - Local: Ollama (Llama 3, Mistral, etc.)
    - Cloud: OpenAI (GPT-4), Google (Gemini), Anthropic (Claude)
    """
    
    def __init__(self, provider: str = "none", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if self.provider != "none":
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                self.model = self.model or "gpt-4-turbo-preview"
                
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model or 'gemini-pro')
                
            elif self.provider == "claude":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = self.model or "claude-3-sonnet-20240229"
                
            elif self.provider == "ollama":
                import ollama
                self.client = ollama
                self.model = self.model or "llama3"
                
        except ImportError as e:
            print(f"Warning: {self.provider} library not installed. Install with: pip install {self.provider}")
            self.provider = "none"
        except Exception as e:
            print(f"Warning: Failed to initialize {self.provider}: {str(e)}")
            self.provider = "none"
    
    def process(self, transcript: str, template: str, language: str = "auto") -> Optional[str]:
        """Process transcript using selected LLM and template"""
        if self.provider == "none":
            return None
        
        prompt = self._build_prompt(transcript, template, language)
        
        try:
            if self.provider == "openai":
                return self._process_openai(prompt)
            elif self.provider == "gemini":
                return self._process_gemini(prompt)
            elif self.provider == "claude":
                return self._process_claude(prompt)
            elif self.provider == "ollama":
                return self._process_ollama(prompt)
        except Exception as e:
            print(f"Error processing with {self.provider}: {str(e)}")
            return None
    
    def _build_prompt(self, transcript: str, template: str, language: str) -> str:
        """Build prompt based on template"""
        templates = {
            "clean": f"""Clean up and correct this transcript. Fix grammar, punctuation, and formatting errors while preserving the original meaning and language.

Transcript:
{transcript}

Provide only the cleaned transcript without any additional commentary.""",

            "summary": f"""Create a concise summary of this transcript. Include:
- Main topics discussed
- Key points and decisions
- Action items (if any)

Transcript:
{transcript}

Provide a well-structured summary.""",

            "translate_en": f"""Translate this transcript to English. Maintain the original meaning and context.

Transcript:
{transcript}

Provide only the English translation.""",

            "translate_ja": f"""Translate this transcript to Japanese. Maintain the original meaning and context.

Transcript:
{transcript}

Provide only the Japanese translation.""",

            "detailed": f"""Analyze this transcript and provide:
1. Cleaned and corrected version
2. Summary of main points
3. Key insights or takeaways
4. Identified speakers and their roles (if discernible)

Transcript:
{transcript}

Provide a comprehensive analysis.""",

            "meeting_notes": f"""Convert this transcript into professional meeting notes with:
- Date/Time (if mentioned)
- Attendees (if identifiable)
- Agenda items discussed
- Decisions made
- Action items with owners
- Next steps

Transcript:
{transcript}

Format as professional meeting minutes."""
        }
        
        return templates.get(template, templates["clean"])
    
    def _process_openai(self, prompt: str) -> str:
        """Process using OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional transcript editor and analyzer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    def _process_gemini(self, prompt: str) -> str:
        """Process using Google Gemini API"""
        response = self.client.generate_content(prompt)
        return response.text
    
    def _process_claude(self, prompt: str) -> str:
        """Process using Anthropic Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _process_ollama(self, prompt: str) -> str:
        """Process using local Ollama"""
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional transcript editor and analyzer."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content']


def get_available_providers() -> Dict[str, Any]:
    """Check which LLM providers are available"""
    providers = {
        "none": {"available": True, "name": "None (Whisper only)"},
        "ollama": {"available": False, "name": "Ollama (Local - Free)"},
        "openai": {"available": False, "name": "OpenAI (GPT-4)"},
        "gemini": {"available": False, "name": "Google Gemini Pro"},
        "claude": {"available": False, "name": "Anthropic Claude"}
    }
    
    try:
        import ollama
        providers["ollama"]["available"] = True
    except ImportError:
        pass
    
    try:
        import openai
        providers["openai"]["available"] = True
    except ImportError:
        pass
    
    try:
        import google.generativeai
        providers["gemini"]["available"] = True
    except ImportError:
        pass
    
    try:
        import anthropic
        providers["claude"]["available"] = True
    except ImportError:
        pass
    
    return providers


def get_templates() -> Dict[str, str]:
    """Get available processing templates"""
    return {
        "clean": "Clean & Correct - Fix grammar and formatting",
        "summary": "Summary - Create concise summary",
        "translate_en": "Translate to English",
        "translate_ja": "Translate to Japanese",
        "detailed": "Detailed Analysis - Full breakdown",
        "meeting_notes": "Meeting Notes - Professional format"
    }
