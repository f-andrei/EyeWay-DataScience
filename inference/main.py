# type: ignore
from utils.utils import is_hls_stream_live, kill_inference_process, cleanup_stream_files, is_rtsp_stream_live
from utils.generate_line_crossing_conf import generate_nvdsanalytics_config_file
from utils.convert_rtsp_to_hls import convert_rtsp_to_hls
from flask import Flask, jsonify, request
from utils.utils import get_source_uri
from utils.constants import *
from flask_cors import CORS 
import subprocess
import threading
import time
import sys
import os

app = Flask(__name__)
CORS(app)

@app.route('/run-inference', methods=['POST'])
def run_inference_api():
    data = request.get_json()
    camera_id, camera_name, source, input_type = (
        data.get('camera_id'),
        data.get('camera_name'),
        data.get('source'),
        data.get('input_type')
    ) 
    
    source_uri = get_source_uri(input_type, source)
    source_nvdsnalytics_config_file = generate_nvdsanalytics_config_file(camera_name)

    if not source:
        return jsonify({'success': False, 'output': 'Error downloading video'}), 500
    
    stdout, stderr = run_inference(source_uri, source_nvdsnalytics_config_file, camera_id)
    
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


def run_inference(source_uri, nvdsanalytics_config_file, camera_id):
    global stream_status
    try:
        kill_inference_process()
        print("Running inference...")
        cmd = [
            'python3',
            '-u',
            '/apps/inference/run_pipeline.py',
            '-i', source_uri,
            '-o', "rtsp",
            '-c', nvdsanalytics_config_file,
            '-id', str(camera_id)
        ]
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
        
        threading.Thread(target=process.communicate).start()
        
        rtsp_url = "rtsp://user:pass@localhost:8554/live"
        
        max_retries = 5
        for _ in range(max_retries):
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
                time.sleep(5)  
        
        stream_status["hls_live"] = False
        return "Inference started but RTSP stream is not live", None
    except Exception as e:
        print(f"Error during inference: {e}")
        stream_status["hls_live"] = False
        return str(e), None


if __name__ == '__main__':
    app.run(debug=True)
