# 1. This tells docker to use the Rust official image
FROM rust:1.84.0-alpine3.21 as builder

WORKDIR /kube-postgress-bootstrap
RUN apk add build-base

# 2. Copy the files in your machine to the Docker image
COPY ./files ./

# Build your program for release
RUN cargo build --release

FROM alpine:3.21
COPY --from=builder /kube-postgress-bootstrap/target/release/kube-postgress-bootstrap /kube-postgress-bootstrap
CMD ["/kube-postgress-bootstrap"]

