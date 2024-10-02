FROM ubuntu:latest

LABEL maintainer="fauzi.mkom@gmail.com"
RUN apt update
RUN apt install python3 python3-pip libffi-dev libssl-dev curl speedtest-cli wget -y
ENV API_KEY ""

COPY requirements.txt /tmp


RUN  pip3 install --upgrade pip --no-cache-dir && \
     pip3 install --upgrade setuptools --no-cache-dir
     
RUN pip3 install -r /tmp/requirements.txt

RUN wget https://raw.githubusercontent.com/sivel/speedtest-cli/v2.1.3/speedtest.py -O /usr/lib/python3/dist-packages/speedtest.py

RUN mkdir /opt/rin

COPY rin.py /opt/rin



ENTRYPOINT ["/usr/bin/python3", "/opt/rin/rin.py"]
