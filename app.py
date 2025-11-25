from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import os
import io

app = Flask(__name__)

# Cấu hình
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Giới hạn 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Cấu hình Tesseract (Windows)
# Nếu dùng Windows, bỏ comment dòng dưới và điều chỉnh đường dẫn
try:
    import tesseract
    # pytesseract-pack sẽ tự động xử lý
except ImportError:
    # Fallback cho local development
    if os.name == 'nt':  # Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def allowed_file(filename):
    """Kiểm tra file có đúng định dạng không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        # Lấy ngôn ngữ từ request (mặc định là tiếng Việt + tiếng Anh)
        lang = request.form.get('language', 'vie+eng')
        
        # Thực hiện OCR
        try:
            text = pytesseract.image_to_string(image, lang=lang)
        except pytesseract.TesseractNotFoundError:
            return jsonify({'error': 'Tesseract chưa được cài đặt hoặc không tìm thấy. Vui lòng cài đặt Tesseract OCR.'}), 500
        except Exception as e:
            return jsonify({'error': f'Lỗi khi xử lý OCR: {str(e)}'}), 500
        
        # Kiểm tra kết quả
        if not text or text.strip() == '':
            return jsonify({
                'text': '',
                'warning': 'Không phát hiện văn bản trong ảnh. Vui lòng thử ảnh khác có chữ rõ ràng hơn.'
            }), 200
        
        return jsonify({
            'text': text.strip(),
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Lỗi server: {str(e)}'}), 500

@app.route('/health')
def health():
    """Kiểm tra trạng thái server"""
    try:
        # Kiểm tra Tesseract có hoạt động không
        pytesseract.get_tesseract_version()
        return jsonify({'status': 'OK', 'tesseract': 'installed'}), 200
    except:
        return jsonify({'status': 'OK', 'tesseract': 'not found'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
