FROM python:3.9

# Create non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the app folder
COPY --chown=user ./app /app/app

# Run uvicorn pointing to your FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
