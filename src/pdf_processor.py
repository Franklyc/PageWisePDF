import os
import io
import tempfile
from pathlib import Path
import base64
import json
import concurrent.futures
import threading
from queue import Queue
import time
import sys

from PyQt5.QtCore import QObject, pyqtSignal
import fitz  # PyMuPDF
from pypdf import PdfReader
import requests
from PIL import Image
from tqdm import tqdm

class PDFProcessor(QObject):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    
    def __init__(self, pdf_path, output_dir, api_key, api_endpoint, model_name,
                 is_summary_mode=False, start_page=None, end_page=None, 
                 concurrent_calls=1, pages_per_call=1, language="English",
                 api_call_interval=0.0):
        super().__init__()
        
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.api_key = api_key
        # Process API endpoint based on rules
        self.api_endpoint = self.process_api_endpoint(api_endpoint)
        self.model_name = model_name
        self.is_summary_mode = is_summary_mode
        self.start_page = start_page
        self.end_page = end_page
        self.concurrent_calls = concurrent_calls
        self.pages_per_call = pages_per_call
        self.language = language
        self.api_call_interval = api_call_interval
        
        self.cancelled = False
        self._thread_lock = threading.Lock()
        self._api_call_lock = threading.Lock()  # Lock for API call interval management
        self._last_api_call_time = 0  # Track last API call time
        
        # Create output directories
        self.images_dir = os.path.join(output_dir, "images")
        self.md_dir = os.path.join(output_dir, "md")
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.md_dir, exist_ok=True)
    
    def log(self, message):
        """Send a log message through the log_update signal"""
        self.log_update.emit(message)
    
    def process_api_endpoint(self, endpoint):
        """
        Process API endpoint based on special rules:
        - If endpoint ends with /, don't append /v1/chat/completions
        - If endpoint ends with #, use exactly as is without modifications
        - Otherwise append /v1/chat/completions if not already there
        """
        # Handle empty endpoint
        if not endpoint:
            return "https://api.openai.com/v1/chat/completions"
        
        # Special case: endpoint ends with #, use as is (strip the #)
        if endpoint.endswith('#'):
            return endpoint[:-1]  # Remove the trailing #
            
        # Special case: endpoint ends with /, don't append /v1
        if endpoint.endswith('/'):

            # Just append chat/completions if not already there
            if not endpoint.endswith('/chat/completions/'):
                return endpoint + 'chat/completions'
            return endpoint
        
        # Normal case: ensure endpoint ends with /v1/chat/completions
        if not endpoint.endswith('/chat/completions'):
            # Check if it already has /v1 at the end
            if not endpoint.endswith('/v1'):
                return endpoint + '/v1/chat/completions'
            else:
                return endpoint + '/chat/completions'
        
        return endpoint
    
    def cancel(self):
        with self._thread_lock:
            self.cancelled = True
    
    def is_cancelled(self):
        with self._thread_lock:
            return self.cancelled
    
    def process(self):
        """Main processing method"""
        self.log(self.tr("Starting PDF processing...") if self.language == "English" else "开始处理 PDF...")
        
        try:
            # Extract total page count using PyPDF for compatibility
            reader = PdfReader(self.pdf_path)
            total_pages = len(reader.pages)
            self.log(self.tr(f"PDF has {total_pages} pages") if self.language == "English" else f"PDF 有 {total_pages} 页")
            
            # Determine page range
            if self.start_page is None:
                self.start_page = 1
            if self.end_page is None:
                self.end_page = total_pages
            
            # Validate page range
            self.start_page = max(1, min(self.start_page, total_pages))
            self.end_page = max(self.start_page, min(self.end_page, total_pages))
            
            num_pages_to_process = self.end_page - self.start_page + 1
            self.log(self.tr(f"Processing pages {self.start_page} to {self.end_page} ({num_pages_to_process} pages)") 
                    if self.language == "English" 
                    else f"处理第 {self.start_page} 页到第 {self.end_page} 页（共 {num_pages_to_process} 页）")
            
            # Step 1: Convert PDF pages to images using PyMuPDF (fitz)
            self.status_update.emit(self.tr("Converting PDF to images...") if self.language == "English" else "正在将 PDF 转换为图像...")
            self.log(self.tr("Converting PDF pages to images...") if self.language == "English" else "正在将 PDF 页面转换为图像...")
            
            image_paths = self.convert_pdf_to_images()
            
            if self.is_cancelled():
                self.log(self.tr("Operation cancelled.") if self.language == "English" else "操作已取消。")
                return
            
            # Step 2: OCR using OpenAI API
            self.status_update.emit(self.tr("Processing images with OCR...") if self.language == "English" else "正在使用 OCR 处理图像...")
            self.log(self.tr("Starting OCR processing...") if self.language == "English" else "开始 OCR 处理...")
            
            # Log API call interval if set
            if self.api_call_interval > 0:
                self.log(self.tr(f"Using API call interval of {self.api_call_interval} seconds") 
                       if self.language == "English" 
                       else f"使用 {self.api_call_interval} 秒的 API 调用间隔")
            
            # Group pages for batch processing if pages_per_call > 1
            page_groups = []
            for i in range(0, len(image_paths), self.pages_per_call):
                group = image_paths[i:i + self.pages_per_call]
                page_groups.append(group)
            
            # Process page groups with concurrent API calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_calls) as executor:
                futures = {executor.submit(self.process_page_group, group): group for group in page_groups}
                completed = 0
                
                for future in concurrent.futures.as_completed(futures):
                    if self.is_cancelled():
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.log(self.tr("Operation cancelled.") if self.language == "English" else "操作已取消。")
                        return
                    
                    try:
                        future.result()
                    except Exception as e:
                        self.log(self.tr(f"Error processing pages: {str(e)}") if self.language == "English" else f"处理页面时出错：{str(e)}")
                    
                    completed += 1
                    progress = 50 + int(completed / len(page_groups) * 40)  # Next 40% of progress
                    self.progress_update.emit(progress)
            
            # Step 3: Consolidate all MD files into a single file
            if not self.is_cancelled():
                self.status_update.emit(self.tr("Consolidating results...") if self.language == "English" else "正在整合结果...")
                self.log(self.tr("Consolidating markdown files...") if self.language == "English" else "正在整合 Markdown 文件...")
                
                consolidated_path = self.consolidate_markdown_files()
                self.log(self.tr(f"Consolidated file created: {consolidated_path}") 
                        if self.language == "English" 
                        else f"已创建整合文件：{consolidated_path}")
                
                self.progress_update.emit(100)
                self.status_update.emit(self.tr("Processing completed") if self.language == "English" else "处理完成")
        
        except Exception as e:
            self.log(self.tr(f"Error: {str(e)}") if self.language == "English" else f"错误：{str(e)}")
            self.status_update.emit(self.tr("Error occurred") if self.language == "English" else "发生错误")
    
    def convert_pdf_to_images(self):
        """Convert PDF pages to images using PyMuPDF (fitz)"""
        image_paths = []
        zoom_factor = 3.0  # Adjust for higher resolution images (equivalent to higher DPI)
        
        try:
            # Open the PDF with PyMuPDF
            pdf_document = fitz.open(self.pdf_path)
            
            # Process each page
            page_count = pdf_document.page_count
            processed_count = 0
            
            # Adjust start/end page for PyMuPDF's 0-based indexing
            start_idx = self.start_page - 1
            end_idx = self.end_page - 1
            
            for page_idx in range(start_idx, end_idx + 1):
                if self.is_cancelled():
                    break
                
                # Get the page
                page = pdf_document[page_idx]
                page_num = page_idx + 1  # Convert back to 1-based page numbers
                
                # Set the transformation matrix for higher resolution
                matrix = fitz.Matrix(zoom_factor, zoom_factor)
                
                # Render page to an image (pixmap)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                
                # Save the image
                image_path = os.path.join(self.images_dir, f"page_{page_num:04d}.png")
                pixmap.save(image_path)
                image_paths.append(image_path)
                
                processed_count += 1
                # Update progress (50% of total progress is for PDF conversion)
                progress = int((processed_count / (end_idx - start_idx + 1)) * 50)
                self.progress_update.emit(progress)
                
                self.log(self.tr(f"Converted page {page_num} to image") if self.language == "English" else f"已将第 {page_num} 页转换为图像")
            
            # Close the PDF document
            pdf_document.close()
            
        except Exception as e:
            self.log(self.tr(f"Error converting PDF to images: {str(e)}") if self.language == "English" else f"将PDF转换为图像时出错：{str(e)}")
            raise
        
        return image_paths
    
    def process_page_group(self, image_paths):
        """Process a group of pages with a single API call"""
        # For a group with multiple pages, we need to determine page numbers
        start_idx = 0
        for img_path in image_paths:
            page_num = int(os.path.basename(img_path).split('_')[1].split('.')[0])
            
            if start_idx == 0:
                page_nums = [page_num]
                start_idx = page_num
            else:
                page_nums.append(page_num)
        
        try:
            # Prepare base64 images
            encoded_images = []
            for img_path in image_paths:
                with open(img_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
                    encoded_images.append(encoded_image)
            
            # Apply API call rate limiting if interval is set
            self.apply_api_call_interval()
            
            # Call OpenAI API
            response = self.call_openai_api(encoded_images, page_nums)
            
            # Write output to markdown files
            if len(encoded_images) == 1:
                # Single page case
                page_num = page_nums[0]
                output_path = os.path.join(self.md_dir, f"page_{page_num:04d}.md")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(response)
                self.log(self.tr(f"Processed page {page_num}") if self.language == "English" else f"已处理第 {page_num} 页")
            else:
                # Multiple pages case - need to split the response by page indicators
                self.split_and_save_multi_page_response(response, page_nums)
        
        except Exception as e:
            self.log(self.tr(f"Error processing page(s) {page_nums}: {str(e)}") 
                    if self.language == "English" 
                    else f"处理第 {page_nums} 页时出错：{str(e)}")
            raise
    
    def apply_api_call_interval(self):
        """Apply a delay between API calls if interval is set"""
        if self.api_call_interval <= 0:
            return
            
        with self._api_call_lock:
            # Calculate time since last API call
            current_time = time.time()
            elapsed = current_time - self._last_api_call_time
            
            # If not enough time has passed, sleep
            if elapsed < self.api_call_interval and self._last_api_call_time > 0:
                sleep_time = self.api_call_interval - elapsed
                time.sleep(sleep_time)
            
            # Update last API call time
            self._last_api_call_time = time.time()
    
    def call_openai_api(self, encoded_images, page_nums):
        """Call OpenAI API with the encoded image and return the response text"""
        
        # Build the prompt based on mode and language
        if self.is_summary_mode:
            if self.language == "English":
                system_prompt = "You are an AI assistant that summarizes content from images of PDF pages."
                user_prompt = f"This is page {page_nums[0]}" if len(page_nums) == 1 else f"These are pages {min(page_nums)}-{max(page_nums)}"
                user_prompt += " of a PDF document. Please summarize the key points in markdown format. Begin with the page number(s) as a header."
            else:
                system_prompt = "你是一个AI助手，用于总结PDF页面图像中的内容。"
                user_prompt = f"这是PDF文档的第{page_nums[0]}页" if len(page_nums) == 1 else f"这是PDF文档的第{min(page_nums)}-{max(page_nums)}页"
                user_prompt += "。请用Markdown格式总结关键要点。请以页码作为标题开始。"
        else:
            if self.language == "English":
                system_prompt = "You are an OCR assistant that extracts text from PDF page images. Preserve the original formatting including tables, equations, and hierarchical structure. Output in markdown format."
                user_prompt = f"This is page {page_nums[0]}" if len(page_nums) == 1 else f"These are pages {min(page_nums)}-{max(page_nums)}"
                user_prompt += " of a PDF document. Extract all text and formatted elements (tables, equations, etc.) faithfully preserving the original structure. Output in markdown format. Begin with the page number as a header and include ONLY the extracted content, no explanations or notes."
            else:
                system_prompt = "你是一个OCR助手，用于从PDF页面图像中提取文本。保留原始格式，包括表格、方程式和层次结构。以Markdown格式输出。"
                user_prompt = f"这是PDF文档的第{page_nums[0]}页" if len(page_nums) == 1 else f"这是PDF文档的第{min(page_nums)}-{max(page_nums)}页"
                user_prompt += "。提取所有文本和格式化元素（表格、方程式等），忠实保留原始结构。以Markdown格式输出。以页码作为标题开始，只包含提取的内容，不要有解释或注释。"
        
        # Build messages with images
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]
        
        # Add image content to the user message
        for encoded_image in encoded_images:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encoded_image}"
                }
            })
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 4096
        }
        
        response = requests.post(self.api_endpoint, headers=headers, data=json.dumps(data))
        
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            self.log(error_msg)
            raise Exception(error_msg)
        
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    
    def split_and_save_multi_page_response(self, response, page_nums):
        """Split a multi-page response and save each page to a separate file"""
        # Look for page headers like "# Page X" or "## Page X"
        import re
        
        # Try to split by page headers
        if self.language == "English":
            pattern = r'#+\s*Page\s+(\d+)'
        else:
            pattern = r'#+\s*第\s*(\d+)\s*页'
        
        matches = re.finditer(pattern, response, re.IGNORECASE)
        split_positions = []
        
        for match in matches:
            split_positions.append((match.start(), int(match.group(1))))
        
        # If no headers found, try to split evenly
        if not split_positions and len(page_nums) > 1:
            self.log(self.tr("Warning: No page headers found in multi-page response. Using heuristic splitting.") 
                   if self.language == "English" 
                   else "警告：在多页响应中未找到页面标题。使用启发式拆分。")
            
            lines = response.split('\n')
            lines_per_page = len(lines) // len(page_nums)
            
            for i, page_num in enumerate(page_nums):
                start_line = i * lines_per_page
                end_line = (i + 1) * lines_per_page if i < len(page_nums) - 1 else len(lines)
                page_content = '\n'.join(lines[start_line:end_line])
                
                # Add header if missing
                if self.language == "English":
                    header = f"# Page {page_num}\n\n"
                else:
                    header = f"# 第 {page_num} 页\n\n"
                
                if not page_content.strip().startswith('#'):
                    page_content = header + page_content
                
                output_path = os.path.join(self.md_dir, f"page_{page_num:04d}.md")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(page_content)
            
            return
        
        # Process each page based on split positions
        for i, (pos, page_num) in enumerate(split_positions):
            next_pos = split_positions[i+1][0] if i < len(split_positions) - 1 else len(response)
            page_content = response[pos:next_pos]
            
            output_path = os.path.join(self.md_dir, f"page_{page_num:04d}.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
            
            self.log(self.tr(f"Processed page {page_num}") if self.language == "English" else f"已处理第 {page_num} 页")
    
    def consolidate_markdown_files(self):
        """Combine all markdown files into a single consolidated file"""
        # Get all markdown files and sort them by page number
        md_files = [f for f in os.listdir(self.md_dir) if f.endswith('.md')]
        md_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        # Determine output filename from input PDF
        pdf_name = os.path.basename(self.pdf_path).split('.')[0]
        output_path = os.path.join(self.output_dir, f"{pdf_name}_consolidated.md")
        
        # Create header for consolidated file
        if self.language == "English":
            header = f"# {pdf_name}\n\n"
            header += f"Consolidated {'summary' if self.is_summary_mode else 'text extraction'} from {self.start_page} to {self.end_page}\n\n"
            header += f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
        else:
            header = f"# {pdf_name}\n\n"
            header += f"从第 {self.start_page} 页到第 {self.end_page} 页的{'摘要' if self.is_summary_mode else '文本提取'}整合\n\n"
            header += f"生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
        
        # Combine all files
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(header)
            
            for md_file in md_files:
                file_path = os.path.join(self.md_dir, md_file)
                with open(file_path, 'r', encoding='utf-8') as input_file:
                    content = input_file.read()
                    output_file.write(content)
                    output_file.write("\n\n---\n\n")  # Add separator between pages
        
        return output_path
    
    def tr(self, text):
        """Simple translation helper function"""
        # In a real app, this would use proper translation mechanisms
        return text
    
    def find_poppler_path(self):
        """Try to find poppler in common installation directories"""
        # Check if poppler is in PATH first
        if self.is_poppler_in_path():
            return None  # Use system PATH
            
        # Common installation directories
        possible_paths = [
            "C:\\Program Files\\poppler\\bin",
            "C:\\Program Files (x86)\\poppler\\bin",
            "C:\\poppler\\bin",
            os.path.expanduser("~\\poppler\\bin"),
            os.path.expanduser("~\\AppData\\Local\\poppler\\bin"),
        ]
        
        # Check for custom poppler location in app directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths.append(os.path.join(app_dir, "poppler", "bin"))
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isfile(os.path.join(path, "pdftoppm.exe")):
                self.log(self.tr(f"Found Poppler at: {path}") if self.language == "English" else f"在以下位置找到Poppler：{path}")
                return path
                
        return None
    
    def is_poppler_in_path(self):
        """Check if poppler is in system PATH"""
        paths = os.environ["PATH"].split(os.pathsep)
        for path in paths:
            if os.path.exists(os.path.join(path, "pdftoppm.exe")):
                return True
        return False