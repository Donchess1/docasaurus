FROM python:3.10-slim-bullseye

WORKDIR /app
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client default-libmysqlclient-dev netcat build-essential libpq-dev pkg-config && \
    apt-get clean

RUN pip install --upgrade pip
COPY ./requirements ./requirements
RUN pip install psycopg2-binary --no-binary psycopg2-binary
RUN pip install -r requirements/dev.txt
COPY ./docker/staging/entrypoint.sh /entrypoint.sh

COPY . .

RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
