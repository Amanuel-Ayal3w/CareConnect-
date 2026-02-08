#!/bin/bash
# Run both FastAPI backend and Streamlit frontend

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
uv run uvicorn backend.api:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit frontend
echo "Starting Streamlit frontend on port 8501..."
uv run streamlit run frontend/app.py --server.port 8501

# Cleanup: kill backend when Streamlit stops
kill $BACKEND_PID
