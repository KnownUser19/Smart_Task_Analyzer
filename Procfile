web: cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn task_analyzer.wsgi --bind 0.0.0.0:$PORT
