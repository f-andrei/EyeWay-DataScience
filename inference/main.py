import signal
from flask import Flask, jsonify, request # type: ignore
import subprocess
import os
from utils.preprocess_video import download_video, get_frame_rate, convert_to_15_fps


app = Flask(__name__)

def run_inference(video_source, input_type):
    try:
        print("Checking video frame rate...")
        frame_rate = get_frame_rate(video_source)

        if frame_rate != 15:
            base_name, ext = os.path.splitext(video_source)
            converted_video_source = f"{base_name}_15fps{ext}"
            if not os.path.exists(converted_video_source):
                print(f"Converting video to 15 FPS...")
                video_source = convert_to_15_fps(video_source, converted_video_source)
                print(f"Finished converting video to 15 FPS: {video_source}")

        if input_type == 'video':
            path_prefix = "file://"
        elif input_type == 'rtsp':
            path_prefix = ""
        
        video_source = path_prefix + video_source
        print("Running inference...")
        cmd = ['python3', '/opt/nvidia/deepstream/deepstream-7.0/sources/apps/inference/run_pipeline.py', 
               '-i', video_source, '-o', "rtsp"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr

    except Exception as e:
        print(f"Error during inference: {e}")
        return str(e), None
    
@app.route('/run-inference', methods=['POST'])
def run_inference_api():
    data = request.get_json()
    source = data.get('source')
    input_type = data.get('input_type')
    if input_type == 'video':
        source = download_video(source)

    stdout, stderr = run_inference(source, input_type)
    
    return jsonify({'success': True, 'output': stdout})


@app.route('/stop-inference', methods=['POST'])
def kill_inference():
    process_name = 'run_pipeline.py'

    try:
        ps_output = subprocess.check_output(f"ps aux | grep {process_name} | grep -v grep", shell=True)
        process_lines = ps_output.decode('utf-8').strip().split('\n')

        if not process_lines or process_lines[0] == '':
            return jsonify({"message": "No inference process found"}), 404

        for process_line in process_lines:
            process_details = process_line.split()
            pid = int(process_details[1])

            os.kill(pid, signal.SIGKILL)

        return jsonify({"message": "Inference process killed successfully"}), 200

    except subprocess.CalledProcessError:
        return jsonify({"error": "Error finding inference process"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
