import os
import sys
sys.path.append('..')

from dotenv import load_dotenv
import deepl
from arxiv_scraper import ArxivScraper

load_dotenv()

class ArxivDeepLPOC:
    def __init__(self):
        self.deepl_api_key = os.getenv('DEEPL_API_KEY')
        if not self.deepl_api_key:
            raise ValueError("DEEPL_API_KEY is not set in environment variables")
        
        self.translator = deepl.Translator(self.deepl_api_key)
        self.arxiv_scraper = ArxivScraper()
    
    def search_and_translate(self, query, max_results=3):
        """
        Search papers from arXiv and translate abstracts using DeepL
        """
        
        # Search on arXiv
        papers = self.arxiv_scraper.search_papers(query, max_results)
        
        if not papers:
            return []
        
        
        # Check usage status
        usage = self.translator.get_usage()
        remaining = usage.character.limit - usage.character.count
        
        # Translate each paper's abstract
        translated_papers = []
        total_chars = 0
        
        for i, paper in enumerate(papers, 1):
            
            # Check abstract character count
            abstract_chars = len(paper['abstract'])
            if remaining < abstract_chars:
                paper['translated_abstract'] = None
                paper['translation_skipped'] = True
            else:
                # Translate with DeepL
                translated = self.translate_abstract(paper['abstract'])
                
                if translated:
                    paper['translated_abstract'] = translated
                    paper['translation_skipped'] = False
                    total_chars += abstract_chars
                    remaining -= abstract_chars
                else:
                    paper['translated_abstract'] = None
                    paper['translation_skipped'] = True
            
            translated_papers.append(paper)
        
        return translated_papers
    
    def translate_abstract(self, abstract):
        """
        Translate abstract to Japanese using DeepL
        """
        try:
            if not abstract or len(abstract.strip()) < 10:
                return None
            
            # Split if too long (DeepL limit)
            max_length = 4000
            if len(abstract) > max_length:
                # Split by sentence boundaries
                sentences = abstract.split('. ')
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    test_chunk = current_chunk + sentence + ". "
                    if len(test_chunk) < max_length:
                        current_chunk = test_chunk
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Translate each chunk
                translated_chunks = []
                for chunk in chunks:
                    result = self.translator.translate_text(chunk, target_lang="JA")
                    translated_chunks.append(result.text)
                
                return " ".join(translated_chunks)
            else:
                result = self.translator.translate_text(abstract, target_lang="JA")
                return result.text
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return None
    
    def translate_title(self, title):
        """
        Translate title
        """
        try:
            result = self.translator.translate_text(title, target_lang="JA")
            return result.text
        except Exception as e:
            print(f"❌ Title translation error: {e}")
            return None
    
    def print_results(self, papers):
        """
        Display results in organized format
        """
        print("\n" + "="*80)
        print("📊 ARXIV + DEEPL Search & Translation Results")
        print("="*80)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n📄 Paper {i}")
            print(f"📝 Original Title: {paper['title']}")
            
            # Translate title
            translated_title = self.translate_title(paper['title'])
            if translated_title:
                print(f"🇯🇵 Japanese Title: {translated_title}")
            
            print(f"👥 Authors: {paper['authors_str']}")
            print(f"📅 Published: {paper['published']}")
            print(f"🔗 arXiv ID: {paper['arxiv_id']}")
            print(f"🌐 URL: {paper['url']}")
            
            print(f"\n📖 Original Abstract ({len(paper['abstract'])} chars):")
            print(paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract'])
            
            if paper.get('translated_abstract'):
                print(f"\n🇯🇵 Japanese Translation ({len(paper['translated_abstract'])} chars):")
                print(paper['translated_abstract'])
            elif paper.get('translation_skipped'):
                print("\n⚠️ Translation skipped (character limit)")
            else:
                print("\n❌ Translation failed")
            
            print("-" * 60)

def main():
    """
    Main execution for arXiv + DeepL POC
    """
    try:
        
        # Create POC instance
        poc = ArxivDeepLPOC()
        
        # Search query
        query = "machine learning"
        
        # Execute search and translation
        papers = poc.search_and_translate(query, max_results=2)
        
        if papers:
            # Display results
            poc.print_results(papers)
            
        else:
    
    except Exception as e:
        print(f"❌ POC failed: {e}")
        if "DEEPL_API_KEY" in str(e):
            print("Please set your DeepL API key in .env file:")
            print("DEEPL_API_KEY=your-api-key-here")
            print("\nGet your free API key at: https://www.deepl.com/pro-api")

if __name__ == "__main__":
    main()