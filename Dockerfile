FROM ubuntu:latest
LABEL authors="aramarchuk"

ENTRYPOINT ["top", "-b"]