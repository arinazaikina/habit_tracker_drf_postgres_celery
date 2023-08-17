FROM python:3.10

RUN apt-get update && apt-get install -y lynx wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1

COPY . .
