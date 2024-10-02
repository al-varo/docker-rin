FROM python:3.9.16-slim-buster

LABEL maintainer="fauzi.mkom@gmail.com"
RUN apt install libffi-dev libssl-dev curl speedtest-cli wget -y
RUN wget https://raw.githubusercontent.com/sivel/speedtest-cli/v2.1.3/speedtest.py -O /usr/lib/python3/dist-packages/speedtest.py
ENV API_KEY ""
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
RUN mkdir /opt/rin
COPY rin.py /opt/rin
CMD python /opt/rin/rin.py
