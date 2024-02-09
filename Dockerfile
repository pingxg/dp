# Use Ubuntu as the base image
FROM python:3.10

# Set the working directory to where you've copied your scripts
WORKDIR /app

# Copy your web automation scripts into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install wget, unzip for Chrome installation and any other dependencies
RUN apt update -y && apt install libgl1-mesa-glx sudo chromium chromium-driver -y
    # apt-get install -y chromium

RUN apt-get install -y libglib2.0 libnss3 libgconf-2-4 libfontconfig1 chromium-driver


# Command to run your script (adjust as necessary)
CMD ["python", "main.py"]
