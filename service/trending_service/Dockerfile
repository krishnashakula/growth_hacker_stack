# ---- Base Stage ----
# Use an official Python runtime as a parent image
# Using a specific version is good practice for reproducibility
# Slim images are smaller and have fewer vulnerabilities
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Poetry or pip configuration can go here if needed
# ENV POETRY_NO_INTERACTION=1 \
#     POETRY_VIRTUALENVS_CREATE=false \
#     POETRY_CACHE_DIR='/var/cache/pypoetry' \
#     PIP_NO_CACHE_DIR=off \
#     PIP_DISABLE_PIP_VERSION_CHECK=on

# Set the working directory in the container
WORKDIR /app

# ---- Builder Stage ----
# This stage is for installing dependencies
FROM base as builder

# Install build dependencies and curl for health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir can reduce image size slightly
# Using a virtual environment within the Docker image is a good practice,
# but for simple services, installing directly can also work.
# Here, we install globally in this stage.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Runner Stage ----
# This is the final stage for the production image
FROM base as runner

# Create a non-root user and group
# Running as non-root is a security best practice
ARG APP_USER=appuser
ARG APP_GROUP=appgroup
ARG APP_UID=1001
ARG APP_GID=1001
RUN groupadd -g ${APP_GID} ${APP_GROUP} && \
    useradd -u ${APP_UID} -g ${APP_GROUP} -s /bin/sh -m ${APP_USER}

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code into the container
# Ensure that only necessary files are copied to keep the image lean
COPY main.py .
# If you have other modules or files in the service/trending_service directory:
# COPY ./other_module.py .
# COPY ./static ./static

# Change ownership of the app directory to the non-root user
RUN chown -R ${APP_USER}:${APP_GROUP} /app

# Switch to the non-root user
USER ${APP_USER}

# Expose the port the app runs on
# This should match the APP_PORT in your main.py settings (default 8000)
EXPOSE 8000

# Define the command to run the application
# Uvicorn is a good choice for FastAPI.
# --host 0.0.0.0 makes it accessible from outside the container.
# --port 8000 should match the EXPOSE instruction and your app's configuration.
# The number of workers can be tuned based on your server's CPU cores.
# Example: For a 2-core machine, 2 * 2 + 1 = 5 workers.
# Uvicorn's default is 1 worker. For more, consider Gunicorn as a process manager for Uvicorn workers.
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
# For production, you might use Gunicorn to manage Uvicorn workers:
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "./gunicorn_conf.py", "main:app"]
# For simplicity with Uvicorn directly:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Healthcheck (optional, but good practice)
# This should match the /health endpoint in your FastAPI app.
# The port 8000 should match the EXPOSE and CMD port.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

