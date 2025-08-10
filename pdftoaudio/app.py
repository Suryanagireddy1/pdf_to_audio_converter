import os
import uuid
from flask import Flask, request, render_template, send_file
import pyttsx3
import pdfplumber

app = Flask(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "pdf" not in request.files:
            return "No file uploaded", 400
        
        pdf_file = request.files["pdf"]
        text_content = ""

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text_content += page.extract_text() or ""

        if not text_content.strip():
            return "No text found in PDF", 400

        # Generate unique audio file path
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        # Convert text to audio
        engine = pyttsx3.init()
        engine.save_to_file(text_content, audio_path)
        engine.runAndWait()

        # Ensure file exists before sending
        if not os.path.exists(audio_path):
            return "Audio generation failed", 500

        return send_file(audio_path, as_attachment=True, download_name="output.mp3")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
