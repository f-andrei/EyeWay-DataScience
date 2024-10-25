# Use the base image
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Set environment variables
ENV DISPLAY=$DISPLAY
ENV CUDA_CACHE_DISABLE=0

# Install additional system utilities and Python packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    kmod \
    python3-gi \
    python3-dev \
    python3-gst-1.0 \
    python3-opencv \
    python3-numpy \
    ffmpeg \
    nginx \
    lsof \
    libgstrtspserver-1.0-0 gstreamer1.0-rtsp \
    libgirepository1.0-dev \
    gobject-introspection gir1.2-gst-rtsp-server-1.0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install additional DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Copy the local wheel file into the Docker image
COPY pyds-1.1.11-py3-none-linux_x86_64.whl /tmp/pyds-1.1.11-py3-none-linux_x86_64.whl

# Install the pyds library from the local wheel file
RUN pip3 install /tmp/pyds-1.1.11-py3-none-linux_x86_64.whl cuda-python requests python-dotenv pytubefix flask yt_dlp cupy-cuda12x --ignore-installed

# Copy and configure Nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY stream.conf /etc/nginx/sites-available/stream.conf
RUN ln -s /etc/nginx/sites-available/stream.conf /etc/nginx/sites-enabled/

# Copy your application files
COPY . /opt/nvidia/deepstream/deepstream/sources/apps

# Set the working directory
WORKDIR /opt/nvidia/deepstream/deepstream/sources/apps
