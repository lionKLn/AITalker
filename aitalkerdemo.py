import json
import os
import random
import gradio as gr
import time
from datetime import datetime
from zhconv import convert
from LLM import LLM
from ASR import WhisperASR
from TFG import SadTalker
from TTS import EdgeTTS
from src.cost_time import calculate_time
import PyPDF2
from docx import Document
# 环境配置
os.environ["GRADIO_TEMP_DIR"] = './temp'

# 系统描述
description = """<p style="text-align: center; font-weight: bold;">
    <span style="font-size: 28px;">Mentor Nekomiya: 软件技术岗 AI 面试官 </span><br> 
    <span>支持本地简历上传和模拟面试，生成逼真面试场景</span>
</p>
"""

# 系统参数配置
blink_every = True
size_of_image = 256
preprocess_type = 'crop'
facerender = 'facevid2vid'
enhancer = False
is_still_mode = False
exp_weight = 1

# 数字人形象配置
pic_path = "girl.png"
crop_pic_path = "./inputs/first_frame_dir_girl/girl.png"
first_coeff_path = "./inputs/first_frame_dir_girl/girl.mat"
crop_info = (
    (403, 403), (19, 30, 502, 513), [40.05956541381802, 40.17324339233366, 443.7892505041507, 443.9029284826663])

use_ref_video = False
ref_video = None
ref_info = 'pose'
use_idle_mode = False
length_of_audio = 5

# # 本地简历存储路径
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# 简历配置
CV_PATH = "./data/candidate_cv.docx"  # 固定简历路径

def parse_cv(file_path):
    """解析本地简历文件"""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return '\n'.join([page.extract_text() for page in reader.pages])
        
        elif ext == '.docx':
            doc = Document(file_path)
            print(doc)
            return '\n'.join([para.text for para in doc.paragraphs if para.text])[:2000]
        
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        else:
            raise ValueError("不支持的简历格式")
    except Exception as e:
        raise RuntimeError(f"简历解析失败: {str(e)}")

@calculate_time
def Asr(audio):
    """语音识别处理"""
    try:
        question = asr.transcribe(audio)
        return convert(question, 'zh-cn')
    except Exception as e:
        print("ASR Error:", e)
        return "语音识别失败，请重试"

@calculate_time
def LLM_response(question, voice='zh-CN-YunyangNeural', rate=0, volume=100, pitch=0, prompt=None):
    """生成回答并合成语音"""
    print(question)
    print(prompt)
    answer = llm.generate(question, prompt)
    print("面试官回答:", answer)
    
    # EdgeTTS生成语音
    output_path = os.path.join(UPLOAD_FOLDER, f"answer_{int(time.time())}.wav")
    tts.predict(answer, voice, rate, volume, pitch, output_path)
    
    return output_path, answer

@calculate_time
def Talker_response(chatbot, source_image, text, 
                   prompt=None, voice='zh-CN-YunyangNeural', 
                   rate=0, volume=100, pitch=0, batch_size=2):
    """生成数字人视频响应"""
    prompt = '你是一个面试官请问出第一个问题'
    driven_audio, response = LLM_response(text, voice, rate, volume, pitch, prompt)
    
    # 生成随机头部动作
    pose_style = random.randint(0, 45)
    
    video = talker.test(pic_path,
                        crop_pic_path,
                        first_coeff_path,
                        crop_info,
                        source_image,
                        driven_audio,
                        )
    return video, chatbot + [(text if prompt == None else '开始面试', response)]

# def save_uploaded_cv(file):
#     """保存上传的简历到本地"""
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     save_path = os.path.join(UPLOAD_FOLDER, f"cv_{timestamp}{os.path.splitext(file.name)[-1]}")
#     with open(save_path, 'wb') as f:
#         f.write(file.read())
#     return save_path

# def read_latest_cv(chatbot, source_image, voice, rate, volume, pitch, batch_size):
#     """读取最新上传的简历"""
#     try:
#         cv_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.startswith('cv_')]
#         if not cv_files:
#             return None, chatbot + [("系统", "未找到简历文件，请先上传")]
            
#         latest_cv = max(cv_files, key=lambda x: os.path.getctime(os.path.join(UPLOAD_FOLDER, x)))
#         with open(os.path.join(UPLOAD_FOLDER, latest_cv), 'r', encoding='utf-8') as f:
#             cv_content = f.read()
        
