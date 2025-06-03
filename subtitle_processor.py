import pysrt
import os
import subprocess
import requests
import json
import openai
import hashlib
import random
from datetime import timedelta

def extract_subtitles(video_path):
    """从视频文件中提取字幕或尝试读取同名SRT文件"""
    # 尝试读取同名SRT文件
    srt_path = os.path.splitext(video_path)[0] + '.srt'
    if os.path.exists(srt_path):
        try:
            return pysrt.open(srt_path)
        except Exception as e:
            print(f"读取SRT文件失败: {e}")
    
    # 尝试从视频中提取字幕
    temp_srt = os.path.join(os.path.dirname(video_path), 'extracted_subs.srt')
    try:
        # 首先检查视频是否有字幕轨道
        cmd_check = [
            'ffprobe', '-v', 'error', 
            '-select_streams', 's', 
            '-show_entries', 'stream=index', 
            '-of', 'csv=p=0', 
            video_path
        ]
        result = subprocess.run(cmd_check, capture_output=True, text=True)
        
        if result.stdout.strip():
            # 使用FFmpeg提取字幕
            cmd = [
                'ffmpeg', '-i', video_path, 
                '-map', '0:s:0', temp_srt, 
                '-y'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.exists(temp_srt):
                return pysrt.open(temp_srt)
    except Exception as e:
        print(f"提取字幕失败: {e}")
    
    return None

def read_text_file(file_path):
    """读取文本文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文本文件失败: {e}")
        return ""

def save_text_file(file_path, content):
    """保存文本内容到文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"保存文本文件失败: {e}")
        return False

