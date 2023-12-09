# pull official base image
FROM python:3.13.0a1-alpine

# set work directory
WORKDIR /bot
COPY . /bot

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_NO_CACHE_DIR=off

# install compiler
RUN apk add -U --no-cache gcc build-base linux-headers ca-certificates python3-dev libffi-dev libressl-dev libxslt-dev

# install poetry (dependency resolver) 
RUN pip install poetry
# disable creating .venv
RUN poetry config virtualenvs.create false
# installing all dependencies
RUN poetry install --no-dev
