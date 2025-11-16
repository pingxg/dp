# Stage 1: Build layer with Chromium + Chromedriver
FROM public.ecr.aws/lambda/python:3.10 AS stage

# Tools needed to download/unzip browser
RUN yum install -y -q sudo unzip curl && yum clean all

# Chromium snapshot ID (from CloudBytes article)
# You can change this later if needed.
ENV CHROMIUM_VERSION=1002910

# Copy and run the browser install script
COPY install-browser.sh /tmp/install-browser.sh
RUN chmod +x /tmp/install-browser.sh \
    && /usr/bin/bash /tmp/install-browser.sh


# Stage 2: Final Lambda image
FROM public.ecr.aws/lambda/python:3.10 AS base

# Install all Chromium dependencies
COPY chrome-deps.txt /tmp/chrome-deps.txt
RUN yum install -y $(cat /tmp/chrome-deps.txt) && yum clean all

# Workdir is /var/task in Lambda images
WORKDIR /var/task

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bring Chromium + Chromedriver from stage image
COPY --from=stage /opt/chrome /opt/chrome
COPY --from=stage /opt/chromedriver /opt/chromedriver

# Copy the rest of your app (including main.py, drivers/, etc.)
COPY . .

# Optional: ensure logs dir exists
RUN mkdir -p /var/task/logs

# Lambda handler
CMD ["main.lambda_handler"]
