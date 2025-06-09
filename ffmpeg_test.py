import os
import subprocess
import sys

def test_ffmpeg_subtitles(video_path, subtitle_path, output_path):
    """
    测试ffmpeg添加字幕功能
    """
    print(f"测试参数:")
    print(f"- 视频路径: {video_path}")
    print(f"- 字幕路径: {subtitle_path}")
    print(f"- 输出路径: {output_path}")
    
    # 检查文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在 - {video_path}")
        return False
    if not os.path.exists(subtitle_path):
        print(f"错误: 字幕文件不存在 - {subtitle_path}")
        return False
        
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 测试方法1：使用ffmpeg子进程参数列表
    try:
        print("\n方法1: 使用参数列表")
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-y',
            '-i', video_path,
            '-vf', f'subtitles={subtitle_path}',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'copy',
            output_path + "_method1.mp4"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("方法1成功!")
    except Exception as e:
        print(f"方法1失败: {e}")
    
    # 测试方法2：使用shell命令字符串
    try:
        print("\n方法2: 使用shell命令字符串")
        
        # 路径处理
        video_path_esc = video_path.replace('\\', '/')
        subtitle_path_esc = subtitle_path.replace('\\', '/')
        output_path_esc = output_path.replace('\\', '/') + "_method2.mp4"
        
        cmd_str = (
            f'ffmpeg -hide_banner -y -i "{video_path_esc}" '
            f'-vf "subtitles={subtitle_path_esc}" '
            f'-c:v libx264 -preset fast -c:a copy "{output_path_esc}"'
        )
        
        print(f"执行命令: {cmd_str}")
        
        result = subprocess.run(
            cmd_str,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("方法2成功!")
    except Exception as e:
        print(f"方法2失败: {e}")
    
    # 测试方法3：使用工作目录
    try:
        print("\n方法3: 切换工作目录")
        
        subtitle_dir = os.path.dirname(subtitle_path)
        subtitle_filename = os.path.basename(subtitle_path)
        current_dir = os.getcwd()
        
        os.chdir(subtitle_dir)
        
        cmd_str = (
            f'ffmpeg -hide_banner -y -i "{video_path_esc}" '
            f'-vf "subtitles={subtitle_filename}" '
            f'-c:v libx264 -preset fast -c:a copy "{output_path_esc}_method3.mp4"'
        )
        
        print(f"执行命令(工作目录 {subtitle_dir}): {cmd_str}")
        
        result = subprocess.run(
            cmd_str,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        os.chdir(current_dir)
        print("方法3成功!")
    except Exception as e:
        print(f"方法3失败: {e}")
        os.chdir(current_dir)
    
    # 测试方法4：尝试直接用cmd.exe
    try:
        print("\n方法4: 使用cmd.exe")
        
        cmd_bat = (
            f'@echo off\n'
            f'cd /d "{subtitle_dir}"\n'
            f'ffmpeg -hide_banner -y -i "{video_path_esc}" '
            f'-vf "subtitles={subtitle_filename}" '
            f'-c:v libx264 -preset fast -c:a copy "{output_path_esc}_method4.mp4"\n'
        )
        
        batch_file = os.path.join(os.path.dirname(output_path), "ffmpeg_test.bat") 
        with open(batch_file, "w") as f:
            f.write(cmd_bat)
            
        print(f"执行批处理: {batch_file}")
        
        result = subprocess.run(
            f'cmd.exe /c "{batch_file}"',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("方法4成功!")
    except Exception as e:
        print(f"方法4失败: {e}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python ffmpeg_test.py <视频路径> <字幕路径> [输出路径]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    
    if len(sys.argv) >= 4:
        output_path = sys.argv[3]
    else:
        output_path = os.path.join(os.path.dirname(video_path), "test_output")
        
    test_ffmpeg_subtitles(video_path, subtitle_path, output_path) 