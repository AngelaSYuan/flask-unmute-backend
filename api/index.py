import os
import io
import tempfile
import subprocess
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {"origins": "http://localhost:8000", "supports_credentials": True}
    },
)
# CORS(app)  # Enable CORS for all routes!
 

# Define your Symphonic Labs API key here or load it from environment variables
API_KEY = os.getenv("API_KEY")  # Ensure this is set in your environment


@app.route("/", methods=["GET"])
def root():
    return "Hello World"


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video_file = request.files["video"]
    video = io.BytesIO(video_file.read())

    try:
        url = "https://api.symphoniclabs.com/transcribe"
        files = {
            "video": ("input.webm", video, "video/webm"),
            "api_key": API_KEY,
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        transcribed_text = response.json().get("transcription", "")
        return jsonify({"transcription": transcribed_text})
    except requests.exceptions.RequestException as e:
        print("Error calling Symphonic Labs API:")
        return jsonify({"error": "Failed to transcribe video"}), 500


@app.route("/api/convert-to-mp4", methods=["POST"])
def convert_to_mp4():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files["video"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_input:
        video.save(temp_input)
        temp_input_path = temp_input.name

    temp_output_path = temp_input_path.replace(".webm", ".mp4")

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                temp_input_path,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                temp_output_path,
            ],
            check=True,
            capture_output=True,
        )
        return send_file(
            temp_output_path, as_attachment=True, download_name="converted_video.mp4"
        )
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return jsonify({"error": "Conversion failed", "details": e.stderr.decode()}), 500
    finally:
        os.unlink(temp_input_path)
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)


if __name__ == "__main__":
    app.run()
