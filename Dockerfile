# # Use Ubuntu as the base image
# FROM python:3.10

# # Set the working directory to where you've copied your scripts
# WORKDIR /app

# # Copy your web automation scripts into the container
# COPY . /app


# # Install any needed packages specified in requirements.txt
# RUN pip3 install --no-cache-dir -r requirements.txt

# # Install wget, unzip for Chrome installation and any other dependencies
# RUN apt update -y && apt install libgl1-mesa-glx sudo chromium chromium-driver -y
#     # apt-get install -y chromium

# RUN apt-get install -y libglib2.0 libnss3 libgconf-2-4 libfontconfig1 chromium-driver



# # Command to run your script (adjust as necessary)
# CMD ["python", "main.py"]


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


# Assuming you have a configuration file for remote_syslog2 named remote_syslog.yml in your project directory
# Make sure this file configures remote_syslog2 to watch the correct log files and points to your Papertrail destination
COPY remote_syslog.yml /etc/log_files.yml


COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]

# # Start remote_syslog in the background and then run your script
# # Note: Adjust the CMD as necessary to start remote_syslog2 with your specific options if not using a config file
# CMD remote_syslog -D --configfile /etc/log_files.yml

# CMD ["python", "/app/main.py"]
