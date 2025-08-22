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
        """Search papers from Google Scholar and get detailed information"""
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
                    # Get detailed information
                    detailed_paper = self.get_paper_details(paper)
                    papers.append(detailed_paper)
                    
                # Rate limiting
                time.sleep(random.uniform(2, 4))
                    
        except Exception as e:
            print(f"Search error: {e}")
            
        return papers
    
    def extract_paper_info(self, result_div):
        """Extract basic paper information"""
        try:
            paper = {}
            
            # Title and paper link
            title_tag = result_div.find('h3', class_='gs_rt')
            if title_tag:
                link_tag = title_tag.find('a')
                if link_tag:
                    paper['title'] = link_tag.get_text().strip()
                    paper['url'] = link_tag.get('href', '')
                else:
                    paper['title'] = title_tag.get_text().strip()
                    paper['url'] = ''
            
            # Authors and publication info
            authors_tag = result_div.find('div', class_='gs_a')
            if authors_tag:
                paper['authors'] = authors_tag.get_text().strip()
            
            # Abstract/snippet
            snippet_tag = result_div.find('div', class_='gs_rs')
            if snippet_tag:
                paper['snippet'] = snippet_tag.get_text().strip()
            
            # Citation count
            cited_tag = result_div.find('div', class_='gs_fl')
            if cited_tag:
                cite_link = cited_tag.find('a')
                if cite_link and 'Cited by' in cite_link.get_text():
                    citations = cite_link.get_text().replace('Cited by ', '')
                    paper['citations'] = citations
            
            # Find PDF links
            pdf_links = result_div.find_all('a')
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                if 'pdf' in text or href.endswith('.pdf'):
                    paper['pdf_url'] = href
                    break
            
            return paper if paper.get('title') else None
            
        except Exception as e:
            print(f"Paper extraction error: {e}")
            return None
    
    def get_paper_details(self, paper):
        """Get detailed paper information (abstract, PDF, etc.)"""
        try:
            if not paper.get('url'):
                return paper
                
            response = requests.get(paper['url'], headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find abstract
            abstract = self.extract_abstract(soup)
            if abstract:
                paper['abstract'] = abstract
            
            # Find more accurate PDF link
            pdf_url = self.find_pdf_link(soup, paper['url'])
            if pdf_url:
                paper['pdf_url'] = pdf_url
            
            # Find DOI
            doi = self.extract_doi(soup)
            if doi:
                paper['doi'] = doi
            
            # Find images
            images = self.extract_images(soup)
            if images:
                paper['images'] = images
                
        except Exception as e:
            print(f"Detail retrieval error: {e}")
            
        return paper
    
    def extract_abstract(self, soup):
        """Extract abstract"""
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
                if len(text) > 50:  # Check if text is long enough
                    return text
        
        # Also search in meta tags
        meta_abstract = soup.find('meta', attrs={'name': 'description'})
        if meta_abstract:
            content = meta_abstract.get('content', '')
            if len(content) > 50:
                return content
                
        return None
    
    def find_pdf_link(self, soup, base_url):
        """Find PDF links"""
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
            
            # Check for PDF-indicating text or URL patterns
            if 'pdf' in text or any(re.search(pattern, href, re.I) for pattern in pdf_patterns):
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        return None
    
    def extract_doi(self, soup):
        """Extract DOI"""
        # From meta tags
        doi_meta = soup.find('meta', attrs={'name': 'citation_doi'})
        if doi_meta:
            return doi_meta.get('content')
        
        # From text using regex
        text = soup.get_text()
        doi_match = re.search(r'10\.\d+/[^\s]+', text)
        if doi_match:
            return doi_match.group()
            
        return None
    
    def extract_images(self, soup):
        """Extract paper-related images"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            alt = img.get('alt', '')
            
            if src and any(keyword in alt.lower() for keyword in ['figure', 'chart', 'graph', 'diagram']):
                if src.startswith('http'):
                    images.append(src)
                    
        return images[:3]  # Maximum 3 images

def main():
    scraper = PaperScraper()
    
    query = "typhoon prediction"
    print("=" * 60)
    
    papers = scraper.search_papers(query, num_results=2)
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'Unknown title')}")
        print(f"Authors: {paper.get('authors', 'Unknown')}")
        print(f"URL: {paper.get('url', 'None')}")
        
        if paper.get('abstract'):
            print(f"Abstract: {paper['abstract'][:200]}...")
        elif paper.get('snippet'):
            print(f"Snippet: {paper['snippet']}")
            
        if paper.get('pdf_url'):
            print(f"PDF: {paper['pdf_url']}")
            
        if paper.get('doi'):
            print(f"DOI: {paper['doi']}")
            
        if paper.get('images'):
            print(f"Images: {len(paper['images'])} found")
            for img_url in paper['images']:
                print(f"  - {img_url}")
                
        if paper.get('citations'):
            print(f"Citations: {paper['citations']}")
            
        print("-" * 60)

if __name__ == "__main__":
    main()