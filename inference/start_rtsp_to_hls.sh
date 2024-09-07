# Remove old files
rm -rf /opt/nvidia/deepstream/deepstream/sources/apps/stream/*

# Start FFmpeg to stream and create HLS
ffmpeg -rtsp_transport tcp -fflags nobuffer -stimeout 10000000  -i rtsp://user:pass@localhost:8554/live  -c:v copy -c:a copy  -hls_time 2 -hls_list_size 10 -hls_flags delete_segments  -start_number 1  -f hls /opt/nvidia/deepstream/deepstream-7.0/sources/apps/stream/stream.m3u8


