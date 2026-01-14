import os
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

class TranscriptSearchEngine:
    """
    LLM-powered semantic search engine for transcriptions.
    Supports keyword search, semantic search, and cross-language queries.
    """
    
    def __init__(self, llm_processor=None):
        self.llm_processor = llm_processor
        self.transcripts = []
        self.index = {}
        self.embeddings_available = False
        
        # Try to import sentence transformers for embeddings
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.embeddings_available = True
        except ImportError:
            self.embedding_model = None
            print("Warning: sentence-transformers not installed. Semantic search will use LLM fallback.")
    
    def index_transcripts(self, output_folder: str):
        """Index all transcripts in the output folder"""
        self.transcripts = []
        self.index = {}
        
        output_path = Path(output_folder)
        if not output_path.exists():
            return
        
        # Find all transcript files (both .txt and .md)
        transcript_files = list(output_path.glob("*_transcript.txt")) + list(output_path.glob("*_transcript.md"))
        
        # Remove duplicates (if both formats exist, prefer .txt for parsing)
        seen_basenames = set()
        unique_files = []
        for file_path in transcript_files:
            basename = str(file_path).replace('_transcript.txt', '').replace('_transcript.md', '')
            if basename not in seen_basenames:
                seen_basenames.add(basename)
                # Prefer .txt if it exists
                txt_path = Path(str(file_path).replace('_transcript.md', '_transcript.txt'))
                if txt_path.exists():
                    unique_files.append(txt_path)
                else:
                    unique_files.append(file_path)
        
        for file_path in unique_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse transcript
                transcript_data = self._parse_transcript(content, str(file_path))
                self.transcripts.append(transcript_data)
                
                # Create embeddings if available
                if self.embeddings_available:
                    full_text = transcript_data['full_text']
                    embedding = self.embedding_model.encode(full_text)
                    transcript_data['embedding'] = embedding
                
            except Exception as e:
                print(f"Error indexing {file_path}: {str(e)}")
        
        print(f"Indexed {len(self.transcripts)} transcripts")
    
    def _parse_transcript(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse transcript file and extract metadata"""
        lines = content.split('\n')
        
        # Extract language
        language = "unknown"
        for line in lines:
            if line.startswith("Detected Language:"):
                language = line.split(":", 1)[1].strip()
                break
        
        # Extract segments with timestamps and speakers
        segments = []
        in_segments = False
        full_text = ""
        
        for line in lines:
            if line.startswith("[") and "->" in line and "]" in line:
                # Parse segment: [00:00:05 -> 00:00:08] SPEAKER_00: text
                match = re.match(r'\[([\d:]+) -> ([\d:]+)\] ([^:]+): (.+)', line)
                if match:
                    start, end, speaker, text = match.groups()
                    segments.append({
                        'start': start,
                        'end': end,
                        'speaker': speaker,
                        'text': text.strip()
                    })
                    full_text += text.strip() + " "
            elif "FULL TRANSCRIPT:" in line:
                in_segments = False
            elif in_segments and line.strip():
                full_text += line.strip() + " "
        
        # If no segments found, use full transcript
        if not segments and "FULL TRANSCRIPT:" in content:
            full_text = content.split("FULL TRANSCRIPT:")[-1].strip()
        
        return {
            'file_path': file_path,
            'file_name': Path(file_path).stem.replace('_transcript', ''),
            'language': language,
            'segments': segments,
            'full_text': full_text.strip()
        }
    
    def keyword_search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Simple keyword search across all transcripts"""
        results = []
        
        for transcript in self.transcripts:
            matches = []
            text = transcript['full_text']
            
            if not case_sensitive:
                query_lower = query.lower()
                text_lower = text.lower()
                
                if query_lower in text_lower:
                    # Find context around matches
                    for segment in transcript['segments']:
                        if query_lower in segment['text'].lower():
                            matches.append({
                                'timestamp': f"{segment['start']} -> {segment['end']}",
                                'speaker': segment['speaker'],
                                'text': segment['text'],
                                'highlight': self._highlight_text(segment['text'], query, case_sensitive)
                            })
            else:
                if query in text:
                    for segment in transcript['segments']:
                        if query in segment['text']:
                            matches.append({
                                'timestamp': f"{segment['start']} -> {segment['end']}",
                                'speaker': segment['speaker'],
                                'text': segment['text'],
                                'highlight': self._highlight_text(segment['text'], query, case_sensitive)
                            })
            
            if matches:
                results.append({
                    'file_name': transcript['file_name'],
                    'language': transcript['language'],
                    'matches': matches,
                    'match_count': len(matches)
                })
        
        return results
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search using embeddings or LLM"""
        if self.embeddings_available:
            return self._embedding_search(query, top_k)
        elif self.llm_processor and self.llm_processor.provider != "none":
            return self._llm_search(query, top_k)
        else:
            # Fallback to keyword search
            return self.keyword_search(query)
    
    def _embedding_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using sentence embeddings"""
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate similarity scores
        scores = []
        for i, transcript in enumerate(self.transcripts):
            if 'embedding' in transcript:
                similarity = np.dot(query_embedding, transcript['embedding']) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(transcript['embedding'])
                )
                scores.append((i, similarity))
        
        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top results
        results = []
        for idx, score in scores[:top_k]:
            if score > 0.3:  # Threshold
                transcript = self.transcripts[idx]
                
                # Find most relevant segments
                relevant_segments = self._find_relevant_segments(transcript, query)
                
                results.append({
                    'file_name': transcript['file_name'],
                    'language': transcript['language'],
                    'similarity_score': float(score),
                    'matches': relevant_segments,
                    'match_count': len(relevant_segments)
                })
        
        return results
    
    def _llm_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using LLM to understand semantic meaning"""
        results = []
        
        for transcript in self.transcripts:
            prompt = f"""Analyze if this transcript is relevant to the query: "{query}"

