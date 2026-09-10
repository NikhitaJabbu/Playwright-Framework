# Official Playwright Python image already has all three browsers plus
# their OS-level dependencies preinstalled -- building this on a bare
# python:3.11 image means separately apt-installing ~30 browser
# dependency packages, which is what most tutorials skip and then their
# Docker instructions don't actually work.
FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENV=dev \
    HEADLESS=true \
    PYTHONUNBUFFERED=1

# Default command runs the smoke suite; override at `docker run` time,
# e.g. `docker run <image> pytest -m regression --browser firefox`
CMD ["pytest", "-m", "smoke", "-v"]
