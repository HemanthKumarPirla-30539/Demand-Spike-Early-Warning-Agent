FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Use the PORT environment variable assigned by Render
ENV PORT 8501

CMD streamlit run app_with_txt.py --server.port=$PORT --server.address=0.0.0.0
