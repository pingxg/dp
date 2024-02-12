# Use Python 3.10 on Ubuntu as the base image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy your web automation scripts and other necessary files into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install wget, unzip for Chrome installation, and any other dependencies
# Also install dependencies required by remote_syslog2
RUN apt update -y && apt install -y \
    libgl1-mesa-glx \
    sudo \
    chromium \
    chromium-driver \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/logs && touch /app/logs/application.log

# Download and install remote_syslog2
RUN wget https://github.com/papertrail/remote_syslog2/releases/download/v0.21/remote_syslog_linux_amd64.tar.gz \
    && tar -xzf remote_syslog_linux_amd64.tar.gz -C /usr/local/bin --strip-components=1 \
    && rm remote_syslog_linux_amd64.tar.gz

RUN apt-get update && apt-get install -y supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY remote_syslog.yml /etc/log_files.yml


COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
