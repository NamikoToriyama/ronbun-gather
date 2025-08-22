import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv

load_dotenv()

class LineNotifier:
    def __init__(self):
        self.line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
        self.user_id = os.getenv('LINE_USER_ID')
        
        if not self.user_id:
            raise ValueError("LINE_USER_ID is not set in environment variables")
    
    def send_message(self, message):
        """LINEにメッセージを送信"""
        try:
            self.line_bot_api.push_message(
                self.user_id,
                TextSendMessage(text=message)
            )
            print(f"✅ LINE message sent successfully")
            return True
        except Exception as e:
            print(f"❌ LINE message error: {e}")
            return False
    
    def format_basic_info_message(self, paper, paper_num, total_papers):
        """1つ目のメッセージ（基本情報）をフォーマット"""
        message = f"[{paper_num}/{total_papers}] 📄 新しい論文\n\n"
        message += f"【タイトル】\n{paper.get('title', '不明')}\n\n"
        message += f"【著者】\n{paper.get('authors_str', '不明')}\n\n"
        message += f"【公開日】\n{paper.get('published', '不明')}\n\n"
        
        # PDFと詳細URLが同じ場合は統合
        pdf_url = paper.get('pdf_url', '')
        
        if pdf_url:
            message += f"【PDF・詳細】\n{pdf_url}\n\n"
                    
        if paper.get('categories'):
            message += f"【カテゴリ】\n{', '.join(paper['categories'][:3])}"
        
        return message
    
    def format_abstract_message(self, paper):
        """2つ目のメッセージ（翻訳した要約）をフォーマット"""
        message = f"📝 要約（日本語翻訳）\n\n"
        
        if paper.get('translated_abstract'):
            message += paper['translated_abstract']
        else:
            message += "翻訳に失敗したため、原文を表示します：\n\n"
            message += paper.get('abstract', '要約なし')
        
        return message
