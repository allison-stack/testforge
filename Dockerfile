# Sandbox image for the Executor agent.
#
# Why pre-bake a custom image instead of using `python:3.12-slim` directly?
#   Each Executor call does `pip install pytest`. That's ~5 seconds per run.
#   You'll do hundreds of runs. Pre-installing pytest cuts that to <1s.
#
# Build once: `docker build -t testforge-sandbox .`
# Then executor.py runs containers FROM this image.

FROM python:3.12-slim
WORKDIR /work
RUN pip install --no-cache-dir pytest==9.0.3

# No CMD — the Executor passes the command at `docker run` time.
