FROM python:3.12.4-slim
LABEL maintainer="vetali5700@gmail.com"

ENV PYTHOUNNBUFFERED 1

WORKDIR app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /app/media/uploads

RUN adduser \
    --disabled-password \
    --no-create-home \
    django_user

RUN chown -R django_user /app/media/uploads/profile
RUN chown -R django_user /app/media/uploads/post
RUN chmod -R 755 /app/media/uploads/profile
RUN chmod -R 755 /app/media/uploads/post

USER django_user
