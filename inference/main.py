import signal
import sys
import time
from flask import Flask, jsonify, request  # type: ignore
import subprocess
import os
from utils.convert_rtsp_to_hls import convert_rtsp_to_hls
from utils.preprocess_video import get_frame_rate, convert_to_15_fps
from utils.get_from_yt import find_stream, download_video
from utils.utils import is_hls_stream_live, kill_inference_process, cleanup_stream_files, is_rtsp_stream_live
from flask_cors import CORS
from configs.constants import *


app = Flask(__name__)
CORS(app)

@app.route('/run-inference', methods=['POST'])
def run_inference_api():
    data = request.get_json()
    source = data.get('source')
    input_type = data.get('input_type')
    source_uri = get_source_uri(input_type, source)
    
    if not source:
        return jsonify({'success': False, 'output': 'Error downloading video'}), 500
    
    stdout, stderr = run_inference(source_uri)
    
    return jsonify({'success': True, 'output': stdout})


@app.route('/stop-inference', methods=['POST'])
def kill_inference():
    try:
        kill_inference_process()
        cleanup_stream_files(HLS_OUTPUT_PATH)
        return jsonify({"message": "Inference process killed and stream files removed successfully"}), 200

    except subprocess.CalledProcessError:
        return jsonify({"error": "Error finding inference process"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

stream_status = {"hls_live": False}

@app.route('/stream-status', methods=['GET'])
def get_stream_status():
    return jsonify(stream_status)


def run_inference(source_uri):
    global stream_status
    try:
        kill_inference_process()
        print("Running inference...")
        cmd = [
            'python3',
            '-u',  # Unbuffered output
            '/opt/nvidia/deepstream/deepstream-7.0/sources/apps/inference/run_pipeline.py',
            '-i', source_uri,
            '-o', "rtsp"
        ]
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
        process.communicate()
        
        rtsp_url = "rtsp://user:pass@localhost:8554/live"
        if is_rtsp_stream_live(rtsp_url):
            convert_rtsp_to_hls(HLS_OUTPUT_PATH)
            
            hls_playlist_path = os.path.join(HLS_OUTPUT_PATH, "stream.m3u8")
            if is_hls_stream_live(hls_playlist_path):
                stream_status["hls_live"] = True
                return "Inference started and HLS stream is live", None
            else:
                stream_status["hls_live"] = False
                return "Inference started but HLS stream is not live", None
        else:
            stream_status["hls_live"] = False
            return "Inference started but RTSP stream is not live", None

    except Exception as e:
        print(f"Error during inference: {e}")
        stream_status["hls_live"] = False
        return str(e), None


def get_source_uri(input_type, source):
    path_prefix = ""
    if input_type == "yt_video":
        path_prefix = "file://"
        frame_rate = get_frame_rate(source)

        if frame_rate != 15 and not input_type == 'rtsp':
            base_name, ext = os.path.splitext(source)
            converted_source = f"{base_name}_15fps{ext}"
            if not os.path.exists(converted_source):
                source = convert_to_15_fps(source, converted_source)

    elif input_type in ["yt_stream"]:
        source = find_stream(source)
    elif input_type == "rtsp":
        path_prefix = ""

    source_uri = path_prefix + source
    return source_uri

if __name__ == '__main__':
    app.run(debug=True)
