import yt_dlp # type: ignore
from pytubefix import YouTube # type: ignore
from pytubefix.cli import on_progress # type: ignore
import re

ydl_opts = {}

def check_stream(data):
    max_height = 1080
    max_fps = 30
    
    streams = data.get('formats', [])[::-1]
    
    for fmt in streams:
        try:
            if (fmt.get('vcodec', 'none') != 'none' and 
                fmt.get('acodec') == 'none' and
                fmt.get('height', 0) <= max_height and
                fmt.get('fps', 0) <= max_fps):
                
                return {
                    'format_id': fmt['format_id'],
                    'ext': fmt['ext'],
                    'requested_formats': [fmt],
                    'protocol': fmt['protocol']
                }
        except KeyError:
            continue
    return None

def find_stream(url):
    def format_getter(ctx):
        result = check_stream(ctx)
        if result:
            yield result
            
    opts = {'format': format_getter}
    
    with yt_dlp.YoutubeDL(opts) as dl:
        data = dl.extract_info(url, download=False)
        return data.get('requested_formats', [])[0].get('url')

def download_video(url):
    try:
        print("Downloading video...")
        yt = YouTube(url, on_progress_callback=on_progress)
        title = yt.title
        filename = re.sub(r'[^a-zA-Z0-9]', '', title).replace('.', '').replace(',', '') + ".mp4"
        ys = yt.streams.get_highest_resolution()
        output_path = "../assets"
        output =  ys.download(output_path=output_path, filename=filename, skip_existing=True)
        return output
    except Exception as e:
        print("Could not download video ", e)
        return None