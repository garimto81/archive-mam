FROM gitpod/workspace-python-3.9

# Install system dependencies
RUN sudo apt-get update && sudo apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && sudo rm -rf /var/lib/apt/lists/*

# Pre-install Python packages
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

USER gitpod