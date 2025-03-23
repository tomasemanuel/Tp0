FROM ubuntu:latest

RUN apt-get update && apt-get install -y netcat-openbsd

CMD ["/bin/sh", "-c", "echo \"hello world\" | nc -w 5 server 12345"]