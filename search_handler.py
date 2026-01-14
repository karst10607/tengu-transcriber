import sys
import json
import argparse
from search_engine import TranscriptSearchEngine
from llm_processor import LLMProcessor

def main():
    parser = argparse.ArgumentParser(description='Search transcripts')
    parser.add_argument('--action', required=True, help='Action: index, keyword, semantic, or ask')
    parser.add_argument('--output-folder', required=True, help='Folder containing transcripts')
    parser.add_argument('--query', help='Search query or question')
    parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    parser.add_argument('--llm-config', help='LLM configuration JSON')
    
    args = parser.parse_args()
    
    # Initialize LLM processor if configured
    llm_processor = None
    if args.llm_config:
        try:
            llm_config = json.loads(args.llm_config)
            if llm_config.get('enabled'):
                llm_processor = LLMProcessor(
                    provider=llm_config.get('provider', 'none'),
                    api_key=llm_config.get('apiKey'),
                    model=llm_config.get('model')
                )
                llm_processor.template = llm_config.get('template', 'clean')
        except Exception as e:
            print(f"Warning: Failed to initialize LLM: {str(e)}", file=sys.stderr)
    
    # Initialize search engine
    search_engine = TranscriptSearchEngine(llm_processor)
    
    # Index transcripts
    search_engine.index_transcripts(args.output_folder)
    
    if args.action == 'index':
        print(json.dumps({'success': True, 'count': len(search_engine.transcripts)}))
        return
    
    if not args.query:
        print(json.dumps({'error': 'Query required'}), file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.action == 'keyword':
            results = search_engine.keyword_search(args.query, args.case_sensitive)
            print(json.dumps({'success': True, 'results': results}))
            
        elif args.action == 'semantic':
            results = search_engine.semantic_search(args.query, top_k=5)
            print(json.dumps({'success': True, 'results': results}))
            
        elif args.action == 'ask':
            answer = search_engine.ask_question(args.query)
            print(json.dumps({'success': True, 'answer': answer}))
            
        else:
            print(json.dumps({'error': f'Unknown action: {args.action}'}), file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
