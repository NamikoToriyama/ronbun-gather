import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, quote
import time
import xml.etree.ElementTree as ET

class ArxivScraper:
    def __init__(self):
        self.base_url = "https://export.arxiv.org/api/query"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_papers(self, query, max_results=5):
        """arXivで論文を検索し、詳細情報を取得"""
        papers = []
        
        try:
            # arXiv APIで検索（関連性順にソート、気象・地球科学関連カテゴリを優先）
            # 気象・地球科学に関連するカテゴリも含めて検索
            search_terms = [
                f'ti:"{query}"',  # タイトルに完全一致
                f'abs:"{query}"',  # アブストラクトに完全一致
                f'(cat:physics.ao-ph OR cat:physics.geo-ph) AND all:{query}'  # 気象・地球物理学カテゴリ
            ]
            
            params = {
                'search_query': ' OR '.join(search_terms),
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',  # 関連性順
                'sortOrder': 'descending'
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # XMLを解析
            root = ET.fromstring(response.content)
            
            # Namespace定義
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                paper = self.extract_paper_info_from_xml(entry, ns)
                
                # HTMLページから画像を取得
                images = self.extract_images_from_html(paper['url'])
                if images:
                    paper['images'] = images
                
                papers.append(paper)
                time.sleep(1)  # レート制限対策
                
        except Exception as e:
            print(f"arXiv検索エラー: {e}")
            
        return papers
    
    def extract_paper_info_from_xml(self, entry, ns):
        """XMLエントリから論文情報を抽出"""
        paper = {}
        
        # タイトル
        title_elem = entry.find('atom:title', ns)
        paper['title'] = title_elem.text.strip() if title_elem is not None else ''
        
        # 著者
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        paper['authors'] = authors
        paper['authors_str'] = ', '.join(authors)
        
        # Abstract
        summary_elem = entry.find('atom:summary', ns)
        paper['abstract'] = summary_elem.text.strip() if summary_elem is not None else ''
        
        # 公開日
        published_elem = entry.find('atom:published', ns)
        paper['published'] = published_elem.text[:10] if published_elem is not None else ''
        
        # 更新日
        updated_elem = entry.find('atom:updated', ns)
        paper['updated'] = updated_elem.text[:10] if updated_elem is not None else ''
        
        # URL
        id_elem = entry.find('atom:id', ns)
        paper['url'] = id_elem.text if id_elem is not None else ''
        
        # arXiv ID
        if paper['url']:
            paper['arxiv_id'] = paper['url'].split('/')[-1]
        
        # PDF URL
        for link in entry.findall('atom:link', ns):
            if link.get('type') == 'application/pdf':
                paper['pdf_url'] = link.get('href')
                break
        
        # カテゴリ
        categories = []
        for category in entry.findall('atom:category', ns):
            term = category.get('term')
            if term:
                categories.append(term)
        paper['categories'] = categories
        paper['primary_category'] = categories[0] if categories else ''
        
        # DOI
        doi_elem = entry.find('arxiv:doi', ns)
        paper['doi'] = doi_elem.text if doi_elem is not None else None
        
        # Journal reference
        journal_elem = entry.find('arxiv:journal_ref', ns)
        paper['journal_ref'] = journal_elem.text if journal_elem is not None else None
        
        # Comment
        comment_elem = entry.find('arxiv:comment', ns)
        paper['comment'] = comment_elem.text if comment_elem is not None else None
        
        return paper
    
    def extract_images_from_html(self, arxiv_url):
        """arXivのHTMLページから図表画像を抽出"""
        images = []
        
        try:
            # arXiv IDを取得
            arxiv_id = arxiv_url.split('/')[-1]
            
            # HTMLページのURL
            html_url = f"https://arxiv.org/html/{arxiv_id}"
            
            response = requests.get(html_url, headers=self.headers)
            
            # HTMLページが存在しない場合はabs ページから試す
            if response.status_code == 404:
                abs_url = f"https://arxiv.org/abs/{arxiv_id}"
                response = requests.get(abs_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 様々な画像パターンを検索
                img_patterns = [
                    'img[src*="figure"]',
                    'img[src*="fig"]', 
                    'img[alt*="Figure"]',
                    'img[alt*="Fig"]',
                    'img[src*="png"]',
                    'img[src*="jpg"]',
                    'img[src*="jpeg"]',
                    'img[src*="svg"]'
                ]
                
                for pattern in img_patterns:
                    img_tags = soup.select(pattern)
                    for img in img_tags:
                        src = img.get('src')
                        alt = img.get('alt', '')
                        
                        if src:
                            # 相対URLを絶対URLに変換
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = urljoin(html_url, src)
                            elif not src.startswith('http'):
                                src = urljoin(html_url, src)
                            
                            image_info = {
                                'url': src,
                                'alt': alt,
                                'caption': self.find_caption_near_image(img)
                            }
                            
                            # 重複チェック
                            if not any(existing['url'] == src for existing in images):
                                images.append(image_info)
                
                # arXivの画像サーバーからも検索
                arxiv_images = self.get_arxiv_source_images(arxiv_id)
                images.extend(arxiv_images)
                
        except Exception as e:
            print(f"画像抽出エラー ({arxiv_url}): {e}")
            
        return images[:5]  # 最大5個まで
    
    def find_caption_near_image(self, img_tag):
        """画像の近くからキャプションを探す"""
        try:
            # 親要素からキャプションを探す
            parent = img_tag.parent
            if parent:
                # figcaption タグ
                caption = parent.find('figcaption')
                if caption:
                    return caption.get_text().strip()
                
                # 画像の後の p タグ
                next_p = img_tag.find_next('p')
                if next_p and len(next_p.get_text()) < 200:
                    text = next_p.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['figure', 'fig.', 'caption']):
                        return text
            
        except Exception:
            pass
            
        return ""
    
    def get_arxiv_source_images(self, arxiv_id):
        """arXivのソースファイルから画像を取得"""
        images = []
        
        try:
            # arXivの画像用URLパターン
            base_patterns = [
                f"https://arxiv.org/html/{arxiv_id}/",
                f"https://arxiv.org/src/{arxiv_id}/",
            ]
            
            # よくある画像ファイル名
            common_names = [
                "figure1.png", "figure2.png", "figure3.png",
                "fig1.png", "fig2.png", "fig3.png",
                "image1.png", "image2.png", "image3.png",
                "plot1.png", "plot2.png", "plot3.png"
            ]
            
            for base_url in base_patterns:
                for name in common_names:
                    img_url = base_url + name
                    
                    # 画像が存在するかチェック
                    try:
                        response = requests.head(img_url, headers=self.headers, timeout=5)
                        if response.status_code == 200:
                            images.append({
                                'url': img_url,
                                'alt': f'Figure from {arxiv_id}',
                                'caption': f'Image: {name}'
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f"arXivソース画像取得エラー: {e}")
            
        return images
    
    def download_pdf(self, paper, download_dir="./downloads"):
        """PDFをダウンロード"""
        try:
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                
            filename = f"{paper['arxiv_id']}.pdf"
            filepath = os.path.join(download_dir, filename)
            
            response = requests.get(paper['pdf_url'], headers=self.headers)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            print(f"PDF downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"PDF download error: {e}")
            return None

def main(custom_queries=None):
    scraper = ArxivScraper()
    
    # デフォルトの検索クエリ（引数で指定されない場合）
    default_queries = [
        "typhoon eye",
        "hurricane eye", 
        "typhoon intensity forecast"
    ]
    
    # 引数で指定されたクエリまたはデフォルトを使用
    queries = custom_queries if custom_queries else default_queries
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"検索クエリ: {query}")
        print('='*60)
        
        papers = scraper.search_papers(query, max_results=2)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"著者: {paper['authors_str']}")
            print(f"公開日: {paper['published']}")
            print(f"arXiv ID: {paper['arxiv_id']}")
            print(f"カテゴリ: {paper['primary_category']}")
            print(f"PDF: {paper['pdf_url']}")
            
            if paper.get('journal_ref'):
                print(f"ジャーナル: {paper['journal_ref']}")
                
            if paper.get('doi'):
                print(f"DOI: {paper['doi']}")
            
            print(f"\nAbstract:")
            print(paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract'])
            
            if paper.get('images'):
                print(f"\n画像 ({len(paper['images'])}個):")
                for j, img in enumerate(paper['images'], 1):
                    print(f"  {j}. {img['url']}")
                    if img['caption']:
                        print(f"     Caption: {img['caption']}")
            
            print("-" * 60)

if __name__ == "__main__":
    main()