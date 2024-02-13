# Use Python 3.10 on Ubuntu as the base image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy your web automation scripts and other necessary files into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install wget, unzip for Chrome installation, and any other dependencies
RUN apt update -y && apt install -y \
    libgl1-mesa-glx \
    sudo \
    chromium \
    chromium-driver \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy the supervisord config file to /etc/supervisor/conf.d/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
