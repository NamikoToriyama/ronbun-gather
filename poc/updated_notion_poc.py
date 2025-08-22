import os
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime

load_dotenv()

class UpdatedNotionPOC:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN is not set in environment variables")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID is not set in environment variables")
        
        self.notion = Client(auth=self.notion_token)
    
    def get_database_info(self):
        """
        Get information about the configured database
        """
        try:
            database = self.notion.databases.retrieve(database_id=self.database_id)
            print(f"📊 Database Title: {database['title'][0]['text']['content']}")
            print(f"📊 Database ID: {database['id']}")
            
            print("\n📋 Database Properties:")
            for prop_name, prop_info in database['properties'].items():
                prop_type = prop_info['type']
                print(f"  - {prop_name}: {prop_type}")
            
            return database
        except Exception as e:
            print(f"❌ Failed to retrieve database info: {e}")
            return None
    
    def create_paper_page(self, title, authors=None, abstract=None, url=None, summary=None):
        """
        Create a new page for a paper with abstract in page content
        """
        try:
            # Properties for the database (using exact property names)
            properties = {
                "NAME ": {  # Note the space after NAME
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
            
            # Add optional properties with exact names
            properties["Read"] = {
                "select": {
                    "name": "No"  # Default to unread
                }
            }
            
            if url:
                properties["URL"] = {
                    "url": url
                }
            
            properties["Date Added"] = {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
            
            # 検索キーワードを追加（テスト用）
            properties["keyword"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": "test-keyword"
                        }
                    }
                ]
            }
            
            if summary:
                properties["Paper "] = {  # Note the space after Paper
                    "rich_text": [
                        {
                            "text": {
                                "content": summary
                            }
                        }
                    ]
                }
            
            # Page content (children) - this is where we put the abstract
            children = []
            
            if authors:
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Authors"}}]
                    }
                })
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": authors}}]
                    }
                })
            
            if abstract:
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Abstract"}}]
                    }
                })
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": abstract}}]
                    }
                })
            
            # Create the page
            page = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            print(f"✅ Created page: {title}")
            print(f"📄 Page ID: {page['id']}")
            print(f"📄 Abstract added to page content")
            return page
            
        except Exception as e:
            print(f"❌ Failed to create page: {e}")
            return None
    
    def get_property_names(self):
        """
        Get list of property names from database
        """
        try:
            database = self.notion.databases.retrieve(database_id=self.database_id)
            return list(database['properties'].keys())
        except:
            return []

def main():
    """
    Test the updated Notion POC functionality
    """
    try:
        notion_poc = UpdatedNotionPOC()
        
        print("🔄 Getting database info...")
        notion_poc.get_database_info()
        
        print("\n🔄 Creating a test paper page...")
        test_page = notion_poc.create_paper_page(
            title="Deep Learning for Natural Language Processing",
            authors="Smith, J., Doe, A., Johnson, M.",
            abstract="This paper presents a comprehensive study of deep learning techniques applied to natural language processing tasks. We explore various neural network architectures including transformers, RNNs, and CNNs for text classification, sentiment analysis, and machine translation. Our experiments show that transformer-based models achieve state-of-the-art performance across multiple benchmarks.",
            url="https://arxiv.org/abs/2023.12345",
            summary="Comprehensive study of DL techniques for NLP with focus on transformers."
        )
        
        if test_page:
            print("\n✅ Updated Notion POC test completed successfully!")
            print("📝 Check your Notion database to see the new page with abstract in content!")
        else:
            print("\n❌ Test page creation failed")
            
    except Exception as e:
        print(f"❌ Error in Updated Notion POC: {e}")

if __name__ == "__main__":
    main()
