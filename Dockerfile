FROM python:3.11-bookworm

# Install Chromium and ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*


# Set environment so Selenium knows where Chromium is
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install notebook jupyterlab selenium

# Copy code
COPY . .

RUN curl https://rclone.org/install.sh | bash

CMD ["python", "run.py"]

