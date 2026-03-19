FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y poppler-utils

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_sm
RUN python -c "import easyocr; easyocr.Reader(['fr'], gpu=False)"

COPY src ./src

CMD ["python", "-m", "src.ocr_module.main"]