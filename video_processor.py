import os
import subprocess
import tempfile
import shutil
import json
import re

def convert_color_to_ass(color):
    """
    将颜色名称或十六进制颜色值转换为ASS格式的颜色代码
    ASS颜色格式: &HBBGGRR& (注意BGR顺序)
    
    Args:
        color: 颜色名称或十六进制值 (如 'white', 'black', '#FF0000')
    
    Returns:
        ASS格式的颜色代码
    """
    # 颜色名称映射
    color_map = {
        'white': '&HFFFFFF&',
        'black': '&H000000&',
        'red': '&H0000FF&',  # 注意BGR顺序
        'green': '&H00FF00&',
        'blue': '&HFF0000&',  # 注意BGR顺序
        'yellow': '&H00FFFF&',
        'cyan': '&HFFFF00&',
        'magenta': '&HFF00FF&',
        'gray': '&H808080&',
        'orange': '&H0080FF&',
    }
    
    # 如果是已知颜色名称，直接返回对应的ASS颜色代码
    if color.lower() in color_map:
        return color_map[color.lower()]
    
    # 如果是十六进制颜色代码，转换为ASS格式
    hex_pattern = r'^#?([0-9A-Fa-f]{6})$'
    match = re.match(hex_pattern, color)
    if match:
        hex_color = match.group(1)
        # 从RGB转换为BGR顺序
        r = hex_color[0:2]
        g = hex_color[2:4]
        b = hex_color[4:6]
        return f"&H{b}{g}{r}&"
    
    # 默认返回白色
    return '&HFFFFFF&'

def check_ffmpeg_available():
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            check=True
        )
        return "ffmpeg version" in result.stdout
    except Exception:
        return False

def process_video(video_path, output_path, subtitle_path, subtitle_style=None):
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # 验证文件存在
    if not all(os.path.exists(f) for f in [video_path, subtitle_path]):
        raise FileNotFoundError("输入文件不存在")

    try:
        # 统一使用正斜杠并正确转义路径
        safe_video_path = video_path.replace('\\', '/')
        safe_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
        safe_output_path = output_path.replace('\\', '/')

        # 默认字幕样式
        default_style = {
            'font': 'Arial',
            'fontsize': 22,
            'primary_color': '&HFFFFFF&',  # 白色，ASS格式
            'outline_color': '&H000000&',  # 黑色，ASS格式
            'outline_width': 1,
            'position': 'bottom',  # 'bottom' 或 'top'
            'margin_v': 30,        # 垂直边距
            'margin_h': 20,        # 水平边距
            'alignment': 2,        # 2=居中, 1=左对齐, 3=右对齐
            'bold': 0,             # 0=关闭, 1=开启
            'italic': 0,           # 0=关闭, 1=开启
        }

        # 如果提供了自定义样式，则更新默认样式
        if subtitle_style:
            # 特殊处理颜色值，确保使用ASS格式
            if 'primary_color' in subtitle_style:
                subtitle_style['primary_color'] = convert_color_to_ass(subtitle_style['primary_color'])
            if 'outline_color' in subtitle_style:
                subtitle_style['outline_color'] = convert_color_to_ass(subtitle_style['outline_color'])
                
            default_style.update(subtitle_style)

        # 构建ASS样式字符串
        style = default_style
        subtitle_filter = f"subtitles='{safe_subtitle_path}'"
        
        # 如果使用ASS字幕格式，可以添加更多样式选项
        subtitle_filter += f":force_style='"
        subtitle_filter += f"FontName={style['font']},"
        subtitle_filter += f"FontSize={style['fontsize']},"
        subtitle_filter += f"PrimaryColour={style['primary_color']},"
        subtitle_filter += f"OutlineColour={style['outline_color']},"
        subtitle_filter += f"BorderStyle=1,"  # 1=边框+阴影
        subtitle_filter += f"Outline={style['outline_width']},"
        subtitle_filter += f"Alignment={style['alignment']},"
        subtitle_filter += f"Bold={style['bold']},"
        subtitle_filter += f"Italic={style['italic']}"
        
        # 添加位置调整到 force_style 参数中
        if style['position'] == 'top':
            subtitle_filter += f",MarginV={style['margin_v']}"
        else:  # 默认底部
            subtitle_filter += f",MarginV={style['margin_v']}"
            
        # 水平位置调整
        if style['alignment'] == 1:  # 左对齐
            subtitle_filter += f",MarginL={style['margin_h']}"
        elif style['alignment'] == 3:  # 右对齐
            subtitle_filter += f",MarginR={style['margin_h']}"
        # 居中对齐不需要额外调整
        
        subtitle_filter += f"'"
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-y',
            '-i', safe_video_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'copy',
            safe_output_path
        ]

        # 打印完整命令用于调试
        print("完整执行命令:", ' '.join(cmd))

        # 执行命令
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"""
        FFmpeg执行失败！
        完整命令: {' '.join(cmd)}
        错误代码: {e.returncode}
        错误输出: {e.stderr}
        """
        raise RuntimeError(error_msg)