Transcript:
{transcript['full_text'][:2000]}...

Is this transcript relevant? If yes, extract the most relevant parts that answer or relate to the query.
Respond in JSON format:
{{"relevant": true/false, "relevance_score": 0-1, "relevant_parts": ["quote1", "quote2"]}}"""
            
            try:
                response = self.llm_processor.process(prompt, "clean", transcript['language'])
                # Parse LLM response and add to results
                # This is a simplified version
                if response and "true" in response.lower():
                    results.append({
                        'file_name': transcript['file_name'],
                        'language': transcript['language'],
                        'llm_analysis': response,
                        'matches': transcript['segments'][:3]  # Top 3 segments
                    })
            except Exception as e:
                print(f"LLM search error: {str(e)}")
                continue
        
        return results[:top_k]
    
    def _find_relevant_segments(self, transcript: Dict, query: str, top_n: int = 3) -> List[Dict]:
        """Find most relevant segments within a transcript"""
        if not self.embeddings_available:
            return transcript['segments'][:top_n]
        
        query_embedding = self.embedding_model.encode(query)
        segment_scores = []
        
        for segment in transcript['segments']:
            segment_embedding = self.embedding_model.encode(segment['text'])
            similarity = np.dot(query_embedding, segment_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(segment_embedding)
            )
            segment_scores.append((segment, similarity))
        
        # Sort by similarity
        segment_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top segments
        return [
            {
                'timestamp': f"{seg['start']} -> {seg['end']}",
                'speaker': seg['speaker'],
                'text': seg['text'],
                'relevance_score': float(score)
            }
            for seg, score in segment_scores[:top_n] if score > 0.3
        ]
    
    def _highlight_text(self, text: str, query: str, case_sensitive: bool) -> str:
        """Highlight query in text"""
        if not case_sensitive:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(query))
        
        return pattern.sub(lambda m: f"**{m.group()}**", text)
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the transcripts using LLM"""
        if not self.llm_processor or self.llm_processor.provider == "none":
            return "LLM is not enabled. Please enable LLM post-processing to use the Q&A feature."
        
        # First, find relevant transcripts
        relevant = self.semantic_search(question, top_k=3)
        
        if not relevant:
            return "I couldn't find any relevant information in the transcripts to answer your question."
        
        # Build context from relevant transcripts
        context = ""
        for result in relevant:
            context += f"\n\nFrom {result['file_name']} ({result['language']}):\n"
            for match in result.get('matches', [])[:3]:
                context += f"- {match.get('text', '')}\n"
        
        # Ask LLM to answer based on context
        prompt = f"""Based on the following transcript excerpts, answer this question: "{question}"

Transcripts:
{context}

Provide a clear, concise answer based only on the information in the transcripts. If the transcripts don't contain enough information to answer, say so."""
        
        try:
            answer = self.llm_processor.process(prompt, "clean", "auto")
            return answer
        except Exception as e:
            return f"Error generating answer: {str(e)}"