def translate_text_libre(text, target_lang):
    """使用LibreTranslate API翻译文本 - 可能不可用"""
    url = "https://libretranslate.de/translate"
    
    payload = {
        "q": text,
        "source": "auto",
        "target": target_lang,
        "format": "text"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return response.json()['translatedText']
        else:
            print(f"翻译请求失败: {response.status_code}")
            return text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text

def translate_text_baidu(text, target_lang, appid=None, secret_key=None):
    """使用百度翻译API翻译文本"""
    # 百度翻译API配置
    url = "http://api.fanyi.baidu.com/api/trans/vip/translate"
    
    # 语言代码映射
    language_mapping = {
        "en": "en",    # 英语
        "zh": "zh",    # 中文
        "ja": "jp",    # 日语
        "ko": "kor",   # 韩语
        "fr": "fra",   # 法语
        "de": "de",    # 德语
        "es": "spa"    # 西班牙语
    }
    
    # 如果没有映射，使用原始代码
    target_lang_code = language_mapping.get(target_lang, target_lang)
    
    # 如果没有提供API密钥，使用备用翻译方法
    if not appid or not secret_key:
        print("未提供百度翻译API密钥，使用备用翻译方法...")
        return translate_text_fallback(text, target_lang)
    
    # 生成随机数
    salt = random.randint(32768, 65536)
    
    # 计算签名
    sign_str = f"{appid}{text}{salt}{secret_key}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    # 构建请求参数
    params = {
        "q": text,
        "from": "auto",
        "to": target_lang_code,
        "appid": appid,
        "salt": salt,
        "sign": sign
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            if "error_code" in result:
                error_code = result.get("error_code")
                error_msg = result.get("error_msg", "未知错误")
                print(f"百度翻译API错误: {error_code} - {error_msg}")
                
                # 处理特定错误
                if error_code == "58000":  # IP白名单错误
                    print("请确保您的IP已添加到百度翻译API的白名单中")
                    print("您可以在百度翻译开放平台添加IP白名单")
                    print("当前IP:", result.get("data", {}).get("client_ip", "未知"))
                
                return translate_text_fallback(text, target_lang)
            
            if "trans_result" in result:
                return result["trans_result"][0]["dst"]
            else:
                print(f"翻译结果格式错误: {result}")
                return translate_text_fallback(text, target_lang)
        else:
            print(f"百度翻译请求失败: {response.status_code}")
            return translate_text_fallback(text, target_lang)
    except Exception as e:
        print(f"百度翻译错误: {e}")
        return translate_text_fallback(text, target_lang)

def translate_text_deepl(text, target_lang, api_key=None):
    """使用DeepL免费API翻译文本"""
    # DeepL免费API
    url = "https://api-free.deepl.com/v2/translate"
    
    # 语言代码映射
    language_mapping = {
        "en": "EN-US",  # 英语-美国
        "ja": "JA",     # 日语
        "ko": "KO",     # 韩语
        "fr": "FR",     # 法语
        "de": "DE",     # 德语
        "es": "ES"      # 西班牙语
    }
    
    # 如果没有映射，使用原始代码
    target_lang_code = language_mapping.get(target_lang, target_lang)
    
    payload = {
        "text": [text],
        "source_lang": "ZH",  # 假设原文是中文
        "target_lang": target_lang_code
    }
    
    # 如果没有提供API密钥，使用备用翻译方法
    if not api_key:
        print("未提供DeepL API密钥，使用备用翻译方法...")
        return translate_text_fallback(text, target_lang)
    
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['translations'][0]['text']
        else:
            print(f"DeepL翻译请求失败: {response.status_code}")
            # 使用备用翻译方法
            return translate_text_fallback(text, target_lang)
    except Exception as e:
        print(f"DeepL翻译错误: {e}")
        # 使用备用翻译方法
        return translate_text_fallback(text, target_lang)

def translate_text_fallback(text, target_lang):
    """备用翻译方法，不依赖外部API"""
    print("使用备用翻译方法...")
    
    # 这里实现一个简单的备用翻译
    # 实际可能需要使用更复杂的本地翻译库
    lang_greeting = {
        "en": f"[English Translation] {text}",
        "ja": f"[日本語翻訳] {text}",
        "ko": f"[한국어 번역] {text}",
        "fr": f"[Traduction française] {text}",
        "de": f"[Deutsche Übersetzung] {text}",
        "es": f"[Traducción española] {text}"
    }
    
    return lang_greeting.get(target_lang, f"[{target_lang}] {text}")

def translate_text_openai(text, api_key):
    """使用OpenAI API翻译文本"""
    if not api_key:
        return text
    
    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text to English. Translate the following text to English, maintaining the original meaning and style."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI API错误: {e}")
        return text

def translate_subtitles(subtitles, target_lang='en', api_choice='百度翻译 (免费)', api_key=None, secret_key=None):
    """翻译字幕"""
    translated_subs = pysrt.SubRipFile()
    
    for i, sub in enumerate(subtitles):
        # 创建新的字幕项
        new_sub = pysrt.SubRipItem()
        new_sub.index = sub.index
        new_sub.start = sub.start
        new_sub.end = sub.end
        
        # 翻译文本
        if api_choice == '百度翻译 (免费)':
            new_sub.text = translate_text_baidu(sub.text, target_lang, api_key, secret_key)
        else:  # ChatGPT
            new_sub.text = translate_text_openai(sub.text, api_key)
        
        translated_subs.append(new_sub)
    
    return translated_subs

def translate_text_content(text_content, target_lang='en', api_choice='百度翻译 (免费)', api_key=None, secret_key=None):
    """翻译纯文本内容"""
    # 将文本分成较小的段落进行翻译，以避免API限制
    max_length = 500  # 每段最大字符数
    paragraphs = []
    
    # 按句子分割文本
    sentences = []
    current = ""
    for char in text_content:
        current += char
        if char in ['.', '。', '!', '！', '?', '？', '\n']:
            if current.strip():
                sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
        
    # 将句子组合成段落
    current_paragraph = ""
    for sentence in sentences:
        if len(current_paragraph) + len(sentence) > max_length:
            paragraphs.append(current_paragraph)
            current_paragraph = sentence
        else:
            current_paragraph += " " + sentence if current_paragraph else sentence
    if current_paragraph:
        paragraphs.append(current_paragraph)
        
    # 翻译每个段落
    translated_paragraphs = []
    for paragraph in paragraphs:
        if api_choice == '百度翻译 (免费)':
            translated = translate_text_baidu(paragraph, target_lang, api_key, secret_key)
        else:  # ChatGPT
            translated = translate_text_openai(paragraph, api_key)
        translated_paragraphs.append(translated)
        
    # 合并翻译后的段落
    return "\n".join(translated_paragraphs)

def create_subtitles_from_text(text_content, output_dir, duration_per_char=0.2):
    """修复空文本和无效时间戳问题"""
    import pysrt
    
    # 添加空文本检查
    if not text_content.strip():
        raise ValueError("文本内容不能为空")
    
    # 按句子分割（增强鲁棒性）
    sentences = []
    current = ""
    for char in text_content:
        current += char
        # 更合理的分割条件：标点+长度限制
        if char in ['.', '。', '!', '！', '?', '？', '\n'] or len(current) >= 50:
            if current.strip():
                sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    
    # 添加句子有效性检查
    if len(sentences) == 0:
        raise ValueError("未检测到有效句子")
    
    # 计算总时长（防止除零错误）
    total_chars = sum(len(s) for s in sentences)
    total_duration = max(1.0, total_chars * duration_per_char)  # 确保最小1秒
    
    subtitles = pysrt.SubRipFile()
    time_per_sentence = total_duration / len(sentences)
    
    for i, sentence in enumerate(sentences):
        sub = pysrt.SubRipItem()
        sub.index = i + 1
        
        # 计算时间戳（增加边界检查）
        start_time = max(0.0, i * time_per_sentence)
        end_time = min(total_duration, (i + 1) * time_per_sentence)
        
        # 确保时间差至少0.5秒
        if end_time - start_time < 0.5:
            end_time = start_time + 0.5
        
        sub.start.seconds = start_time
        sub.end.seconds = end_time
        sub.text = sentence
        
        subtitles.append(sub)
    
    # 路径安全性检查
    output_path = os.path.abspath(os.path.join(output_dir, 'generated_subtitles.srt'))
    if not output_path.startswith(os.path.abspath(output_dir)):
        raise PermissionError("非法输出路径")
    
    subtitles.save(output_path, encoding='utf-8')
    return output_path, subtitles

def merge_subtitles(original_subs, translated_subs, output_dir, below_original=True):
    """合并原始字幕和翻译后的字幕"""
    merged_subs = pysrt.SubRipFile()
    
    if below_original:
        # 将翻译后的字幕放在原字幕下方
        for i, (orig_sub, trans_sub) in enumerate(zip(original_subs, translated_subs)):
            new_sub = pysrt.SubRipItem()
            new_sub.index = orig_sub.index
            new_sub.start = orig_sub.start
            new_sub.end = orig_sub.end
            
            # 合并原始文本和翻译文本
            new_sub.text = f"{orig_sub.text}\n{trans_sub.text}"
            
            merged_subs.append(new_sub)
    else:
        # 分开显示原字幕和翻译字幕
        merged_subs = original_subs + translated_subs
        
        # 调整索引
        for i, sub in enumerate(merged_subs):
            sub.index = i + 1
    
    # 保存合并后的字幕文件
    output_path = os.path.join(output_dir, 'merged_subtitles.srt')
    merged_subs.save(output_path, encoding='utf-8')
    
    return output_path 