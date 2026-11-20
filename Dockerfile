# FixPilot session server + support dashboard (Cloud Run).
# Only the server side goes in the image: the AI agent runs on the customer's own PC, so no Gemini key is needed here.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/__init__.py server/main.py server/
COPY dashboard/ dashboard/
COPY kb/ kb/
COPY demo_app/ demo_app/
COPY pitch/ pitch/
COPY explainer/ explainer/

# Cloud Run sets PORT (8080); locally it falls back to 8080 too.
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
