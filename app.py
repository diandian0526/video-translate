import streamlit as st
import os
import tempfile
import shutil
import pysrt
from subtitle_processor import extract_subtitles, translate_subtitles, merge_subtitles
from subtitle_processor import read_text_file, save_text_file, translate_text_content, create_subtitles_from_text
from video_processor import process_video, download_video_from_url, auto_generate_subtitles
from video_processor import extract_audio, generate_text_from_audio
import subprocess
import traceback
import json

def main():
    st.set_page_config(page_title="视频字幕翻译工具", layout="wide")
    
    # 添加自定义CSS，全面优化界面设计
    st.markdown("""
    <style>
    /* 全局样式重置与基础设置 */
    * {
        box-sizing: border-box;
        transition: all 0.2s ease;
    }
    
    /* 整体页面样式 - 使用柔和的渐变背景 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
        color: #333;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 左侧边栏背景 - 深色主题 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #1a252f 100%);
        border-radius: 0;
        padding: 20px 10px;
        box-shadow: 2px 0px 10px rgba(0,0,0,0.2);
    }
    
    /* 左侧边栏文字颜色 - 全面增强所有文本元素的颜色 */
    section[data-testid="stSidebar"] .block-container {
        color: #ffffff !important;
    }
    
    /* 左侧边栏所有文本元素 */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: #ffffff !important;
    }
    
    /* 左侧边栏输入框文本 */
    section[data-testid="stSidebar"] input, 
    section[data-testid="stSidebar"] .stTextInput input {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* 输出视频路径显示框样式特殊定制 */
    section[data-testid="stSidebar"] .stTextInput input[aria-label="输出视频保存路径"] {
        color: #1E90FF !important;
        background-color: rgba(255, 255, 255, 0.25) !important;
        font-weight: 500;
        border-color: rgba(70, 130, 180, 0.5) !important;
        border-width: 2px;
    }
    
    /* 左侧边栏下拉菜单 */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* 左侧边栏复选框和单选按钮 */
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stRadio label {
        font-weight: 400;
    }
    
    /* 左侧边栏标题 */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #ffffff;
        font-weight: 600;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 15px;
    }
    
    /* 左侧边栏标签文字 */
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* 左侧边栏警告框文字 */
    section[data-testid="stSidebar"] .stAlert {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 左侧边栏信息框 */
    section[data-testid="stSidebar"] .element-container div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    /* 右侧主区域背景 */
    .main .block-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
        margin: 20px;
    }
    
    /* 标签页设计 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 0 10px;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4682B4;
        color: white;
        font-weight: 600;
    }
    
    /* 标签页内容区域 */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border-radius: 0 8px 8px 8px;
        padding: 20px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* 标题样式 */
    h1 {
        color: #2C3E50;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 30px;
        text-align: center;
        background: linear-gradient(90deg, #4682B4, #5F9EA0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    h2, h3 {
        color: #2C3E50;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    
    /* 按钮样式 */
    .stButton>button {
        background: linear-gradient(90deg, #4682B4, #5F9EA0);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background: linear-gradient(90deg, #5F9EA0, #4682B4);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* 输入框样式 */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 12px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #4682B4;
        box-shadow: 0 0 0 2px rgba(70, 130, 180, 0.2);
    }
    
    /* 选择框样式 */
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* 文件上传区域 */
    .stFileUploader>div>button {
        background: linear-gradient(90deg, #4682B4, #5F9EA0);
        color: white;
        border-radius: 8px;
    }
    
    .stFileUploader>div>button:hover {
        background: linear-gradient(90deg, #5F9EA0, #4682B4);
    }
    
    /* 进度条样式 */
    .stProgress>div>div>div {
        background-color: #4682B4;
    }
    
    /* 信息框样式 */
    .stAlert {
        border-radius: 8px;
        padding: 15px;
    }
    
    /* 成功信息框 */
    .element-container div[data-stale="false"] div[data-testid="stImage"] + div[data-testid="stMarkdownContainer"] p {
        background-color: rgba(25, 135, 84, 0.1);
        border-left: 4px solid #198754;
        padding: 15px;
        border-radius: 4px;
    }
    
    /* 警告信息框 */
    .element-container div[data-stale="false"] div[data-testid="stImage"] + div[data-testid="stMarkdownContainer"] p {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 15px;
        border-radius: 4px;
    }
    
    /* 错误信息框 */
    .element-container div[data-stale="false"] div[data-testid="stImage"] + div[data-testid="stMarkdownContainer"] p {
        background-color: rgba(220, 53, 69, 0.1);
        border-left: 4px solid #dc3545;
        padding: 15px;
        border-radius: 4px;
    }
    
    /* 完全隐藏顶部导航栏 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 添加团队Logo样式 */
    .team-logo {
        position: absolute;
        top: 20px;
        right: 40px;
        font-size: 1rem;
        font-weight: 600;
        color: #2C3E50;
        background: rgba(255, 255, 255, 0.95);
        padding: 10px 15px;
        border-radius: 8px;
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.08);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
        border: 1px solid rgba(70, 130, 180, 0.2);
        backdrop-filter: blur(5px);
    }
    
    .team-logo svg {
        flex-shrink: 0;
    }
    
    .logo-text {
        font-family: 'Arial', sans-serif;
        letter-spacing: 0.5px;
        font-weight: 700;
        background: linear-gradient(90deg, #2C3E50, #4682B4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-right: 2px;
    }
    
    .tm {
        font-size: 0.6rem;
        vertical-align: super;
        font-weight: 400;
        margin-left: 1px;
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 20px;
            margin: 10px;
        }
        
        h1 {
            font-size: 1.8rem;
        }
        
        .team-logo {
            top: 10px;
            right: 15px;
            padding: 6px 10px;
        }
        
        .team-logo svg {
            width: 18px;
            height: 18px;
        }
        
        .logo-text {
            font-size: 0.85rem;
        }
        
        .tm {
            font-size: 0.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 添加团队Logo到右上角
    st.markdown("""
    <div class="team-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#4682B4" stroke="#2C3E50" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="5" fill="#5F9EA0" stroke="#2C3E50" stroke-width="1"/>
        </svg>
        <span class="logo-text">译心译意团队<span class="tm">™</span></span>
    </div>
    """, unsafe_allow_html=True)
    
    # 创建.streamlit目录和config.toml文件（如果不存在）
    config_dir = ".streamlit"
    config_path = os.path.join(config_dir, "config.toml")
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write("""
[theme]
primaryColor = "#4682B4"
backgroundColor = "#f5f7fa"
secondaryBackgroundColor = "#ffffff"
textColor = "#333333"
font = "sans serif"
            """)
    
    st.title("视频字幕翻译工具")
    
    # 初始化会话状态变量
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None
    if 'text_path' not in st.session_state:
        st.session_state.text_path = None
    if 'text_content' not in st.session_state:
        st.session_state.text_content = ""
    if 'edited_content' not in st.session_state:
        st.session_state.edited_content = ""
    if 'translated_content' not in st.session_state:
        st.session_state.translated_content = ""
    if 'video_path' not in st.session_state:
        st.session_state.video_path = None
    if 'temp_dir' not in st.session_state:
        # 创建固定临时目录
        temp_dir = r'C:\Temp\video'
        os.makedirs(temp_dir, exist_ok=True)
        st.session_state.temp_dir = temp_dir
    
    # 用于存储API密钥的文件路径
    api_keys_file = os.path.join(st.session_state.temp_dir, "api_keys.json")
    
    # 初始化API密钥存储
    if 'api_keys' not in st.session_state:
        # 尝试从文件加载保存的API密钥
        if os.path.exists(api_keys_file):
            try:
                with open(api_keys_file, 'r', encoding='utf-8') as f:
                    st.session_state.api_keys = json.load(f)
            except Exception as e:
                st.session_state.api_keys = {
                    "baidu_appid": "",
                    "baidu_secret_key": "",
                    "openai_api_key": ""
                }
                print(f"加载API密钥文件失败: {e}")
        else:
            st.session_state.api_keys = {
                "baidu_appid": "",
                "baidu_secret_key": "",
                "openai_api_key": ""
            }
    
    # 保存API密钥到文件的函数
    def save_api_keys():
        try:
            with open(api_keys_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.api_keys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存API密钥失败: {e}")
    
    # 侧边栏-参数设置
    with st.sidebar:
        st.header("参数设置")
        target_language = st.selectbox(
            "选择目标翻译语言",
            options=["中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语"],
            index=0
        )
        
        language_code = {
            "中文": "zh",
            "英语": "en",
            "日语": "ja",
            "韩语": "ko",
            "法语": "fr",
            "德语": "de",
            "西班牙语": "es"
        }
        
        subtitle_position = st.radio(
            "字幕位置",
            options=["原字幕下方", "单独轨道"],
            index=0
        )
        
        api_choice = st.radio(
            "选择翻译API",
            options=["百度翻译 (免费)", "ChatGPT (需自备API密钥)"],
            index=0
        )
        
        if api_choice == "百度翻译 (免费)":
            # 显示已保存的百度API密钥（如果有）
            saved_baidu_appid = st.session_state.api_keys.get("baidu_appid", "")
            saved_baidu_secret = st.session_state.api_keys.get("baidu_secret_key", "")
            
            # 显示保存状态
            if saved_baidu_appid and saved_baidu_secret:
                st.success("已保存百度翻译API密钥")
                show_saved = st.checkbox("使用已保存的密钥", value=True)
                
                if show_saved:
                    # 使用已保存的密钥
                    baidu_appid = saved_baidu_appid
                    baidu_secret_key = saved_baidu_secret
                    
                    # 显示重新输入选项
                    if st.button("重新输入API密钥"):
                        show_saved = False
                else:
                    # 重新输入密钥
                    baidu_appid = st.text_input("百度翻译APP ID", type="password", help="如需使用百度翻译API，请输入APP ID")
                    baidu_secret_key = st.text_input("百度翻译密钥", type="password", help="请输入百度翻译密钥")
                    
                    # 保存新输入的密钥
                    if baidu_appid and baidu_secret_key and (baidu_appid != saved_baidu_appid or baidu_secret_key != saved_baidu_secret):
                        st.session_state.api_keys["baidu_appid"] = baidu_appid
                        st.session_state.api_keys["baidu_secret_key"] = baidu_secret_key
                        save_api_keys()
                        st.success("API密钥已保存")
            else:
                # 首次输入密钥
                baidu_appid = st.text_input("百度翻译APP ID", type="password", help="如需使用百度翻译API，请输入APP ID")
                baidu_secret_key = st.text_input("百度翻译密钥", type="password", help="请输入百度翻译密钥")
                
                # 保存新输入的密钥
                if baidu_appid and baidu_secret_key:
                    save_key = st.checkbox("保存密钥供下次使用", value=True)
                    if save_key:
                        st.session_state.api_keys["baidu_appid"] = baidu_appid
                        st.session_state.api_keys["baidu_secret_key"] = baidu_secret_key
                        save_api_keys()
                        st.success("API密钥已保存")
            
            openai_api_key = None
            
            if not baidu_appid or not baidu_secret_key:
                st.warning("请填写百度翻译APP ID和密钥")
                st.info("您可以在百度翻译开放平台获取API密钥，并确保将您的IP添加到白名单中")
        elif api_choice == "ChatGPT (需自备API密钥)":
            # 显示已保存的OpenAI API密钥（如果有）
            saved_openai_key = st.session_state.api_keys.get("openai_api_key", "")
            
            # 显示保存状态
            if saved_openai_key:
                st.success("已保存OpenAI API密钥")
                show_saved = st.checkbox("使用已保存的密钥", value=True)
                
                if show_saved:
                    # 使用已保存的密钥
                    openai_api_key = saved_openai_key
                    
                    # 显示重新输入选项
                    if st.button("重新输入API密钥"):
                        show_saved = False
                else:
                    # 重新输入密钥
                    openai_api_key = st.text_input("OpenAI API密钥", type="password")
                    
                    # 保存新输入的密钥
                    if openai_api_key and openai_api_key != saved_openai_key:
                        st.session_state.api_keys["openai_api_key"] = openai_api_key
                        save_api_keys()
                        st.success("API密钥已保存")
            else:
                # 首次输入密钥
                openai_api_key = st.text_input("OpenAI API密钥", type="password")
                
                # 保存新输入的密钥
                if openai_api_key:
                    save_key = st.checkbox("保存密钥供下次使用", value=True)
                    if save_key:
                        st.session_state.api_keys["openai_api_key"] = openai_api_key
                        save_api_keys()
                        st.success("API密钥已保存")
            
            baidu_appid = None
            baidu_secret_key = None
        
        # 添加字幕样式设置折叠面板
        with st.expander("字幕样式设置", expanded=False):
            # 字体选择
            font_options = ["Arial", "SimHei", "Microsoft YaHei", "SimSun", "KaiTi", "FangSong", "Times New Roman"]
            font = st.selectbox("字体", options=font_options, index=0)
            
            # 字体大小
            fontsize = st.slider("字体大小", min_value=12, max_value=48, value=24, step=2)
            
            # 字体颜色
            primary_color_options = {
                "白色": "white", 
                "黑色": "black", 
                "黄色": "yellow", 
                "红色": "red", 
                "蓝色": "blue", 
                "绿色": "green",
                "粉色": "pink"
            }
            primary_color_display = st.selectbox("字体颜色", options=list(primary_color_options.keys()), index=0)
            primary_color = primary_color_options[primary_color_display]
            
            # 轮廓颜色
            outline_color_options = {
                "黑色": "black", 
                "白色": "white", 
                "黄色": "yellow", 
                "红色": "red", 
                "蓝色": "blue", 
                "绿色": "green",
                "透明": "transparent"
            }
            outline_color_display = st.selectbox("轮廓颜色", options=list(outline_color_options.keys()), index=0)
            outline_color = outline_color_options[outline_color_display]
            
            # 轮廓宽度
            outline_width = st.slider("轮廓宽度", min_value=0, max_value=4, value=2, step=1)
            
            # 位置
            position = st.radio("字幕位置", options=["底部", "顶部"], index=0)
            position_value = "bottom" if position == "底部" else "top"
            
            # 垂直边距
            margin_v = st.slider("垂直边距", min_value=10, max_value=100, value=30, step=5)
            
            # 水平边距
            margin_h = st.slider("水平边距", min_value=10, max_value=100, value=20, step=5)
            
            # 对齐方式
            alignment_options = {"居中对齐": 2, "左对齐": 1, "右对齐": 3}
            alignment_display = st.radio("对齐方式", options=list(alignment_options.keys()), index=0, horizontal=True)
            alignment = alignment_options[alignment_display]
            
            # 粗体和斜体
            col1, col2 = st.columns(2)
            with col1:
                bold = 1 if st.checkbox("粗体", value=False) else 0
            with col2:
                italic = 1 if st.checkbox("斜体", value=False) else 0
            
            # 创建字幕样式字典
            subtitle_style = {
                'font': font,
                'fontsize': fontsize,
                'primary_color': primary_color,
                'outline_color': outline_color,
                'outline_width': outline_width,
                'position': position_value,
                'margin_v': margin_v,
                'margin_h': margin_h,
                'alignment': alignment,
                'bold': bold,
                'italic': italic
            }
        
        auto_subtitle = st.checkbox("如无字幕，自动生成（需安装Whisper）", value=True)
        
        output_path = st.text_input("输出视频保存路径", value=r"C:\Temp\video\output")
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
                st.success(f"已创建输出目录: {output_path}")
            except Exception as e:
                st.error(f"创建输出目录失败: {e}")
    
    # 主区域-上传和处理
    tabs = st.tabs(["📤 本地上传",
                    "🌐 URL链接",
                    "🎵 音频处理",
                    "✏ 文本编辑",
                    "🌍 翻译结果",
                    "🎬 视频生成"])
    
    with tabs[0]:  # 本地上传
        uploaded_file = st.file_uploader("上传视频文件", type=["mp4", "avi", "mkv", "mov"])
        
        if uploaded_file:
            # 创建临时文件保存上传的视频
            temp_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.video_path = temp_path
            st.video(temp_path)
            
            # 添加一个处理视频按钮
            if st.button("一键生成视频"):
                # 调用process_uploaded_video函数，传递字幕样式参数
                process_uploaded_video(
                    st.session_state.video_path,
                    st.session_state.temp_dir,
                    language_code[target_language],
                    api_choice,
                    baidu_appid if api_choice == "百度翻译 (免费)" else openai_api_key,
                    baidu_secret_key if api_choice == "百度翻译 (免费)" else None,  # 传递secret_key
                    subtitle_position == "原字幕下方",
                    auto_subtitle,
                    subtitle_style  # 传递字幕样式
                )
            
            if st.button("开始提取音频"):
                with st.spinner("正在提取音频..."):
                    st.session_state.audio_path = extract_audio(temp_path, st.session_state.temp_dir)
                    if st.session_state.audio_path:
                        st.success("音频提取成功!")
                        st.audio(st.session_state.audio_path)
                    else:
                        st.error("音频提取失败")
    
    with tabs[1]:  # URL链接
        video_url = st.text_input("输入视频URL")
        
        # 添加会话状态变量，用于存储URL和下载状态
        if 'url_video_downloaded' not in st.session_state:
            st.session_state.url_video_downloaded = False
        if 'last_video_url' not in st.session_state:
            st.session_state.last_video_url = ""
        
        # 检查是否已经下载过视频，避免重复下载
        if video_url and video_url != st.session_state.last_video_url:
            st.session_state.url_video_downloaded = False
        
        download_button = st.button("从URL下载视频")
        
        # 如果点击下载按钮或已经下载过视频
        if (video_url and download_button) or (video_url and st.session_state.url_video_downloaded and video_url == st.session_state.last_video_url):
            if not st.session_state.url_video_downloaded:
                with st.spinner("下载并处理URL视频中..."):
                    # 下载视频
                    video_path = download_video_from_url(video_url, st.session_state.temp_dir)
                    
                    if video_path:
                        st.session_state.video_path = video_path
                        st.session_state.url_video_downloaded = True
                        st.session_state.last_video_url = video_url
                        st.success("视频下载成功!")
                    else:
                        st.error("视频下载失败，请检查URL或尝试其他视频")
            
            # 如果视频已下载成功，显示视频
            if st.session_state.url_video_downloaded and st.session_state.video_path:
                st.video(st.session_state.video_path)
                
                # 添加处理视频按钮
                if st.button("一键生成视频", key="process_url_video"):
                    # 调用process_uploaded_video函数，传递字幕样式参数
                    process_uploaded_video(
                        st.session_state.video_path,
                        st.session_state.temp_dir,
                        language_code[target_language],
                        api_choice,
                        baidu_appid if api_choice == "百度翻译 (免费)" else openai_api_key,
                        baidu_secret_key if api_choice == "百度翻译 (免费)" else None,  # 传递secret_key
                        subtitle_position == "原字幕下方",
                        auto_subtitle,
                        subtitle_style  # 传递字幕样式
                    )
                
                # 添加提取音频按钮
                extract_button = st.button("开始提取音频", key="extract_url_audio")
                
                if extract_button:
                    with st.spinner("正在提取音频..."):
                        st.session_state.audio_path = extract_audio(st.session_state.video_path, st.session_state.temp_dir)
                        if st.session_state.audio_path:
                            st.success("音频提取成功!")
                            st.audio(st.session_state.audio_path)
                        else:
                            st.error("音频提取失败，可能是视频没有音轨或格式不支持")
                
                # 如果已经提取了音频，显示音频
                if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
                    st.success("音频已提取")
                    st.audio(st.session_state.audio_path)
    
    with tabs[2]:  # 音频处理
        st.subheader("音频处理")
        
        if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
            st.audio(st.session_state.audio_path)
            
            # 检查whisper是否已安装
            whisper_installed = False
            try:
                # 尝试导入whisper模块
                import importlib.util
                if importlib.util.find_spec('whisper') is not None:
                    whisper_installed = True
            except ImportError:
                pass
            
            if not whisper_installed:
                st.warning("未检测到Whisper语音识别库，将使用备用方法处理音频。为获得更好的结果，建议安装Whisper：")
                st.code("pip install openai-whisper")
                if st.button("了解更多关于Whisper"):
                    st.markdown("""
                    ### 关于Whisper
                    
                    Whisper是OpenAI开发的强大语音识别系统，可以将音频转换为文本。它支持多种语言，识别准确率高。
                    
                    #### 安装要求:
                    - Python 3.8+
                    - PyTorch 1.10.0+
                    - FFmpeg
                    
                    #### 安装命令:
                    ```
                    pip install openai-whisper
                    ```
                    
                    安装后重新运行程序，即可使用Whisper自动生成高质量文本。
                    """)
            
            if st.button("从音频生成文本"):
                with st.spinner("正在生成文本，这可能需要一些时间..."):
                    st.session_state.text_path = generate_text_from_audio(st.session_state.audio_path, st.session_state.temp_dir)
                    if st.session_state.text_path and os.path.exists(st.session_state.text_path):
                        st.session_state.text_content = read_text_file(st.session_state.text_path)
                        st.session_state.edited_content = st.session_state.text_content
                        st.success("文本生成成功!")
                        
                        # 如果文本中包含提示信息，说明使用了备用方法
                        if "由于未安装Whisper" in st.session_state.text_content or "请手动输入" in st.session_state.text_content:
                            st.info("由于未安装Whisper，生成的是基本信息模板。请在文本编辑页面手动输入音频内容。")
                    else:
                        st.error("文本生成失败")
        else:
            st.info("请先在\"本地上传\"或\"URL链接\"标签页上传视频并提取音频")
    
    with tabs[3]:  # 文本编辑
        st.subheader("文本编辑")
        
        if st.session_state.text_content:
            st.session_state.edited_content = st.text_area("编辑识别的文本", st.session_state.edited_content, height=400)
            
            if st.button("保存编辑后的文本"):
                edited_text_path = os.path.join(st.session_state.temp_dir, "edited_text.txt")
                if save_text_file(edited_text_path, st.session_state.edited_content):
                    st.success("文本保存成功!")
                else:
                    st.error("文本保存失败")
        else:
            st.info("请先在\"音频处理\"标签页生成文本")
    
    with tabs[4]:  # 翻译结果
        st.subheader("翻译结果")
        
        if st.session_state.edited_content:
            # 如果选择了百度翻译API，但没有提供API密钥，则显示提示
            if api_choice == "百度翻译 (免费)" and (not baidu_appid or not baidu_secret_key):
                st.warning("请在侧边栏填写百度翻译APP ID和密钥后继续")
            
            if st.button("翻译编辑后的文本"):
                with st.spinner("正在翻译文本..."):
                    # 使用正确的API密钥
                    if api_choice == "百度翻译 (免费)":
                        if not baidu_appid or not baidu_secret_key:
                            st.error("请先在侧边栏填写百度翻译APP ID和密钥")
                            return
                            
                        st.session_state.translated_content = translate_text_content(
                            st.session_state.edited_content,
                            target_lang=language_code[target_language],
                            api_choice=api_choice,
                            api_key=baidu_appid,
                            secret_key=baidu_secret_key
                        )
                    else:
                        if not openai_api_key:
                            st.error("请先在侧边栏填写OpenAI API密钥")
                            return
                            
                        st.session_state.translated_content = translate_text_content(
                            st.session_state.edited_content,
                            target_lang=language_code[target_language],
                            api_choice=api_choice,
                            api_key=openai_api_key
                        )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 原文")
                st.text_area("原文内容", st.session_state.edited_content, height=300, disabled=True)
            
            with col2:
                st.markdown("##### 翻译结果")
                st.session_state.translated_content = st.text_area(
                    "翻译内容", 
                    st.session_state.translated_content, 
                    height=300
                )
        else:
            st.info("请先在\"文本编辑\"标签页编辑文本")
    
    with tabs[5]:  # 视频生成
        st.subheader("视频生成")
        
        if st.session_state.video_path and st.session_state.edited_content and st.session_state.translated_content:
            
            # 添加字幕样式预览
            st.markdown("### 字幕样式预览")
            
            # 创建预览样式的HTML
            preview_style = f"""
            <div style="padding: 10px; background-color: rgba(0,0,0,0.7); border-radius: 5px; margin-bottom: 20px;">
                <p style="
                    font-family: {subtitle_style['font']};
                    font-size: {subtitle_style['fontsize']}px;
                    color: {subtitle_style['primary_color']};
                    text-shadow: 0px 0px {subtitle_style['outline_width']}px {subtitle_style['outline_color']};
                    text-align: {['left', 'center', 'right'][subtitle_style['alignment']-1]};
                    font-weight: {'bold' if subtitle_style['bold'] == 1 else 'normal'};
                    font-style: {'italic' if subtitle_style['italic'] == 1 else 'normal'};
                    margin: 0;
                ">
                这是字幕样式预览，This is subtitle style preview
                </p>
            </div>
            """
            
            st.markdown(preview_style, unsafe_allow_html=True)
            
            if st.button("生成字幕视频"):
                try:
                    # 创建输出目录（确保路径存在）
                    os.makedirs(output_path, exist_ok=True)
                    
                    # 生成翻译字幕文件
                    translated_srt_path = os.path.join(output_path, "translated_subtitles.srt")
                    translated_subs = pysrt.SubRipFile()
                    
                    # 将翻译内容转换为SRT格式
                    translated_subs = create_subtitles_from_text(
                        st.session_state.translated_content, 
                        output_path,
                        duration_per_char=0.2
                    )[1]
                    
                    # 保存翻译字幕到指定路径
                    translated_subs.save(translated_srt_path, encoding='utf-8')
                    st.success(f"翻译字幕已保存至: {translated_srt_path}")

                    # 生成带字幕的视频
                    video_filename = os.path.basename(st.session_state.video_path)
                    output_video_path = os.path.join(output_path, f"translated_{video_filename}")
                    
                    # 执行视频处理，传递字幕样式
                    success = process_video(
                        st.session_state.video_path, 
                        output_video_path, 
                        translated_srt_path,
                        subtitle_style  # 传递字幕样式参数
                    )
                    
                    if success:
                        st.success(f"视频处理成功! 保存在 {output_video_path}")
                        st.video(output_video_path)
                    else:
                        st.error("视频处理失败")
                except ValueError as e:
                    st.error(f"字幕生成失败: {str(e)}")
                except PermissionError as e:
                    st.error(f"文件保存失败: {str(e)}")
                except Exception as e:
                    st.error(f"未知错误: {str(e)[:200]}")
        else:
            missing = []
            if not st.session_state.video_path:
                missing.append("视频")
            if not st.session_state.edited_content:
                missing.append("编辑后的文本")
            if not st.session_state.translated_content:
                missing.append("翻译后的文本")
                
            st.info(f"请先完成以下步骤: {', '.join(missing)}")
    
def process_uploaded_video(video_path, temp_dir, target_lang, api_choice, api_key, secret_key=None, merge_below=True, auto_subtitle=True, subtitle_style=None):
    """处理上传的视频"""
    with st.spinner("处理中，请稍候..."):
        # 提取字幕
        subtitles = extract_subtitles(video_path)
        
        if not subtitles and auto_subtitle:
            st.info("正在自动生成字幕，这可能需要一些时间...")
            subtitle_path = auto_generate_subtitles(video_path, temp_dir)
            if subtitle_path and os.path.exists(subtitle_path):
                subtitles = pysrt.open(subtitle_path)
                
        if not subtitles:
            st.error("未能从视频中提取到字幕，请确保视频包含嵌入式字幕或上传带有同名SRT文件")
            return
        
        # 翻译字幕
        with st.status("正在翻译字幕..."):
            translated_subs = translate_subtitles(
                subtitles, 
                target_lang=target_lang,
                api_choice=api_choice,
                api_key=api_key,
                secret_key=secret_key
            )
        
        # 合并字幕并处理视频
        output_filename = f"translated_{os.path.basename(video_path)}"
        output_path = os.path.join(temp_dir, output_filename)
        
        with st.status("正在合并字幕..."):
            merged_srt_path = merge_subtitles(
                subtitles, 
                translated_subs, 
                temp_dir,
                merge_below
            )
        
        with st.status("正在处理最终视频..."):
            success = process_video(video_path, output_path, merged_srt_path, subtitle_style)
        
        if success:
            # 显示结果并提供下载链接
            st.success("视频处理完成!")
            st.video(output_path)
            
            with open(output_path, "rb") as file:
                st.download_button(
                    label="下载翻译后的视频",
                    data=file,
                    file_name=output_filename,
                    mime="video/mp4"
                )
        else:
            st.error("视频处理失败，请检查日志或尝试其他视频")

if __name__ == "__main__":
    main() 