from flask import Flask, render_template, request, send_file
import pdfplumber
from gtts import gTTS
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "static/audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf_file = request.files.get("pdf_file")

        if not pdf_file or pdf_file.filename == "":
            return render_template("index.html", error="Please upload a PDF file.")

        # Save uploaded PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(pdf_path)

        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            return render_template("index.html", error="No text found in the PDF.")

        # Generate audio filename
        audio_filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

        # Convert text to speech
        tts = gTTS(text=text, lang='en')
        tts.save(audio_path)

        return send_file(audio_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # For cloud platforms
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
