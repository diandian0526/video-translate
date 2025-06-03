import os
import subprocess
import tempfile
import shutil

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

def process_video(video_path, output_path, subtitle_path):
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

        # 构建FFmpeg命令
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-y',
            '-i', safe_video_path,
            '-vf', f"subtitles='{safe_subtitle_path}'",
            '-c:v', 'libx264',
            '-preset', 'fast',  # 修正为完整的fast
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
        
        subprocess.run(cmd, check=True)
        
        return video_filename
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
        音频文件路径
    """
    try:
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
        
        return audio_path
    except subprocess.SubprocessError as e:
        print(f"提取音频失败: {e}")
        return None

def auto_generate_subtitles(video_path, output_dir):
    """
    为没有字幕的视频自动生成字幕
    使用whisper模型或vosk进行语音识别
    
    Args:
        video_path: 视频路径
        output_dir: 输出目录
    
    Returns:
        生成的字幕文件路径
    """
    try:
        # 提取音频
        audio_path = extract_audio(video_path, output_dir)
        if not audio_path:
            return None
            
        # 使用whisper命令行工具生成字幕
        subtitle_path = os.path.join(output_dir, "auto_generated.srt")
        
        # 假设已安装whisper
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
        print(f"自动生成字幕失败: {e}")
        return None

def generate_text_from_audio(audio_path, output_dir):
    """
    从音频生成纯文本（非字幕格式）
    使用whisper进行音频识别
    
    Args:
        audio_path: 音频文件路径
        output_dir: 输出目录
    
    Returns:
        生成的文本文件路径
    """
    try:
        text_path = os.path.join(output_dir, "audio_text.txt")
        
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
        print(f"生成文本失败: {e}")
        return None

def text_to_subtitles(text_content, output_dir, segment_duration=5):
    """
    将纯文本转换为字幕文件格式，根据指定的分段时间
    
    Args:
        text_content: 文本内容
        output_dir: 输出目录
        segment_duration: 每个字幕分段的持续时间（秒）
    
    Returns:
        生成的字幕文件路径
    """
    import pysrt
    from datetime import timedelta
    
    try:
        # 将文本按句子分割
        sentences = []
        current_sentence = ""
        
        for char in text_content:
            current_sentence += char
            if char in ['。', '!', '?', '！', '？', '.'] or len(current_sentence) > 20:
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence:
            sentences.append(current_sentence.strip())
        
        # 创建SRT文件
        subs = pysrt.SubRipFile()
        
        for i, sentence in enumerate(sentences):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            
            sub = pysrt.SubRipItem()
            sub.index = i + 1
            sub.start.seconds = start_time
            sub.end.seconds = end_time
            sub.text = sentence
            
            subs.append(sub)
        
        # 保存SRT文件
        output_path = os.path.join(output_dir, "generated_subtitles.srt")
        subs.save(output_path, encoding='utf-8')
        
        return output_path
    except Exception as e:
        print(f"文本转字幕失败: {e}")
        return None 