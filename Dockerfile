FROM python:3.9

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN python prodigy/prodigy_utils/setup.py develop

ENTRYPOINT bash
