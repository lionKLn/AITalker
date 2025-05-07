import os
import random 
import gradio as gr
import numpy as np
import time
import torch
import gc
import warnings
warnings.filterwarnings('ignore')
from zhconv import convert
from LLM import LLM
from TTS import EdgeTTS
from src.cost_time import calculate_time

# 固定配置参数
FIXED_CONFIG = {
    "character_image": "../examples/source_image/art_3.png",  # 固定面试官形象
    "voice": "zh-CN-YunyangNeural",  # 固定声音
    "tts_method": "Edge-TTS",
    "llm_method": "Qwen",
    "talker_method": "SadTalker",
    "pose_styles": [3, 5, 7, 9],  # 点头动作样式库
    "sample_questions": [
        "请用2分钟做个自我介绍",
        "为什么选择这个岗位？",
        "请分享一个你解决过的技术难题案例",
        "你如何看待团队合作中的冲突？"
    ]
}

class InterviewState:
    """面试流程状态管理"""
    def __init__(self):
        self.step = 0  # 0-等待开始 1-进行中 2-已完成
        self.resume_text = ""
        self.history = []
    
    def get_next_question(self, last_answer=""):
        """生成面试问题"""
        if self.step == 0:
            self.step = 1
            return "请先做一个简短的自我介绍"
        
        # 结合简历内容和最后回答生成问题
        prompt = f"面试官简历摘要：{self.resume_text[:300]}\n候选人的上一个回答：{last_answer[:200]}\n请生成一个专业的后续面试问题"
        return llm.generate(prompt, system="你是一个严谨的AI面试官")

interview_state = InterviewState()

def get_title(title='AI面试官 - 智能招聘助手'):
    description = f"""
    <p style="text-align: center; font-weight: bold;">
        <span style="font-size: 28px;">{title}</span>
        <br>
        <span>AI面试官是基于Linly-Talker开发的智能招聘系统，具备多模态交互能力，支持实时语音对话和智能问题生成。</span>
    </p>
    """
    return description

# 初始化核心模块
edgetts = EdgeTTS()
llm = LLM().init_model(
    FIXED_CONFIG["llm_method"], 
    prefix_prompt="你是一个专业的AI面试官，需要根据候选人的简历和回答提出有深度的技术问题"  # 修改参数名
)
from TFG import SadTalker
talker = SadTalker(lazy_load=True)

@calculate_time
def Asr(audio):
    """语音识别（固定使用Whisper-base）"""
    try:
        question = asr.transcribe(audio)
        return convert(question, 'zh-cn')
    except Exception as e:
        return "语音识别失败，请重试"

def generate_video(response_text):
    """生成数字人视频（带随机点头动作）"""
    # TTS生成语音
    tts_file = "interview_answer.wav"
    edgetts.predict(
        response_text, 
        voice=FIXED_CONFIG["voice"],
        rate=0, volume=100, pitch=0,
        save_path=tts_file
    )
    
    # 视频生成参数（添加随机动作）
    video = talker.test2(
        FIXED_CONFIG["character_image"],
        tts_file,
        preprocess_type='crop',
        pose_style=random.choice(FIXED_CONFIG["pose_styles"]),  # 随机点头动作
        exp_weight=1.2,  # 增强表情
        is_still_mode=False,
        enhancer=False
    )
    return video

def process_interview(audio_input, text_input, resume_file, history):
    """处理面试流程"""
    # 简历解析
    if resume_file and not interview_state.resume_text:
        interview_state.resume_text = "解析后的简历内容..."  # 这里需要实际简历解析逻辑
        yield history + [("系统", "简历已解析，请开始面试")], None
        return
    
    # 语音识别
    if audio_input:
        text = Asr(audio_input)
        yield history + [("候选人", text)], None
        return
    
    # 生成面试官问题
    if text_input:
        # 添加用户回答到历史
        new_history = history + [("候选人", text_input)]
        
        # 生成面试官响应
        response = interview_state.get_next_question(text_input)
        
        # 生成视频
        video = generate_video(response)
        
        yield new_history + [("面试官", response)], video

def create_webui():
    """创建专用面试界面"""
    with gr.Blocks(analytics_enabled=False, title='AI Interviewer') as app:
        gr.HTML(get_title())
        
        with gr.Row():
            # 简历上传区
            with gr.Column(scale=1):
                resume_upload = gr.File(label="上传简历（PDF/docx）")
                status_info = gr.Textbox(label="系统状态", interactive=False)
                
            # 主交互区
            with gr.Column(scale=2):
                # 视频输出
                video_output = gr.Video(label="AI面试官", autoplay=True)
                
                # 聊天界面
                chatbot = gr.Chatbot(height=300, show_copy_button=True)
                
                # 输入区
                with gr.Row():
                    audio_input = gr.Audio(sources=["microphone"], type="filepath", label="语音回答")
                    text_input = gr.Textbox(placeholder="输入文字回答...", label="文字回答")
                
                submit_btn = gr.Button("发送", variant="primary")

        # 交互逻辑
        inputs = [audio_input, text_input, resume_upload, chatbot]
        outputs = [chatbot, video_output]
        
        submit_btn.click(
            fn=process_interview,
            inputs=inputs,
            outputs=outputs
        )
    
    return app

if __name__ == "__main__":
    # 环境配置
    os.environ["GRADIO_TEMP_DIR"] = './temp'
    torch.set_num_threads(4)
    
    # 启动应用
    app = create_webui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )