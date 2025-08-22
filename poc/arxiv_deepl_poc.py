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
        arXivで論文を検索し、abstractをDeepLで日本語翻訳
        """
        print(f"🔍 Searching for papers: '{query}'")
        
        # arXivで検索
        papers = self.arxiv_scraper.search_papers(query, max_results)
        
        if not papers:
            print("❌ No papers found")
            return []
        
        print(f"✅ Found {len(papers)} papers")
        
        # 使用状況を確認
        usage = self.translator.get_usage()
        remaining = usage.character.limit - usage.character.count
        print(f"📊 DeepL usage: {usage.character.count:,} / {usage.character.limit:,} characters")
        print(f"📊 Remaining: {remaining:,} characters")
        
        # 各論文のabstractを翻訳
        translated_papers = []
        total_chars = 0
        
        for i, paper in enumerate(papers, 1):
            print(f"\n📄 Processing paper {i}/{len(papers)}: {paper['title'][:50]}...")
            
            # abstractの文字数をチェック
            abstract_chars = len(paper['abstract'])
            if remaining < abstract_chars:
                print(f"⚠️ Skipping translation (insufficient quota: need {abstract_chars}, have {remaining})")
                paper['translated_abstract'] = None
                paper['translation_skipped'] = True
            else:
                # DeepLで翻訳
                translated = self.translate_abstract(paper['abstract'])
                
                if translated:
                    paper['translated_abstract'] = translated
                    paper['translation_skipped'] = False
                    total_chars += abstract_chars
                    remaining -= abstract_chars
                    print(f"✅ Translation completed ({abstract_chars} characters)")
                else:
                    paper['translated_abstract'] = None
                    paper['translation_skipped'] = True
                    print("❌ Failed to translate abstract")
            
            translated_papers.append(paper)
        
        print(f"\n📊 Translation summary: {total_chars:,} characters used")
        return translated_papers
    
    def translate_abstract(self, abstract):
        """
        AbstractをDeepLで日本語翻訳
        """
        try:
            if not abstract or len(abstract.strip()) < 10:
                return None
            
            # 長すぎる場合は分割（DeepLの制限対策）
            max_length = 4000
            if len(abstract) > max_length:
                # 文の区切りで分割
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
                
                # 各チャンクを翻訳
                translated_chunks = []
                for chunk in chunks:
                    result = self.translator.translate_text(chunk, target_lang="JA")
                    translated_chunks.append(result.text)
                
                return " ".join(translated_chunks)
            else:
                result = self.translator.translate_text(abstract, target_lang="JA")
                return result.text
            
        except Exception as e:
            print(f"❌ 翻訳エラー: {e}")
            return None
    
    def translate_title(self, title):
        """
        タイトルを翻訳
        """
        try:
            result = self.translator.translate_text(title, target_lang="JA")
            return result.text
        except Exception as e:
            print(f"❌ タイトル翻訳エラー: {e}")
            return None
    
    def print_results(self, papers):
        """
        結果を整理して表示
        """
        print("\n" + "="*80)
        print("📊 ARXIV + DEEPL 検索・翻訳結果")
        print("="*80)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n📄 論文 {i}")
            print(f"📝 原題: {paper['title']}")
            
            # タイトル翻訳
            translated_title = self.translate_title(paper['title'])
            if translated_title:
                print(f"🇯🇵 邦題: {translated_title}")
            
            print(f"👥 著者: {paper['authors_str']}")
            print(f"📅 公開日: {paper['published']}")
            print(f"🔗 arXiv ID: {paper['arxiv_id']}")
            print(f"🌐 URL: {paper['url']}")
            
            print(f"\n📖 原文Abstract ({len(paper['abstract'])} chars):")
            print(paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract'])
            
            if paper.get('translated_abstract'):
                print(f"\n🇯🇵 日本語翻訳 ({len(paper['translated_abstract'])} chars):")
                print(paper['translated_abstract'])
            elif paper.get('translation_skipped'):
                print("\n⚠️ 翻訳をスキップしました（文字数制限のため）")
            else:
                print("\n❌ 翻訳に失敗しました")
            
            print("-" * 60)

def main():
    """
    arXiv + DeepL POCのメイン実行
    """
    try:
        print("🚀 Starting arXiv + DeepL POC...")
        
        # POCインスタンス作成
        poc = ArxivDeepLPOC()
        
        # 検索クエリ
        query = "machine learning"
        
        # 検索と翻訳実行
        papers = poc.search_and_translate(query, max_results=2)
        
        if papers:
            # 結果表示
            poc.print_results(papers)
            
            print(f"\n✅ POC completed successfully!")
            translated_count = len([p for p in papers if p.get('translated_abstract')])
            print(f"📄 Processed {len(papers)} papers")
            print(f"🇯🇵 Translated {translated_count} abstracts")
        else:
            print("❌ No papers found or processed")
    
    except Exception as e:
        print(f"❌ POC failed: {e}")
        if "DEEPL_API_KEY" in str(e):
            print("Please set your DeepL API key in .env file:")
            print("DEEPL_API_KEY=your-api-key-here")
            print("\nGet your free API key at: https://www.deepl.com/pro-api")

if __name__ == "__main__":
    main()