import os
from notion_client import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NotionSaver:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        if self.notion_token and self.notion_database_id:
            self.notion = Client(auth=self.notion_token)
            print("✅ Notion integration enabled")
        else:
            self.notion = None
            print("⚠️ Notion integration disabled (missing credentials)")
    
    def is_enabled(self):
        """Notion連携が有効かどうか"""
        return self.notion is not None
    
    def get_existing_urls(self):
        """データベースから既存のURLを取得"""
        if not self.notion:
            return set()
        
        try:
            existing_urls = set()
            has_more = True
            start_cursor = None
            
            while has_more:
                # データベースをクエリ
                query_params = {
                    "database_id": self.notion_database_id,
                    "page_size": 100
                }
                
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                response = self.notion.databases.query(**query_params)
                
                # 各ページのURLプロパティを取得
                for page in response["results"]:
                    properties = page.get("properties", {})
                    url_prop = properties.get("URL", {})
                    
                    if url_prop.get("type") == "url" and url_prop.get("url"):
                        existing_urls.add(url_prop["url"])
                
                # 次のページがあるかチェック
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            print(f"📊 Found {len(existing_urls)} existing papers in Notion database")
            return existing_urls
            
        except Exception as e:
            print(f"❌ Error getting existing URLs: {e}")
            return set()
    
    def is_duplicate(self, paper_url, existing_urls):
        """論文URLが重複しているかチェック"""
        return paper_url in existing_urls if paper_url else False
    
    def save_paper(self, paper, search_keyword=None):
        """論文情報をNotionに保存"""
        if not self.notion:
            return False
            
        try:
            # Notionページのプロパティ設定
            properties = {
                "NAME ": {  # Note the space after NAME
                    "title": [
                        {
                            "text": {
                                "content": paper.get('title', 'Unknown Title')
                            }
                        }
                    ]
                },
                "Read": {
                    "select": {
                        "name": "UNREAD"  # デフォルトでUNREAD
                    }
                },
                "Date Added": {
                    "date": {
                        "start": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            }
            
            # 検索キーワードを追加
            if search_keyword:
                properties["keyword"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": search_keyword
                            }
                        }
                    ]
                }
            
            # URLがある場合は追加
            if paper.get('pdf_url'):
                properties["URL"] = {
                    "url": paper['pdf_url']
                }
            
            # ページコンテンツ（children）を作成
            children = []
            
            # 著者情報
            if paper.get('authors_str'):
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Authors"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paper['authors_str']}}]
                        }
                    }
                ])
            
            # 英語論文（オリジナル）
            if paper.get('abstract'):
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "English Abstract"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paper['abstract']}}]
                        }
                    }
                ])
            
            # DeepL翻訳済み論文
            if paper.get('translated_abstract'):
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Japanese Translation (DeepL)"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paper['translated_abstract']}}]
                        }
                    }
                ])
            
            # 図表
            if paper.get('images'):
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Figures"}}]
                    }
                })
                
                for i, img in enumerate(paper['images'][:5], 1):  # 最大5個まで
                    # 画像URL
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": f"Figure {i}: "}},
                                {"type": "text", "text": {"content": img['url']}, "href": img['url']}
                            ]
                        }
                    })
                    
                    # キャプション（ある場合）
                    if img.get('caption'):
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": f"Caption: {img['caption']}"}}]
                            }
                        })
            
            # Notionページを作成
            page = self.notion.pages.create(
                parent={"database_id": self.notion_database_id},
                properties=properties,
                children=children
            )
            
            print(f"✅ Saved to Notion: {paper.get('title', 'Unknown')[:50]}...")
            return page
            
        except Exception as e:
            print(f"❌ Notion save error: {e}")
            return None
