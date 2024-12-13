import shutil
import subprocess
import os

def convert_rtsp_to_hls(stream_dir, loglevel='quiet'):    
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
        'ffmpeg', '-loglevel', loglevel, '-rtsp_transport', 'udp', '-fflags', 'nobuffer', 
        '-stimeout', '5000000', '-i', 'rtsp://user:pass@localhost:8554/live', 
        '-c:v', 'copy', '-c:a', 'copy', '-hls_time', '4', '-hls_list_size', '15', 
        '-hls_flags', 'delete_segments+program_date_time', '-flush_packets', '1', 
        '-start_number', '1', '-f', 'hls', f"{stream_dir}/stream.m3u8"
    ]
    subprocess.Popen(ffmpeg_cmd)