#         return Talker_response(
#             chatbot, source_image, 
#             f"候选人简历内容：{cv_content[:1000]}...（已截断）",
#             '请根据简历内容提出第一个面试问题',
#             voice, rate, volume, pitch, batch_size
#         )
#     except Exception as e:
#         print("读取简历失败:", e)
#         return None, chatbot + [("系统", "简历读取失败，请检查文件格式")]

# def start_interview():
#     """启动面试流程"""
#     try:
#         # 读取并解析简历
#         cv_content = parse_cv(CV_PATH)
#         prompt = f"根据以下简历内容开始技术面试：\n{cv_content[:1000]}..."
        
#         # 生成首个问题
#         initial_question = llm.generate(prompt)
#         source_image = gr.Image(label="面试官形象", type="filepath", elem_id="img2img_image",
#                                                         value='examples/source_image/full4.jpeg',
#                                                         width=512)
#         return Talker_response([], source_image,initial_question)
#     except Exception as e:
#         print("面试启动失败:", e)
#         return None, [("系统", f"面试初始化失败: {str(e)}")]
def clear_session():
    """清空会话"""
    llm.clear_history()
    return '', []

def main():
    """预处理默认的简历"""
    
    """主界面"""
    with gr.Blocks(analytics_enabled=False, title='AI面试官') as inference:
        gr.HTML(description)
        
        with gr.Row(equal_height=False):
            # 左侧控制面板
            with gr.Column(variant='panel'):
                chatbot = gr.Chatbot(label="对话记录", height=400)
                question_audio = gr.Audio(sources=['microphone'], 
                                         type="filepath", 
                                         label='语音输入')
                input_text = gr.Textbox(label="文字输入", lines=3)
                #input_text = "你好面试官"
                with gr.Accordion("Advanced Settings(高级设置) ",
                                              open=False):
                                source_image = gr.Image(label="面试官形象", type="filepath", elem_id="img2img_image",
                                                        value='examples/source_image/full4.jpeg',
                                                        width=512)
                                # voice = gr.Dropdown([],
                                #                     value='zh-CN-XiaoxiaoNeural',
                                #                     label="Voice")
                                # rate = gr.Slider(minimum=-100,
                                #                  maximum=100,
                                #                  value=0,
                                #                  step=1.0,
                                #                  label='Rate')
                                # volume = gr.Slider(minimum=0,
                                #                    maximum=100,
                                #                    value=100,
                                #                    step=1,
                                #                    label='Volume')
                                # pitch = gr.Slider(minimum=-100,
                                #                   maximum=100,
                                #                   value=0,
                                #                   step=1,
                                #                   label='Pitch')
                                # batch_size = gr.Slider(minimum=1,
                                #                        maximum=10,
                                #                        value=2,
                                #                        step=1,
                                #                        label='Talker Batch size')

                
                with gr.Row():
                    asr_btn = gr.Button("🎤 语音转文字")
                    submit_btn = gr.Button("🚀 发送", variant='primary')
                    clear_btn = gr.Button("🧹 清空记录")

            # 右侧显示面板
            with gr.Column(variant='panel'):
                gen_video = gr.Video(label="面试官视频", format="mp4", autoplay=True)

        # 事件绑定
        submit_btn.click(fn=Talker_response,
                         inputs=[chatbot,
                                 source_image,
                                 input_text],
                         outputs=[gen_video, chatbot])
        asr_btn.click(Asr, inputs=question_audio, outputs=input_text)
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, input_text])
        
        #自动启动面试
        # inference.load(
        #     fn=start_interview,
        #     outputs=[gen_video, chatbot]
        # )
#         cv_content = parse_cv(CV_PATH)
#         print(cv_content)
#         # gen_video, chatbot = Talker_response(chatbot, source_image, cv_content + '面试正式开始，以下是这位同学的简历。请给出第一个题目。')
#         gen_video, chatbot = Talker_response(chatbot, source_image, '面试正式开始，以下是这位同学的简历。请给出第一个题目。')
        

    return inference

if __name__ == "__main__":
    # 初始化模块
    # llm_class = LLM(mode='offline')
    # llm = llm_class.init_model('Qwen', 'Qwen/Qwen-1_8B-Chat', prefix_prompt="你是一个严谨的面试官")
    llm_class = LLM(mode='offline')
    llm = llm_class.init_model('Qwen', 'Qwen/Qwen-1_8B-Chat', prefix_prompt="你是一个严谨的面试官")
    #llm = llm_class.init_model('直接回复 Direct Reply')
   
    talker = SadTalker(lazy_load=True)
    asr = WhisperASR('base')
    tts = EdgeTTS()
    
    # 启动应用
    gr.close_all()
    demo = main()
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=6006,
        debug=True
    )