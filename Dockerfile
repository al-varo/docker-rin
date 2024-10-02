FROM python:3.9.16-slim-buster

LABEL maintainer="fauzi.mkom@gmail.com"
ENV API_KEY ""
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
RUN mkdir /opt/rin
COPY rin.py /opt/rin
CMD python /opt/rin/rin.py
