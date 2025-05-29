FROM python:3.8
ENV DockerHOME=/home/app/bot

RUN mkdir -p $DockerHOME

WORKDIR $DockerHOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY .. $DockerHOME
RUN pip install -r requirements.txt
CMD python index.py