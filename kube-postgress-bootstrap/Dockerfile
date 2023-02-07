# 1. This tells docker to use the Rust official image
FROM rust:1.67-alpine3.17 as rbuilder

WORKDIR /kube-postgress-bootstrap
RUN apk add build-base

# 2. Copy the files in your machine to the Docker image
COPY ./files ./

# Build your program for release
RUN cargo build --release

FROM alpine:3.17
COPY --from=rbuilder /kube-postgress-bootstrap/target/release/kube-postgress-bootstrap /kube-postgress-bootstrap
CMD ["/kube-postgress-bootstraps"]
