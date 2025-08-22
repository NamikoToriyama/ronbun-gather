import os
from dotenv import load_dotenv
import deepl

load_dotenv()

def test_deepl_connection():
    """
    DeepL API接続をテスト
    """
    try:
        # APIキーをチェック
        api_key = os.getenv('DEEPL_API_KEY')
        if not api_key:
            print("❌ DEEPL_API_KEY is not set in environment variables")
            print("Please add your DeepL API key to .env file:")
            print("DEEPL_API_KEY=your-api-key-here")
            print("\nDeepL API Key取得方法:")
            print("1. https://www.deepl.com/pro-api にアクセス")
            print("2. アカウント作成（無料プランあり）")
            print("3. API Keyを取得")
            return False
        
        # DeepL翻訳者を初期化
        translator = deepl.Translator(api_key)
        
        # 使用状況を確認
        usage = translator.get_usage()
        print(f"✅ DeepL connection successful!")
        print(f"📊 Usage: {usage.character.count:,} / {usage.character.limit:,} characters")
        print(f"📊 Remaining: {usage.character.limit - usage.character.count:,} characters")
        
        # 簡単な翻訳テスト
        result = translator.translate_text("Hello, world!", target_lang="JA")
        print(f"🔄 Test translation: 'Hello, world!' → '{result.text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ DeepL connection failed: {e}")
        if "auth" in str(e).lower() or "key" in str(e).lower():
            print("Please check your DeepL API key in .env file")
        return False

def translate_text(text, target_lang="JA", source_lang=None):
    """
    テキストをDeepLで翻訳
    """
    try:
        api_key = os.getenv('DEEPL_API_KEY')
        if not api_key:
            return None
            
        translator = deepl.Translator(api_key)
        
        result = translator.translate_text(
            text, 
            target_lang=target_lang,
            source_lang=source_lang
        )
        
        return result.text
        
    except Exception as e:
        print(f"❌ 翻訳エラー: {e}")
        return None

def translate_abstract(abstract):
    """
    論文のabstractを日本語に翻訳
    """
    if not abstract or len(abstract.strip()) < 10:
        return None
    
    # 長すぎる場合は分割
    max_length = 4000  # DeepLの制限
    if len(abstract) > max_length:
        # 文の区切りで分割
        sentences = abstract.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 各チャンクを翻訳
        translated_chunks = []
        for chunk in chunks:
            translated = translate_text(chunk)
            if translated:
                translated_chunks.append(translated)
        
        return " ".join(translated_chunks)
    else:
        return translate_text(abstract)

def main():
    print("🔄 Testing DeepL connection...")
    
    if test_deepl_connection():
        print("\n🔄 Testing abstract translation...")
        
        # サンプルabstractで翻訳テスト
        sample_abstract = """
        This paper presents a novel approach to typhoon prediction using deep learning models. 
        We propose a new neural network architecture that combines convolutional neural networks (CNNs) 
        with long short-term memory (LSTM) networks to predict typhoon paths and intensity. 
        Our model achieves 95% accuracy in predicting typhoon trajectories 24 hours in advance, 
        significantly outperforming traditional meteorological models.
        """
        
        translated = translate_abstract(sample_abstract.strip())
        
        if translated:
            print("✅ Translation test successful!")
            print(f"Original ({len(sample_abstract)} chars):")
            print(sample_abstract.strip())
            print(f"\nTranslated ({len(translated)} chars):")
            print(translated)
        else:
            print("❌ Translation test failed")
    
    else:
        print("Please set up DeepL API key first")

if __name__ == "__main__":
    main()