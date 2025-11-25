from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import os
import io
import requests
import base64

app = Flask(__name__)

# Cấu hình
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Giới hạn 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    """Kiểm tra file có đúng định dạng không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ocr_with_api(image, language='vie+eng'):
    """Sử dụng OCR.space API miễn phí"""
    try:
        # Chuyển image sang base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Map ngôn ngữ
        lang_map = {
            'vie': 'vie',
            'eng': 'eng', 
            'vie+eng': 'vie+eng'
        }
        lang_code = lang_map.get(language, 'vie+eng')
        
        # Gọi OCR.space API
        payload = {
            'base64Image': f'data:image/png;base64,{img_str}',
            'apikey': 'K87283542388957',  # API key miễn phí
            'language': lang_code,
            'isOverlayRequired': False,
            'OCREngine': 2
        }
        
        response = requests.post('https://api.ocr.space/parse/image', data=payload, timeout=30)
        result = response.json()
        
        if result.get('IsErroredOnProcessing', False):
            return None, result.get('ErrorMessage', 'Unknown error from OCR API')
        else:
            parsed_text = result['ParsedResults'][0]['ParsedText']
            return parsed_text.strip(), None
            
    except Exception as e:
        return None, f"API Error: {str(e)}"

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/ocr', methods=['POST'])
def ocr():
    """API xử lý OCR"""
    try:
        # Kiểm tra có file không
        if 'image' not in request.files:
            return jsonify({'error': 'Không tìm thấy file ảnh'}), 400
        
        file = request.files['image']
        
        # Kiểm tra file có được chọn không
        if file.filename == '':
            return jsonify({'error': 'Chưa chọn file'}), 400
        
        # Kiểm tra định dạng file
        if not allowed_file(file.filename):
            return jsonify({'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, BMP'}), 400
        
        # Đọc ảnh từ file
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Lấy ngôn ngữ từ request
        lang = request.form.get('language', 'vie+eng')
        
        # Thực hiện OCR bằng API
        text, error = ocr_with_api(image, lang)
        
        if error:
            return jsonify({'error': f'Lỗi OCR: {error}'}), 500
        
        # Kiểm tra kết quả
        if not text or text.strip() == '':
            return jsonify({
                'text': '',
                'warning': 'Không phát hiện văn bản trong ảnh. Vui lòng thử ảnh khác có chữ rõ ràng hơn.'
            }), 200
        
        return jsonify({
            'text': text,
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500

@app.route('/health')
def health():
    """Kiểm tra trạng thái server"""
    return jsonify({'status': 'OK', 'ocr_engine': 'ocr.space_api'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
