#使用前通过命令安装pip install fastapi uvicorn[standard]
#pip install typer
#运行命令uvicorn fastdemo:app --reload

#外部访问需要使用cpolar穿透命令为cpolar http 8000
#需要在服务器上安装curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
#cpolar authtoken xxxxxxx
#uvicorn fastdemo:app --reload
#cpolar http 8000
#之后会出现一个外部的网址，可以访问

import logging
import os
import re
import tempfile
from datetime import datetime
from typing import List

import spacy
import whisper
from fastapi import FastAPI, HTTPException
from fastapi import Form
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydub import AudioSegment

import musetalkdemo

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
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

model = whisper.load_model("base")  # 可根据需要选择模型大小，如 'small', 'medium', 'large'

@app.post("/voice-to-text/")
async def voice_to_text(file: UploadFile = File(...)):
    """
        asr 语音识别，输入语音文件，输出文字

        参数:
        audio_file: 音频文件

        返回:
        - 成功: 处理后的文本
        - 失败: 错误信息
        """
    allowed_types = [
        "audio/mpeg",  # .mp3
        "audio/wav",  # .wav
        "audio/x-wav",  # .wav
        "audio/x-m4a",  # .m4a
        "audio/flac",  # .flac
        "audio/x-flac"
    ]

    if file.content_type not in allowed_types:
        return JSONResponse(status_code=400, content={"error": "仅支持 MP3/WAV/M4A/FLAC 格式的音频文件。"})

    try:
        # 创建临时文件存储上传的原始音频
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(await file.read())
            temp_input_path = temp_audio.name

        # 统一转换为 WAV 格式（Whisper 推荐）
        temp_output_path = temp_input_path.replace(suffix, ".wav")
        audio = AudioSegment.from_file(temp_input_path)
        audio.export(temp_output_path, format="wav")

        # 使用 whisper 模型进行识别
        result = model.transcribe(temp_output_path)
        text = result["text"]

        # 删除临时文件
        os.remove(temp_input_path)
        os.remove(temp_output_path)

        return {"text": text.strip()}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"处理失败: {str(e)}"})


# 简历解析的NLP模型
nlp = spacy.load("zh_core_web_sm")
# 扩展的技术栈关键词库（包含中英文）
TECH_KEYWORDS = [
    # 编程语言
    "Python", "Java", "C\+\+", "C#", "JavaScript", "TypeScript", "Go", "Rust",
    "Kotlin", "Swift", "PHP", "Ruby", "Scala", "HTML", "CSS", "SQL",
    "Python", "Java", "C语言", "JavaScript", "Go语言", "PHP", "HTML", "CSS", "SQL",

    # 数据库
    "MySQL", "PostgreSQL", "Redis", "MongoDB", "Oracle", "SQLite", "SQL Server",
    "Elasticsearch", "Cassandra", "HBase", "DynamoDB",
    "MySQL", "PostgreSQL", "Redis", "MongoDB", "Oracle", "SQLite", "SQL Server",

    # 框架
    "Django", "Flask", "Spring", "Spring Boot", "React", "Vue", "Angular",
    "Node.js", "Express", "Ruby on Rails", "Laravel", ".NET", "ASP.NET",
    "Django", "Flask", "Spring", "Vue", "Angular", "Node.js", ".NET",

    # 云服务
    "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云", "Docker", "Kubernetes",
    "OpenStack", "Serverless", "Lambda", "EC2", "S3", "RDS",
    "AWS", "Azure", "GCP", "阿里云", "腾讯云", "华为云", "Docker", "Kubernetes",

    # 大数据
    "Hadoop", "Spark", "Kafka", "Flink", "Storm", "Hive", "Pig", "HDFS",
    "Hadoop", "Spark", "Kafka", "Flink", "Hive",

    # 其他技术
    "Git", "SVN", "Jenkins", "GitLab", "GitHub", "CI/CD", "RESTful", "GraphQL",
    "gRPC", "微服务", "容器化", "DevOps", "敏捷开发", "单元测试", "自动化测试",
    "Git", "SVN", "Jenkins", "GitLab", "GitHub", "CI/CD", "RESTful", "微服务",

    # 专业领域
    "机器学习", "深度学习", "人工智能", "AI", "计算机视觉", "自然语言处理", "NLP",
    "数据挖掘", "大数据分析", "区块链", "物联网", "IoT", "网络安全",
    "机器学习", "深度学习", "人工智能", "AI", "自然语言处理", "NLP", "数据挖掘"
]


