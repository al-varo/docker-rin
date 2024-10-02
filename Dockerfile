FROM python:3.5.8-slim-buster
LABEL maintainer="fauzi.mkom@gmail.com"
RUN apt update -y && \
    apt install -y libffi-dev && \
    apt install -y libssl-dev && \
    apt install -y curl && \
    apt install -y speedtest-cli && \
    apt install -y wget
RUN wget https://raw.githubusercontent.com/sivel/speedtest-cli/v2.1.3/speedtest.py -O /usr/local/lib/python3.9/speedtest.py    
ENV API_KEY ""
COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
RUN mkdir /opt/rin
COPY rin.py /opt/rin
CMD python /opt/rin/rin.py
