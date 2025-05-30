#使用前通过命令安装pip install fastapi uvicorn[standard]
#pip install typer
#运行命令uvicorn fastdemo:app --reload

#外部访问需要使用cpolar穿透命令为cpolar http 8000
#需要在服务器上安装curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
#cpolar authtoken xxxxxxx
#uvicorn fastdemo:app --reload
#cpolar http 8000
#之后会出现一个外部的网址，可以访问
from typing import Union
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import musetalkdemo  # 导入musetalkdemo模块
import os

app = FastAPI()

# # 存储生成视频的临时目录
# OUTPUT_DIR = "generated_videos"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/generate-video/")
async def generate_video(text: str):
    """
    接收文本参数并生成视频
    
    参数:
    text: 输入文本内容
    
    返回:
    - 成功: 视频文件下载
    - 失败: 错误信息
    """
    try:
        # 生成唯一文件名
        # video_filename = f"{uuid.uuid4().hex}.mp4"
        # output_path = os.path.join(OUTPUT_DIR, video_filename)
        
        # 调用你的模块方法
        video_path = musetalkdemo.musetalk_response(text)  # 假设支持输出路径参数
        
        # 返回视频文件
        return FileResponse(
            path=video_path,
            media_type='video/mp4',
            filename=f"generated_video.mp4"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"视频生成失败: {str(e)}"
        )

@app.post("/generate-text/")
async def process_text(text: str):
    try:
        # 假设 musetalk_response 返回 (视频路径, 处理后的文本)
        processed_text = musetalkdemo.llm_answer(text)
        return {"text": processed_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")