import io
import os
from flask import Flask, render_template, request, send_file
import pdfplumber
from google.cloud import texttospeech
from datetime import datetime

app = Flask(__name__)

# Optional: max chars to send to TTS in one request (safety to avoid very large requests)
MAX_TTS_CHARS = 30000  # adjust if needed; Google quotas apply

# Initialize Google TTS client (requires GOOGLE_APPLICATION_CREDENTIALS env var)
tts_client = texttospeech.TextToSpeechClient()

def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from uploaded PDF bytes using pdfplumber (returns string)."""
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def synthesize_mp3_from_text(text, voice_name="en-US-Wavenet-D", speaking_rate=1.0):
    """
    Uses Google Cloud Text-to-Speech to synthesize MP3 bytes from text.
    Returns bytes (MP3).
    """
    if not text:
        raise ValueError("Empty text for synthesis.")

    if len(text) > MAX_TTS_CHARS:
        # Defensive: refuse huge requests to keep memory & quotas sane.
        raise ValueError(f"Text too long for single TTS request ({len(text)} chars). "
                         "Please upload a smaller PDF or split it.")

    # Build the input
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Select the voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name
    )

    # Select audio config (MP3)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate
    )

    # Perform the request
    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content  # bytes

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        uploaded = request.files.get("pdf_file")
        if not uploaded or uploaded.filename == "":
            error = "Please upload a PDF file."
            return render_template("index.html", error=error)

        if not uploaded.filename.lower().endswith(".pdf"):
            error = "Only PDF files are allowed."
            return render_template("index.html", error=error)

        try:
            pdf_bytes = uploaded.read()
            text = extract_text_from_pdf_bytes(pdf_bytes)
            if not text.strip():
                error = "No readable text found in the PDF (maybe it's scanned images)."
                return render_template("index.html", error=error)

            # optional: truncate / check length
            if len(text) > MAX_TTS_CHARS:
                # Option: send first N chars and warn, or return error to user.
                error = ("PDF text is very large. Please upload a smaller file or split the PDF. "
                         f"Extracted length: {len(text)} chars. Limit: {MAX_TTS_CHARS} chars.")
                return render_template("index.html", error=error)

            # Synthesize audio bytes (MP3)
            audio_bytes = synthesize_mp3_from_text(text)

            # Stream the bytes back as an MP3 file (no disk usage)
            audio_stream = io.BytesIO(audio_bytes)
            audio_stream.seek(0)
            download_name = f"pdf_audio_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.mp3"
            return send_file(
                audio_stream,
                as_attachment=True,
                download_name=download_name,
                mimetype="audio/mpeg"
            )

        except Exception as e:
            # For production you might log the traceback
            error = f"Conversion failed: {str(e)}"
            return render_template("index.html", error=error)

    return render_template("index.html", error=error)

if __name__ == "__main__":
    # port for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
