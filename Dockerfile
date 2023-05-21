FROM python:3.10.9-slim

WORKDIR /code/bot

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./bot /code/bot

CMD ["python3", "bot.py"]