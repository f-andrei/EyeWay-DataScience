
import subprocess


def get_frame_rate(video_path):
    print("Checking video frame rate...")
    try:
        cmd = ['ffprobe', '-v', '0', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
               '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        frame_rate_str = result.stdout.strip()
        num, denom = map(int, frame_rate_str.split('/'))
        frame_rate = num / denom
        print(f"Frame rate: {frame_rate}")
        return frame_rate
    except Exception as e:
        print(f"Error getting frame rate: {e}")
        return None

def convert_to_15_fps(video_path, output_path):
    try:
        print("Converting video to 15 FPS...")
        cmd = ['ffmpeg', '-i', video_path, '-r', '15', '-c:v', 'h264_nvenc', '-preset', 'fast', output_path]
        subprocess.run(cmd, capture_output=True, text=True)
        return output_path
    except Exception as e:
        print(f"Error converting video: {e}")
        return None



