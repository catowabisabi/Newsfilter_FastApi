from translate import Translator

# 翻譯器

class CnTranslator:
    def __init__(self):
        self.translator     = Translator()
    def translate_to_chinese(self, text):
        try:
            # 將長文本分成較小的段落
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            translated_chunks = []
            for chunk in chunks:
                translated = self.translator.translate(chunk, dest='zh-TW')
                translated_chunks.append(translated.text)
            return ' '.join(translated_chunks)
        except Exception as e:
            print(f"翻譯錯誤: {e}")
            return text