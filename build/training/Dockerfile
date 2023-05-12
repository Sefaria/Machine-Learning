FROM python:3.9

WORKDIR /app/
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
WORKDIR prodigy_scripts/prodigy_utils/
RUN python setup.py develop
WORKDIR /app/

ENTRYPOINT [ "python", "util/job.py" ]