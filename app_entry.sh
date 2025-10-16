#!/usr/bin/env bash
set -e

# Default to 8501 if PORT not provided by the platform
PORT="${PORT:-8501}"

# Run Streamlit
exec streamlit run fire_app_eli.py --server.port="$PORT" --server.address=0.0.0.0
