FROM alpine:3.19.0

RUN apk update && \
    apk add python3 \
        py3-pip

COPY requirements.txt .

RUN pip --no-cache-dir install --break-system-packages \
    -r requirements.txt

RUN mkdir /app
WORKDIR /app