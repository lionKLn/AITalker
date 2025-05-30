from TFG import MuseTalk_RealTime
from LLM import LLM
from TTS import EdgeTTS 

llm = LLM(mode='offline').init_model('Qwen', 'Qwen/Qwen-1_8B-Chat')

try:
    from TFG import MuseTalk_RealTime
    musetalker = MuseTalk_RealTime()
    musetalker.init_model()
except Exception as e:
    error_print(f"MuseTalk Error: {e}")
    error_print("如果使用MuseTalk，请先下载MuseTalk相关模型")
print("模型已加载完成")
                                    
def tts_generate(text):
    tts = EdgeTTS(list_voices=False)
    #TEXT = '''测试'''
    TEXT = text
    VOICE = "zh-CN-XiaoxiaoNeural"
    OUTPUT_FILE, OUTPUT_SUBS = "tts.wav", "tts.vtt"
    audio_file, sub_file = tts.predict(TEXT, VOICE, 0, 50, 0, OUTPUT_FILE, OUTPUT_SUBS)
    print("Audio file written to", audio_file, "and subtitle file written to", sub_file)

def llm_answer(prompt):
    text = llm.generate(prompt)
    print(text)
    return text
    

def musetalk_response(text):
    '''参数text是前端传递过来的文本，即简历或者处理过后的语音'''
    
    tts_generate(text)
    #tts.wav
    driven_audio = "./tts.wav"

    #test.mov
    # 假设 musetalker 是已实例化的类对象
    source_video = "test.mov"  
    bbox_shift = 0

    

    # 调用方法
    result_video_path, bbox_shift_text = musetalker.prepare_material(
        video_path=source_video,
        bbox_shift=bbox_shift
    )

   

    video = musetalker.inference_noprepare(driven_audio, 
                                            source_video, 
                                            bbox_shift)
    print(video)
    return video

if __name__ == "__main__":
    musetalk_response("test")