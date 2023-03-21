# Local Build Instructions:
# 1. From the repository root run the following
# $ docker build -f ./build/prodigy/Dockerfile .

FROM gcr.io/production-deployment/base-web:latest

ENV PRODIGY_HOME=/home/prodigy
WORKDIR /home/prodigy

# Expects the Prodigy python wheel to exist at ./researchprodigy/*
COPY ./prodigy_scripts/* ./
RUN mkdir ./prodigy_utils
COPY ./prodigy_scripts/prodigy_utils/* ./prodigy_utils/
RUN mkdir ./util
COPY ./util/* ./util/
RUN pip3 install ./prodigy*.whl

COPY build/prodigy/requirements.txt ./
RUN pip3 install -r ./requirements.txt

RUN python -m nltk.downloader punkt

RUN cd ./prodigy_utils && python setup.py develop

ENTRYPOINT [ "/bin/bash", "-c" ]
EXPOSE 8080