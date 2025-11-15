from flask import Flask, request, jsonify
import PyPDF2
import re
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # ✅ Allow requests from your React frontend (localhost:3000)

UPLOAD_FOLDER = './tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Extract text from PDF
def pdf_to_text(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
    return text

# ✅ Extract abstract from text
def extract_abstract_from_text(text):
    text = re.sub(r'\s+', ' ', text)
    intro_matches = [m.start() for m in re.finditer(r'\bIntroduction\b', text, re.IGNORECASE)]
    abstract_start = re.search(r'\bAbstract\b', text, re.IGNORECASE)

    abstract = "Abstract not found."

    if abstract_start and len(intro_matches) >= 2:
        start_index = abstract_start.end()
        end_index = intro_matches[1]
        abstract = text[start_index:end_index].strip()
    elif abstract_start and len(intro_matches) == 1:
        start_index = abstract_start.end()
        end_index = intro_matches[0]
        abstract = text[start_index:end_index].strip()

    return abstract


# ✅ Flask route for handling file upload and extraction
@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        text = pdf_to_text(file_path)
        if not text.strip():
            return jsonify({'success': False, 'error': 'No extractable text found'}), 400

        abstract = extract_abstract_from_text(text)
        return jsonify({'success': True, 'text': abstract})

    except Exception as e:
        print("❌ Error during extraction:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
     port = int(os.environ.get("PORT", 8080))
     app.run(host='0.0.0.0', port=port)