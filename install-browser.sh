#!/bin/bash
set -e

echo "Downloading Chromium snapshot ${CHROMIUM_VERSION}..."

# Chromium (Linux_x64 snapshot)
curl "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/\
Linux_x64%2F${CHROMIUM_VERSION}%2Fchrome-linux.zip?alt=media" \
  -o /tmp/chromium.zip

unzip /tmp/chromium.zip -d /tmp/
mv /tmp/chrome-linux /opt/chrome
rm /tmp/chromium.zip

echo "Downloading Chromedriver snapshot ${CHROMIUM_VERSION}..."

curl "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/\
Linux_x64%2F${CHROMIUM_VERSION}%2Fchromedriver_linux64.zip?alt=media" \
  -o /tmp/chromedriver_linux64.zip

unzip /tmp/chromedriver_linux64.zip -d /tmp/
mv /tmp/chromedriver_linux64/chromedriver /opt/chromedriver
rm /tmp/chromedriver_linux64.zip

chmod +x /opt/chrome/chrome /opt/chromedriver

echo "Chromium & Chromedriver installed under /opt"