@app.post("/resume-parsing/")
async def resume_parsing(resume_text: str = Form(...)):
    """
    简历解析，输入简历文本，输出面试技术栈，面试项目
    参数:
      resume_text: 简历文本
    返回:
      - tech_stack: 技术栈列表
      - projects:项目经验列表
    """
    logger.info(f"收到简历解析请求，文本长度: {len(resume_text)} 字符")

    try:
        # 技术栈关键词提取
        tech_keywords = extract_tech_stack(resume_text)
        logger.info(f"提取到技术栈: {tech_keywords}")

        # 项目经验提取
        projects = extract_projects(resume_text)
        logger.info(f"提取到项目: {[p['name'] for p in projects]}")

        return {
            "tech_stack": tech_keywords,
            "projects": projects
        }

    except Exception as e:
        logger.error(f"简历解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"简历解析失败: {str(e)}")


def extract_tech_stack(text: str) -> list:
    """从文本中提取技术栈关键词"""
    found_keywords = []
    text_lower = text.lower()  # 转换为小写进行不区分大小写的匹配

    # 对每个关键词进行更灵活的匹配
    for keyword in TECH_KEYWORDS:
        # 处理带特殊字符的关键词（如C++）
        clean_keyword = re.escape(keyword)

        # 创建更灵活的匹配模式：
        # 1. 关键词前后可能有0-2个其他字符（考虑中英文混排）
        # 2. 关键词可能被括号包围
        # 3. 关键词可能被标点符号包围
        pattern = rf'[\s(（【「\[]?{clean_keyword}[\s)）】」\],.;：:！!？?]?'

        # 使用re.search允许部分匹配
        if re.search(pattern, text, re.IGNORECASE):
            # 保留原始形式的关键词
            found_keywords.append(keyword)

    # 去重处理（保留原始大小写）
    unique_keywords = []
    seen = set()
    for kw in found_keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_keywords.append(kw)

    return unique_keywords


def extract_projects(text: str) -> list:
    """
    从简历文本中提取项目经验，返回一个 list，每个元素是 {"name": 项目名称，"description": 项目描述（可选）}
    这里仅演示如何更全面地从多种写法中抓取项目名称，并且尽量兼顾中英混合简历。
    """
    projects = []
    seen = set()  # 用来去重

    # 1. 先按“项目经验”这一段拆分，拿到各个项目段落（做为补充，可选）
    #    如果简历里有“项目经验：”或者“工作项目”之类的标题，可以先定位到那一段，然后在里面进一步抽取。
    #    这里简单示例：如果存在 “项目经验” 字样，就截取其后的文本，否则直接用全文
    body = text
    match_pe = re.search(r'(项目经验[:：\s]*)([\s\S]+)$', text)
    if match_pe:
        body = match_pe.group(2)

    # 2. 定义多种常见的项目名称正则模式
    patterns = [
        # 【项目名】（最常见的格式之一）
        r'【([^】]{2,50})】',

        # “项目名称：XXX” 或 “项目：XXX” （中文分隔符）
        r'项目(?:名称)?[：:\s]*([^\n\r，；；]{2,50})',

        # “XXX项目” / “XXX系统” / “XXX平台”/ “XXX方案”
        # 要求名称长度在 2~50 之间，后面紧跟 项目、系统、平台、方案
        r'([^\s\d，；\n]{2,50}?)(?:项目|系统|平台|方案)(?=[\s，；,\.;:：。]|$)',

        # 英文写法 “Project：XXX” 或 “Project：XXX” （中英文冒号都考虑）
        r'Project\s*[：:\s]*([^\n\r,;]{2,50})',

        # “负责XXX项目” / “参与XXX系统” / “在XXX平台中” 之类
        r'(?:负责|参与|设计|开发)[^，。,；\n]{0,10}?([^\s\d，；\n]{2,50}?)(?:项目|系统|平台)(?=[\s，；,;]|$)',

        # 纯序号开头：例如 “1. XXX项目” 或 “* XXX项目”
        r'(?:^|\n)[\s\-*]*[\d一二三四五六七八九十]+[\.．、\s]*([^\s\r\n\d]{2,50}?)(?:项目|系统|平台)(?=[\s，；,;]|$)',
    ]

    # 3. 对每个模式分别做 findall，拿到潜在的“项目名”
    for pattern in patterns:
        for match in re.findall(pattern, body, flags=re.IGNORECASE):
            name = match.strip()
            # 清理尾部可能残留的标点
            name = re.sub(r'[，。；、\s]+$', '', name)
            # 长度筛选 2~50 之间
            if 2 <= len(name) <= 50:
                normalized = name.lower().replace(' ', '')
                if normalized not in seen and is_valid_project_name(name):
                    seen.add(normalized)
                    projects.append({"name": name})

    # 4. 如果上面没有匹配到任何项目名，可以尝试按行扫描：
    #    例如：某些简历会写成 “项目一：XXX” 或者每行都写一个小标题。
    if not projects:
        for line in body.splitlines():
            # 去除行首行尾空白
            ln = line.strip()
            # 跳过过短的行
            if len(ln) < 4 or len(ln) > 100:
                continue
            # 如果这一行包含“项目”字样，就把冒号后的部分认为是项目名
            if '项目' in ln and '：' in ln:
                parts = re.split(r'[：:]', ln, maxsplit=1)
                if len(parts) == 2:
                    candidate = parts[1].strip()
                    # 截断到第一个逗号或句号之前
                    candidate = re.split(r'[，。,；;]', candidate)[0].strip()
                    if 2 <= len(candidate) <= 50 and is_valid_project_name(candidate):
                        normalized = candidate.lower().replace(' ', '')
                        if normalized not in seen:
                            seen.add(normalized)
                            projects.append({"name": candidate})

    # 5. 最终只保留前 10 个项目，防止过多噪声
    return projects[:10]


def is_valid_project_name(name: str) -> bool:
    """
    验证一个项目名称是否“合理”。可以根据简历特点继续微调。
    - 长度 2~50
    - 不包含明显无效的短词、数字或纯符号
    - 不包含通用无效关键词，如 '项目名称', '项目描述' 等
    """
    if not name:
        return False

    # 长度筛选
    if len(name) < 2 or len(name) > 50:
        return False

    # 排除常见无效片段
    invalids = ["项目名称", "项目描述", "职责", "工作内容", "技术栈", "序号", "一", "二", "三"]
    for inv in invalids:
        if inv in name:
            return False

    # 排除纯数字或纯标点
    if re.fullmatch(r'[\d\s\W]+', name):
        return False

    return True




# --------------------------------------------------------------------------
# 1. 先定义输入数据和输出数据的 Pydantic 模型（可选，但能让接口更规范）
# ----------------------------------------------------------------------
class QARecord(BaseModel):
    """
    单条面试问答记录
    """
    question: str = Field(..., description="面试官提出的问题文本")
    answer: str = Field(..., description="候选人的回答文本")
    timestamp: str = Field(None, description="可选：该条问答发生的时间戳（ISO 格式字符串）")

class InterviewData(BaseModel):
    """
    前端传入的整个面试对话记录，示例结构：
    {
      "candidate": "张三",                    # 候选人姓名，可选
      "position": "后端开发工程师",           # 面试岗位，可选
      "records": [
        {
          "question": "请简单介绍一下自己？",
          "answer": "我叫张三，毕业于XXX大学……",
          "timestamp": "2025-05-30T10:15:00"
        },
        {
          "question": "你最擅长的编程语言是什么？",
          "answer": "我主要用 Python 和 Java。",
          "timestamp": "2025-05-30T10:17:20"
        },
        ……
      ]
    }
    """
    candidate: str = Field(None, description="候选人姓名，可选")
    position: str = Field(None, description="面试岗位，可选")
    records: List[QARecord] = Field(..., description="问答列表，至少一个问答元素")


class QuestionItem(BaseModel):
    """
    输出中 questionList 的单个项目格式
    """
    idx: int = Field(..., description="本题在 questionList 中的序号（从 1 开始）")
    question: str = Field(..., description="问题文本")
    answer: str = Field(..., description="回答文本")
    timestamp: str = Field(None, description="可选：该条问答发生时间戳")

class ReportResponse(BaseModel):
    """
    最终返回给前端的“面试报告”结构
    """
    title: str = Field(..., description="报告标题，例如 “张三 面试报告” 或 “面试报告”")
    candidate: str = Field(None, description="候选人姓名，若前端未传入，可省略或为 None")
    position: str = Field(None, description="面试岗位，若前端未传入，可省略或为 None")
    generate_time: str = Field(..., description="报告生成时间，ISO 格式字符串")
    total_questions: int = Field(..., description="本次面试一共多少个问答记录")
    summary: str = Field(..., description="对本次面试问答的简要总结（可在此自行上屏写死或用 NLP 生成）")
    questionList: List[QuestionItem] = Field(..., description="一个数组，按顺序列出所有问答记录")
@app.post("/generate-report/", response_model=ReportResponse)
async def generate_report(interview_data: InterviewData):
    """
    接收：interview_data（详见 InterviewData 结构）
      - candidate: 候选人姓名（可选）
      - position: 面试岗位（可选）
      - records: List[QARecord]，问答记录列表

    返回：ReportResponse 结构，包括：
      - title: 报告标题
      - candidate: 候选人姓名（若有）
      - position: 面试岗位（若有）
      - generate_time: 报告生成时间
      - total_questions: 问答总数
      - summary: 对本次面试整体表现的简要评语
      - questionList: [{ idx, question, answer, timestamp }, …] 列表，按原序排列
    """

    try:
        # 1. 从 interview_data 中提取基本字段
        candidate_name = interview_data.candidate or ""
        position = interview_data.position or ""
        records = interview_data.records  # List[QARecord]

        # 2. 生成报告标题
        if candidate_name and position:
            title = f"{candidate_name} {position} 面试报告"
        elif candidate_name:
            title = f"{candidate_name} 面试报告"
        else:
            title = "面试报告"

        # 3. 按顺序构建 questionList
        question_list = []
        for idx, qa in enumerate(records, start=1):
            question_item = QuestionItem(
                idx=idx,
                question=qa.question,
                answer=qa.answer,
                timestamp=qa.timestamp or ""
            )
            question_list.append(question_item)

        # 4. 生成一个简单的“summary”
        #    这里可以自行扩展，比如调用 LLM，总结面试表现／推荐打分等。
        #    演示示例：如果问答数量超过 5 条，就说“面试问答充足”；否则提示“问答条数较少”。
        total_q = len(records)
        if total_q >= 5:
            summary_text = f"本次面试共包含 {total_q} 条问答，问答内容充实，覆盖了关键技术点。"
        elif total_q > 0:
            summary_text = f"本次面试共 {total_q} 条问答，建议在后续环节深入考察更多技术细节。"
        else:
            summary_text = "未检测到面试问答记录。请确认是否传入了 records 字段。"

        # 5. 填充返回结构
        response = ReportResponse(
            title=title,
            candidate=candidate_name if candidate_name else None,
            position=position if position else None,
            generate_time=datetime.utcnow().isoformat() + "Z",
            total_questions=total_q,
            summary=summary_text,
            questionList=question_list
        )

        return response

    except Exception as e:
        # 若发生任何异常，返回 500 并携带错误信息
        raise HTTPException(status_code=500, detail=f"生成面试报告失败：{str(e)}")