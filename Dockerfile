FROM python:3.9

WORKDIR /app/
ENV PYTHONPATH="/app/"
ENV MONGO_HOST="mongodb://127.0.0.1"
ENV MONGO_PORT="27017"
ENV MONGO_USER=""
ENV MONGO_PASSWORD=""
ENV REPLICASET_NAME=""
ENV GPU_ID=-1
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
WORKDIR prodigy_scripts/prodigy_utils/
RUN python setup.py develop
WORKDIR /app/

ENTRYPOINT [ "python", "util/job.py" ]