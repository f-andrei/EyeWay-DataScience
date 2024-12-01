# Base image
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch

# Set environment variables
ENV CUDA_CACHE_DISABLE=0

# Install system dependencies
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
    libgstrtspserver-1.0-0 \
    gstreamer1.0-rtsp \
    libgirepository1.0-dev \
    gobject-introspection \
    gir1.2-gst-rtsp-server-1.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install DeepStream plugins
RUN bash /opt/nvidia/deepstream/deepstream/user_additional_install.sh

# Copy and install pyds wheel file
COPY pyds-1.2.0-py3-none-linux_x86_64.whl /tmp/
RUN pip3 install /tmp/pyds-1.2.0-py3-none-linux_x86_64.whl \
    cuda-python \
    requests \
    python-dotenv \
    pytubefix \
    flask \
    flask_cors \
    yt_dlp \
    cupy-cuda12x \
    pillow \
    --ignore-installed

# Configure Nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY stream.conf /etc/nginx/sites-available/stream.conf
RUN ln -s /etc/nginx/sites-available/stream.conf /etc/nginx/sites-enabled/

# Set up application directory
RUN mkdir -p /apps
COPY . /apps
WORKDIR /apps

# Copy and set up entrypoint script
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["entrypoint.sh"]
CMD ["/bin/bash"]