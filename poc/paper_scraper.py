import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote, urljoin
import re

class PaperScraper:
    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def search_papers(self, query, num_results=5):
        """Google Scholarで論文を検索し、詳細情報を取得"""
        papers = []
        
        try:
            search_url = f"{self.base_url}?q={quote(query)}&hl=en&num={num_results}"
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find_all('div', class_='gs_r gs_or gs_scl')
            
            for result in results[:num_results]:
                paper = self.extract_paper_info(result)
                if paper:
                    # 詳細情報を取得
                    detailed_paper = self.get_paper_details(paper)
                    papers.append(detailed_paper)
                    
                # レート制限対策
                time.sleep(random.uniform(2, 4))
                    
        except Exception as e:
            print(f"検索エラー: {e}")
            
        return papers
    
    def extract_paper_info(self, result_div):
        """基本的な論文情報を抽出"""
        try:
            paper = {}
            
            # タイトルと論文リンク
            title_tag = result_div.find('h3', class_='gs_rt')
            if title_tag:
                link_tag = title_tag.find('a')
                if link_tag:
                    paper['title'] = link_tag.get_text().strip()
                    paper['url'] = link_tag.get('href', '')
                else:
                    paper['title'] = title_tag.get_text().strip()
                    paper['url'] = ''
            
            # 著者と出版情報
            authors_tag = result_div.find('div', class_='gs_a')
            if authors_tag:
                paper['authors'] = authors_tag.get_text().strip()
            
            # 抄録
            snippet_tag = result_div.find('div', class_='gs_rs')
            if snippet_tag:
                paper['snippet'] = snippet_tag.get_text().strip()
            
            # 引用数
            cited_tag = result_div.find('div', class_='gs_fl')
            if cited_tag:
                cite_link = cited_tag.find('a')
                if cite_link and 'Cited by' in cite_link.get_text():
                    citations = cite_link.get_text().replace('Cited by ', '')
                    paper['citations'] = citations
            
            # PDFリンクを探す
            pdf_links = result_div.find_all('a')
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                if 'pdf' in text or href.endswith('.pdf'):
                    paper['pdf_url'] = href
                    break
            
            return paper if paper.get('title') else None
            
        except Exception as e:
            print(f"論文情報抽出エラー: {e}")
            return None
    
    def get_paper_details(self, paper):
        """論文の詳細情報を取得（abstract、PDF等）"""
        try:
            if not paper.get('url'):
                return paper
                
            response = requests.get(paper['url'], headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Abstractを探す
            abstract = self.extract_abstract(soup)
            if abstract:
                paper['abstract'] = abstract
            
            # より正確なPDFリンクを探す
            pdf_url = self.find_pdf_link(soup, paper['url'])
            if pdf_url:
                paper['pdf_url'] = pdf_url
            
            # DOIを探す
            doi = self.extract_doi(soup)
            if doi:
                paper['doi'] = doi
            
            # 画像を探す
            images = self.extract_images(soup)
            if images:
                paper['images'] = images
                
        except Exception as e:
            print(f"詳細情報取得エラー: {e}")
            
        return paper
    
    def extract_abstract(self, soup):
        """abstractを抽出"""
        abstract_selectors = [
            'div.abstract',
            'section.abstract', 
            'div.section.abstract',
            'p.abstract',
            '[id*="abstract"]',
            '[class*="abstract"]'
        ]
        
        for selector in abstract_selectors:
            abstract_tag = soup.select_one(selector)
            if abstract_tag:
                text = abstract_tag.get_text().strip()
                if len(text) > 50:  # 十分な長さがあるかチェック
                    return text
        
        # metaタグからも探す
        meta_abstract = soup.find('meta', attrs={'name': 'description'})
        if meta_abstract:
            content = meta_abstract.get('content', '')
            if len(content) > 50:
                return content
                
        return None
    
    def find_pdf_link(self, soup, base_url):
        """PDFリンクを探す"""
        pdf_patterns = [
            r'\.pdf$',
            r'\.pdf\?',
            r'download.*pdf',
            r'pdf.*download'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            text = link.get_text().lower()
            
            # PDFを示すテキストやURLパターンをチェック
            if 'pdf' in text or any(re.search(pattern, href, re.I) for pattern in pdf_patterns):
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        return None
    
    def extract_doi(self, soup):
        """DOIを抽出"""
        # metaタグから
        doi_meta = soup.find('meta', attrs={'name': 'citation_doi'})
        if doi_meta:
            return doi_meta.get('content')
        
        # テキストから正規表現で
        text = soup.get_text()
        doi_match = re.search(r'10\.\d+/[^\s]+', text)
        if doi_match:
            return doi_match.group()
            
        return None
    
    def extract_images(self, soup):
        """論文に関連する画像を抽出"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            alt = img.get('alt', '')
            
            if src and any(keyword in alt.lower() for keyword in ['figure', 'chart', 'graph', 'diagram']):
                if src.startswith('http'):
                    images.append(src)
                    
        return images[:3]  # 最大3つまで

def main():
    scraper = PaperScraper()
    
    query = "typhoon prediction"
    print(f"検索クエリ: {query}")
    print("=" * 60)
    
    papers = scraper.search_papers(query, num_results=2)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'タイトル不明')}")
        print(f"著者: {paper.get('authors', '不明')}")
        print(f"URL: {paper.get('url', 'なし')}")
        
        if paper.get('abstract'):
            print(f"Abstract: {paper['abstract'][:200]}...")
        elif paper.get('snippet'):
            print(f"概要: {paper['snippet']}")
            
        if paper.get('pdf_url'):
            print(f"PDF: {paper['pdf_url']}")
            
        if paper.get('doi'):
            print(f"DOI: {paper['doi']}")
            
        if paper.get('images'):
            print(f"画像: {len(paper['images'])}個見つかりました")
            for img_url in paper['images']:
                print(f"  - {img_url}")
                
        if paper.get('citations'):
            print(f"引用数: {paper['citations']}")
            
        print("-" * 60)

if __name__ == "__main__":
    main()