def download_video_from_url(url, output_dir):
    """
    从URL下载视频
    
    Args:
        url: 视频URL
        output_dir: 输出目录
    
    Returns:
        下载的视频路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 创建临时文件名
        video_filename = os.path.join(output_dir, "downloaded_video.mp4")
        
        # 检测是否是B站链接
        is_bilibili = "bilibili.com" in url or "b23.tv" in url
        
        # 使用yt-dlp下载视频（比youtube-dl更新更快）
        cmd = [
            'yt-dlp',
            url,
            '-o', video_filename,
            '--no-playlist',
            '--write-auto-sub',  # 自动写入字幕
            '--sub-format', 'srt',  # 字幕格式为SRT
            '--sub-lang', 'zh-CN',  # 优先选择中文字幕
            '--convert-subs', 'srt'  # 转换字幕为SRT格式
        ]
        
        # 对于B站视频，添加额外的参数
        if is_bilibili:
            cmd.extend([
                '--extractor-args', 'BiliBili:stream_types=["flv720","flv480","flv360"]',  # 指定可用的流类型
                '--ignore-errors',  # 忽略错误继续下载
            ])
        
        # 执行下载命令
        subprocess.run(cmd, check=True)
        
        # 检查下载的文件是否存在
        if not os.path.exists(video_filename):
            # 尝试查找可能的其他文件名（yt-dlp有时会添加格式ID）
            possible_files = [f for f in os.listdir(output_dir) if f.startswith("downloaded_video") and f.endswith(".mp4")]
            if possible_files:
                # 使用找到的第一个文件
                actual_filename = os.path.join(output_dir, possible_files[0])
                # 重命名为预期的文件名
                if actual_filename != video_filename:
                    shutil.move(actual_filename, video_filename)
        
        # 再次检查文件是否存在
        if os.path.exists(video_filename) and os.path.getsize(video_filename) > 0:
            return video_filename
        else:
            print(f"下载的视频文件不存在或为空: {video_filename}")
            return None
    except subprocess.SubprocessError as e:
        print(f"下载视频失败: {e}")
        return None

def extract_audio(video_path, output_dir):
    """
    从视频中提取音频
    
    Args:
        video_path: 视频路径
        output_dir: 输出目录
    
    Returns:
        音频文件路径，如果视频没有音频则返回None
    """
    try:
        # 首先检查视频文件是否包含音频流
        cmd_check = [
            'ffprobe', 
            '-v', 'error',
            '-select_streams', 'a', 
            '-show_entries', 'stream=index', 
            '-of', 'csv=p=0', 
            video_path
        ]
        
        result = subprocess.run(cmd_check, capture_output=True, text=True)
        
        # 如果没有音频流，返回None
        if not result.stdout.strip():
            print(f"警告: 视频 {video_path} 不包含音频流")
            return None
        
        audio_path = os.path.join(output_dir, "extracted_audio.wav")
        
        # 使用FFmpeg提取音频
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 禁用视频
            '-acodec', 'pcm_s16le',  # 音频编码
            '-ar', '16000',  # 采样率
            '-ac', '1',  # 单声道
            '-y',
            audio_path
        ]
        
        subprocess.run(cmd, check=True)
        
        # 检查生成的音频文件是否存在且大小大于0
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            return audio_path
        else:
            print(f"警告: 生成的音频文件 {audio_path} 不存在或为空")
            return None
            
    except subprocess.SubprocessError as e:
        print(f"提取音频失败: {e}")
        return None

def auto_generate_subtitles(video_path, output_dir):
    """
    为没有字幕的视频自动生成字幕
    使用whisper模型或备用方法进行语音识别
    
    Args:
        video_path: 视频路径
        output_dir: 输出目录
    
    Returns:
        生成的字幕文件路径
    """
    # 提取音频
    audio_path = extract_audio(video_path, output_dir)
    if not audio_path:
        return None
    
    subtitle_path = os.path.join(output_dir, "auto_generated.srt")
    
    # 检查whisper是否已安装
    whisper_installed = False
    try:
        # 尝试导入whisper模块
        import importlib
        importlib.import_module('whisper')
        whisper_installed = True
    except ImportError:
        pass
    
    # 检查whisper命令行工具是否可用
    if not whisper_installed:
        try:
            result = subprocess.run(['whisper', '--help'], capture_output=True, text=True)
            whisper_installed = 'usage: whisper' in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            whisper_installed = False
    
    if whisper_installed:
        try:
            # 使用whisper命令行工具生成字幕
            cmd = [
                'whisper',
                audio_path,
                '--model', 'tiny',  # 使用tiny模型，速度快但准确度低
                '--output_dir', output_dir,
                '--output_format', 'srt'
            ]
            
            subprocess.run(cmd, check=True)
            
            # Whisper输出的文件名可能不是我们期望的
            expected_output = os.path.join(output_dir, os.path.basename(audio_path).replace('.wav', '.srt'))
            if os.path.exists(expected_output):
                shutil.move(expected_output, subtitle_path)
                return subtitle_path
        except subprocess.SubprocessError as e:
            print(f"使用Whisper生成字幕失败: {e}")
            # 继续使用备用方法
    
    # 备用方法：创建一个简单的字幕文件
    try:
        print("Whisper未安装或不可用，使用备用方法生成简单字幕...")
        import pysrt
        
        # 获取视频时长
        cmd_info = [
            'ffprobe',
            '-v', 'error',
            '-show_format',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd_info, capture_output=True, text=True)
        video_info = json.loads(result.stdout) if result.stdout else {}
        
        # 尝试获取视频时长
        try:
            duration = float(video_info.get('format', {}).get('duration', '60'))
        except (ValueError, TypeError):
            duration = 60  # 默认1分钟
        
        # 创建简单的字幕文件
        subs = pysrt.SubRipFile()
        
        # 添加提示字幕
        sub = pysrt.SubRipItem()
        sub.index = 1
        sub.start.seconds = 0
        sub.end.seconds = min(10, duration / 3)
        sub.text = "由于未安装Whisper，无法自动生成字幕\n请在文本编辑页面手动输入内容"
        subs.append(sub)
        
        # 添加第二条提示
        if duration > 10:
            sub = pysrt.SubRipItem()
            sub.index = 2
            sub.start.seconds = duration / 3
            sub.end.seconds = 2 * duration / 3
            sub.text = "安装Whisper可实现自动字幕生成\n安装命令: pip install openai-whisper"
            subs.append(sub)
        
        # 添加第三条提示
        if duration > 20:
            sub = pysrt.SubRipItem()
            sub.index = 3
            sub.start.seconds = 2 * duration / 3
            sub.end.seconds = duration
            sub.text = "安装后重新运行程序\n即可自动生成字幕"
            subs.append(sub)
        
        # 保存字幕文件
        subs.save(subtitle_path, encoding='utf-8')
        return subtitle_path
    except Exception as e:
        print(f"生成备用字幕失败: {e}")
        return None

def generate_text_from_audio(audio_path, output_dir):
    """
    从音频生成纯文本（非字幕格式）
    使用whisper进行音频识别，如果whisper未安装则使用简单的备用方法
    
    Args:
        audio_path: 音频文件路径
        output_dir: 输出目录
    
    Returns:
        生成的文本文件路径
    """
    text_path = os.path.join(output_dir, "audio_text.txt")
    
    # 检查whisper是否已安装
    whisper_installed = False
    try:
        # 尝试导入whisper模块
        import importlib
        importlib.import_module('whisper')
        whisper_installed = True
    except ImportError:
        pass
    
    # 检查whisper命令行工具是否可用
    if not whisper_installed:
        try:
            result = subprocess.run(['whisper', '--help'], capture_output=True, text=True)
            whisper_installed = 'usage: whisper' in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            whisper_installed = False
    
    if whisper_installed:
        try:
            # 使用whisper命令行工具生成文本
            cmd = [
                'whisper',
                audio_path,
                '--model', 'base',  # 使用base模型，平衡速度和准确度
                '--output_dir', output_dir,
                '--output_format', 'txt'
            ]
            
            subprocess.run(cmd, check=True)
            
            # Whisper输出的文件名可能不是我们期望的
            expected_output = os.path.join(output_dir, os.path.basename(audio_path).replace('.wav', '.txt'))
            if os.path.exists(expected_output):
                shutil.move(expected_output, text_path)
                return text_path
        except subprocess.SubprocessError as e:
            print(f"使用Whisper生成文本失败: {e}")
            # 继续使用备用方法
    
    # 备用方法：使用FFmpeg从音频中提取基本信息
    try:
        print("Whisper未安装或不可用，使用备用方法生成简单文本...")
        
        # 获取音频文件信息
        cmd_info = [
            'ffprobe',
            '-v', 'error',
            '-show_format',
            '-show_streams',
            '-of', 'json',
            audio_path
        ]
        
        result = subprocess.run(cmd_info, capture_output=True, text=True)
        audio_info = json.loads(result.stdout) if result.stdout else {}
        
        # 生成简单的文本内容
        content = [
            "音频文件信息摘要（请手动输入文本内容）:",
            "--------------------------------",
            f"文件名: {os.path.basename(audio_path)}",
            f"时长: {audio_info.get('format', {}).get('duration', '未知')} 秒",
        ]
        
        if 'streams' in audio_info:
            for i, stream in enumerate(audio_info['streams']):
                content.append(f"音轨 {i+1}: {stream.get('codec_name', '未知')} {stream.get('sample_rate', '')}Hz")
        
        content.extend([
            "--------------------------------",
            "注意: 由于未安装Whisper语音识别工具，无法自动生成文本。",
            "请在下方手动输入音频内容，或安装Whisper后重试。",
            "安装命令: pip install openai-whisper"
        ])
        
        # 保存到文本文件
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return text_path
    except Exception as e:
        print(f"生成文本失败: {e}")
        
        # 最后的备用方案：创建一个空白文本文件
        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("请在此处输入音频内容。\n\n注意: 自动语音识别失败，请手动输入内容。")
            return text_path
        except:
            return None

def text_to_subtitles(text_content, output_dir, segment_duration=5):
    """
    将纯文本转换为字幕文件格式，使用更智能的分段方法
    
    Args:
        text_content: 文本内容
        output_dir: 输出目录
        segment_duration: 每个字符的基础持续时间（秒）
    
    Returns:
        生成的字幕文件路径
    """
    import pysrt
    import re
    
    try:
        # 使用更智能的句子分割方法
        sentences = []
        # 按标点符号和自然段落分割
        pattern = r'([^。！？.!?\n]+[。！？.!?\n])'
        raw_sentences = re.findall(pattern, text_content)
        
        # 处理分割后的句子，避免过长句子
        for raw_sentence in raw_sentences:
            # 去除首尾空白
            cleaned = raw_sentence.strip()
            if not cleaned:
                continue
                
            # 如果句子太长，进一步分割
            if len(cleaned) > 40:
                # 按逗号、分号等次要标点分割
                sub_pattern = r'([^，,；;、]+[，,；;、])'
                sub_sentences = re.findall(sub_pattern, cleaned)
                
                # 如果能分割，就添加分割后的子句
                if sub_sentences:
                    for sub in sub_sentences:
                        if sub.strip():
                            sentences.append(sub.strip())
                    
                    # 检查是否有剩余部分
                    last_part = re.sub(r'.*[，,；;、]', '', cleaned).strip()
                    if last_part:
                        sentences.append(last_part)
                else:
                    # 如果无法按次要标点分割，则按固定长度分割
                    for i in range(0, len(cleaned), 30):
                        part = cleaned[i:i+30].strip()
                        if part:
                            sentences.append(part)
            else:
                sentences.append(cleaned)
        
        # 如果没有有效句子，使用原始方法分割
        if not sentences:
            # 备用分割方法
            current_sentence = ""
            for char in text_content:
                current_sentence += char
                if char in ['。', '!', '?', '！', '？', '.', '\n'] or len(current_sentence) > 30:
                    if current_sentence.strip():
                        sentences.append(current_sentence.strip())
                    current_sentence = ""
            
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
        
        # 创建SRT文件
        subs = pysrt.SubRipFile()
        
        # 动态计算每个句子的时长
        current_time = 0.0
        for i, sentence in enumerate(sentences):
            sub = pysrt.SubRipItem()
            sub.index = i + 1
            
            # 根据句子长度和复杂度计算时长
            char_count = len(sentence)
            base_duration = char_count * 0.2  # 每个字符约0.2秒
            
            # 根据句子结束的标点符号调整时长
            if sentence.endswith(('。', '.', '!', '！', '?', '？')):
                pause_time = 0.5  # 句号等停顿较长
            elif sentence.endswith(('，', ',', '、', '；', ';')):
                pause_time = 0.3  # 逗号等停顿较短
            else:
                pause_time = 0.2  # 无明显标点的默认停顿
            
            # 最终时长 = 基础时长 + 停顿时间，确保最小时长
            sentence_duration = max(1.0, base_duration + pause_time)
            
            # 设置时间戳
            start_seconds = current_time
            end_seconds = current_time + sentence_duration
            
            # 更新当前时间
            current_time = end_seconds
            
            # 转换为时间对象
            sub.start.seconds = start_seconds
            sub.end.seconds = end_seconds
            sub.text = sentence
            
            subs.append(sub)
        
        # 保存SRT文件
        output_path = os.path.join(output_dir, "generated_subtitles.srt")
        subs.save(output_path, encoding='utf-8')
        
        return output_path
    except Exception as e:
        print(f"文本转字幕失败: {e}")
        return None