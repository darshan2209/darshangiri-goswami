web: gunicorn ai_twin_server:app --worker-class gthread --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
