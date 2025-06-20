FROM python:3.12
WORKDIR /app
COPY req.txt ./req.txt
RUN pip install --no-cache-dir -r req.txt
COPY ToDo/ .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]