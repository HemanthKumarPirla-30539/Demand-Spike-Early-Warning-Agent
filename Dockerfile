FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501
EXPOSE 8000

CMD ["streamlit", "run", "app_with_txt.py", "--server.port=8501", "--server.address=0.0.0.0"]
