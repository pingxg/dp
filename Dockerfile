# Use Ubuntu as the base image
FROM ubuntu:latest

# Install wget, unzip for Chrome installation and any other dependencies
RUN apt-get update && apt-get install -y wget unzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

# Copy your web automation scripts into the container
COPY . /app

# Set the working directory to where you've copied your scripts
WORKDIR /app

# Install any Python dependencies for your script, if necessary
RUN apt-get update && apt-get install -y python3 python3-pip

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80
# Command to run your script (adjust as necessary)
# CMD ["python3", "bw.py"]
CMD ["whereis", "google-chrome-stable"]
