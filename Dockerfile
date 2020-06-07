FROM python:3.7-alpine
RUN apk --update add git && \
    pip install -U pip && \
    pip install dep-license

CMD ["deplic"]
