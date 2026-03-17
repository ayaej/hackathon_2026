FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download fr_core_news_sm

COPY . .

CMD ["python", "main.py"]