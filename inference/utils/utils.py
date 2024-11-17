from utils.get_from_yt import find_stream
from utils.preprocess_video import get_frame_rate, convert_to_15_fps
import os
import shutil
import signal
import subprocess
import time

def get_source_uri(input_type, source):
    path_prefix = ""
    if input_type == "youtube_video":
        path_prefix = "file://"
        frame_rate = get_frame_rate(source)

        if frame_rate != 15 and not input_type == 'rtsp':
            base_name, ext = os.path.splitext(source)
            converted_source = f"{base_name}_15fps{ext}"
            if not os.path.exists(converted_source):
                source = convert_to_15_fps(source, converted_source)

    elif input_type == "youtube_stream":
        source = find_stream(source)
    elif input_type == "ip_camera":
        path_prefix = ""

    source_uri = path_prefix + source
    return source_uri

def is_rtsp_stream_live(rtsp_url, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1', rtsp_url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                print("RTSP Stream is live!")
                return True
        except Exception as e:
            print(f"Error checking RTSP stream: {e}")
        time.sleep(1)
    return False

def is_hls_stream_live(hls_path, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(hls_path):
            print("HLS Stream is live!")
            return True
        time.sleep(1)
    return False


def kill_inference_process():
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
        print("Inference process killed successfully")
        return "Inference process killed successfully"

    except subprocess.CalledProcessError:
        return "Error finding inference process"
    except Exception as e:
        return str(e)
    
def cleanup_stream_files(stream_dir):
    try:
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
            return "Stream files deleted successfully."
        else:
            return "Stream directory does not exist"
    except Exception as e:
        return str(e)