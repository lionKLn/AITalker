import os
import gradio as gr
from datetime import datetime
import PyPDF2
from docx import Document

# 配置文件存储路径
UPLOAD_FOLDER = './test_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_file(file_info):
    """修复版文件保存方法"""
    try:
        if not file_info:
            return "错误：未接收到文件"
        
        # 获取文件信息（Gradio最新版本返回字典）
        file_name = file_info.name
        file_bytes = file_info.read()  # 直接读取字节内容
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        save_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{os.path.basename(file_name)}")
        
        # 保存文件
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
            
        return f"文件保存成功：{save_path}"
    except AttributeError:
        # 处理旧版Gradio的文件对象格式
        try:
            save_path = os.path.join(UPLOAD_FOLDER, file_info)
            with open(save_path, 'rb') as f:
                file_bytes = f.read()
            return f"文件保存成功：{save_path}"
        except Exception as e:
            return f"兼容处理失败：{str(e)}"
    except Exception as e:
        return f"文件保存失败：{str(e)}"

def parse_file_content(file_path):
    """修复版文件解析方法"""
    try:
        if not os.path.exists(file_path):
            return "错误：文件不存在"
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # PDF文件解析
        if file_ext == '.pdf':
            text = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = page.extract_text() or ""  # 处理空页面
                    text.append(page_text)
            return '\n'.join(text)[:2000]
        
        # Word文档解析
        elif file_ext == '.docx':
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs if para.text])[:2000]
        
        # 纯文本文件
        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[:2000]
        
        else:
            return "错误：不支持的文件格式"
    except PyPDF2.errors.PdfReadError:
        return "错误：PDF文件无法读取（可能已损坏或加密）"
    except Exception as e:
        return f"文件解析失败：{str(e)}"

def process_upload(file_info):
    """增强版文件处理流程"""
    try:
        # 步骤1：保存文件
        save_result = save_uploaded_file(file_info)
        if "失败" in save_result:
            return save_result, ""
        
        saved_path = save_result.split("：")[1] if "成功" in save_result else ""
        
        # 步骤2：解析内容
        if saved_path and os.path.exists(saved_path):
            parsed_content = parse_file_content(saved_path)
            return save_result, parsed_content
        
        return save_result, "文件保存后路径无效"
    except Exception as e:
        return f"处理异常：{str(e)}", ""

# 创建测试界面
with gr.Blocks(title="简历解析测试") as demo:
    gr.Markdown("## 简历文件解析测试系统（修复版）")
    gr.Markdown("支持格式：PDF/DOCX/TXT，最大文件大小10MB")
    
    with gr.Row():
        file_input = gr.File(
            label="📁 上传简历文件",
            file_types=[".pdf", ".docx", ".txt"],
            file_count="single"
        )
        process_btn = gr.Button("🚀 解析文件", variant="primary")
    
    with gr.Row():
        save_status = gr.Textbox(label="文件保存状态", interactive=False)
        parsed_content = gr.Textbox(label="解析结果", lines=10, interactive=False)
    
    # 事件绑定
    process_btn.click(
        fn=process_upload,
        inputs=file_input,
        outputs=[save_status, parsed_content]
    )

if __name__ == "__main__":
    # 运行前需要安装的依赖：
    # pip install PyPDF2 python-docx gradio
    
    # 启动测试服务
    demo.launch(
        server_name="0.0.0.0",
        server_port=6006,
        show_error=True
    )