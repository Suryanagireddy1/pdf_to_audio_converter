from flask import Flask, render_template, request, send_file
import pdfplumber
from gtts import gTTS
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "pdf_file" not in request.files:
            return render_template("index.html", error="No file uploaded")

        pdf_file = request.files["pdf_file"]

        if pdf_file.filename == "":
            return render_template("index.html", error="Please select a PDF file.")

        if pdf_file and pdf_file.filename.lower().endswith(".pdf"):
            file_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
            pdf_file.save(file_path)

            # Extract text
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            if not text.strip():
                return render_template("index.html", error="No readable text found in PDF.")

            # Convert text to audio
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
            tts = gTTS(text)
            tts.save(audio_path)

            return send_file(audio_path, as_attachment=True, download_name="output.mp3")

        return render_template("index.html", error="Only PDF files are allowed.")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
