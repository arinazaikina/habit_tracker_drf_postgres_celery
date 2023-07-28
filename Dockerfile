FROM python:3.10

RUN apt-get update && apt-get install -y lynx wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /usr/wait-for-it.sh
RUN chmod +x /usr/wait-for-it.sh
