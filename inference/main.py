import signal
import time
from flask import Flask, jsonify, request  # type: ignore
import subprocess
import os
from utils.preprocess_video import download_video, get_frame_rate, convert_to_15_fps
import shutil

app = Flask(__name__)

def run_inference(video_source, input_type):
    try:
        print(kill_process())
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
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(7)  

        stream_dir = "/opt/nvidia/deepstream/deepstream-7.0/sources/apps/inference/stream"
        if not os.path.exists(stream_dir):
            os.makedirs(stream_dir)

        for filename in os.listdir(stream_dir):
            file_path = os.path.join(stream_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path) 
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path) 
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")


        ffmpeg_cmd = [
            'ffmpeg', '-rtsp_transport', 'tcp', '-fflags', 'nobuffer', '-stimeout', '10000000',
            '-i', 'rtsp://user:pass@localhost:8554/live', '-c:v', 'copy', '-c:a', 'copy',
            '-hls_time', '2', '-hls_list_size', '10', '-hls_flags', 'delete_segments',
            '-start_number', '1', '-f', 'hls', f"{stream_dir}/stream.m3u8"
        ]
        subprocess.Popen(ffmpeg_cmd)

        return "Inference started", None

    except Exception as e:
        print(f"Error during inference: {e}")
        return str(e), None


def kill_process():
    process_name = 'run_pipeline.py'
    try:
        ps_output = subprocess.check_output(f"ps aux | grep {process_name} | grep -v grep", shell=True)
        process_lines = ps_output.decode('utf-8').strip().split('\n')

        if not process_lines or process_lines[0] == '':
            return "No inference process found"

        for process_line in process_lines:
            process_details = process_line.split()
            pid = int(process_details[1])
            os.kill(pid, signal.SIGKILL)

        return "Inference process killed successfully"

    except subprocess.CalledProcessError:
        return "Error finding inference process"
    except Exception as e:
        return str(e)

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
    stream_dir = "/opt/nvidia/deepstream/deepstream/sources/apps/inference/stream"

    try:
        print(kill_process())

        if os.path.exists(stream_dir):
            print(f"Removing stream files from {stream_dir}...")
            for filename in os.listdir(stream_dir):
                file_path = os.path.join(stream_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path) 
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            print("Stream files deleted successfully.")

        return jsonify({"message": "Inference process killed and stream files removed successfully"}), 200

    except subprocess.CalledProcessError:
        return jsonify({"error": "Error finding inference process"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
