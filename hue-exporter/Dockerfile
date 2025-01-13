FROM golang:1.23-alpine3.21 AS builder

ARG VERSION=b3fb13b5f9397c3500ce9df8889207561e52126f

RUN go install github.com/aexel90/hue_exporter@${VERSION}

FROM alpine:3.21
RUN apk update && apk add ca-certificates tzdata && rm -rf /var/cache/apk/*
WORKDIR /hue_exporter
COPY --from=builder /go/bin/hue_exporter ./
ENTRYPOINT ["./hue_exporter"]
