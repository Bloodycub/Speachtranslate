from flask import Flask, request, jsonify, render_template
import os
import wave
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import logging
import subprocess

logging.basicConfig(level=logging.DEBUG)

# Set the path for ffmpeg
ffmpeg_path = r"B:\git_addons\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = r"B:\git_addons\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe"

# Add ffmpeg to the PATH environment variable
os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.path.dirname(ffmpeg_path)
print("FFMPEG Path:", ffmpeg_path)

# Initialize Flask app
app = Flask(__name__)

# Load the VOSK model
MODEL_PATH = r"C:\Users\USERNAME\.cache\vosk\vosk-model-small-ru-0.22"  # Change the username as needed
model = Model(MODEL_PATH)
SAMPLE_RATE = 16000  # VOSK model sample rate

# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_webm_to_wav(webm_file):
    """Convert the webm audio file to wav using ffmpeg."""
    try:
        wav_file_path = os.path.join(UPLOAD_FOLDER, "converted_audio.wav")
        # Run ffmpeg to convert to WAV with mono, 16kHz sample rate
        command = [
            ffmpeg_path,
            "-i", webm_file,           # Input file
            "-ac", "1",                # Set to mono (1 channel)
            "-ar", str(SAMPLE_RATE),   # Set sample rate to 16kHz
            wav_file_path              # Output file
        ]
        subprocess.run(command, check=True)
        print(f"Converted WAV file saved at: {wav_file_path}")
        return wav_file_path
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error converting file: {str(e)}")

def transcribe_audio(file_path):
    """Transcribe audio file using VOSK."""
    wf = wave.open(file_path, "rb")
    
    # Print detailed file properties
    print(f"File info: Channels={wf.getnchannels()}, Sample Width={wf.getsampwidth()}, Frame Rate={wf.getframerate()} Hz")
    
    # Validate WAV file format
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != SAMPLE_RATE:
        raise ValueError("Audio file must be WAV format mono PCM with 16kHz sample rate.")
    
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    transcription = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            transcription += recognizer.Result()

    transcription += recognizer.FinalResult()
    wf.close()
    return transcription

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    """Handle audio file upload and transcription."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        filename = audio_file.filename
        print(f"File uploaded: {filename}")
        
        # Validate file extension
        if not filename.endswith(".webm"):
            return jsonify({"error": "Only .webm files are supported"}), 400
        
        # Save the uploaded file
        webm_file_path = os.path.join(UPLOAD_FOLDER, "recording.webm")
        audio_file.save(webm_file_path)

        # Check if file was saved successfully
        if os.path.exists(webm_file_path):
            print("File saved successfully.")
        else:
            print("File save failed.")
            return jsonify({"error": "Failed to save the file"}), 500

        # Convert the uploaded webm file to wav
        wav_file_path = convert_webm_to_wav(webm_file_path)

        # Transcribe the converted wav file
        transcription = transcribe_audio(wav_file_path)

        # Clean up the uploaded and converted files
        os.remove(webm_file_path)
        os.remove(wav_file_path)

        return jsonify({"transcription": transcription})

    except Exception as e:
        print(f"Error: {str(e)}")  # Print the error traceback for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
