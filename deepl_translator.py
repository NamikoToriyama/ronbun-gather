import os
import deepl
from dotenv import load_dotenv

load_dotenv()

class DeepLTranslator:
    def __init__(self):
        self.deepl_api_key = os.getenv('DEEPL_API_KEY')
        if not self.deepl_api_key:
            raise ValueError("DEEPL_API_KEY is not set in environment variables")
        self.translator = deepl.Translator(self.deepl_api_key)
    
    def get_usage(self):
        """DeepL使用状況を取得"""
        try:
            usage = self.translator.get_usage()
            return {
                'used': usage.character.count,
                'limit': usage.character.limit,
                'remaining': usage.character.limit - usage.character.count
            }
        except Exception as e:
            print(f"⚠️ Could not check DeepL usage: {e}")
            return {'used': 0, 'limit': 500000, 'remaining': 500000}
    
    def translate_abstract(self, abstract):
        """AbstractをDeepLで日本語翻訳"""
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
            print(f"❌ Translation error: {e}")
            return None