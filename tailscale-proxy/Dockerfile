FROM alpine:latest as tailscale
WORKDIR /app
COPY . ./
ENV TSFILE=tailscale_1.16.2_amd64.tgz
RUN wget https://pkgs.tailscale.com/stable/${TSFILE} && tar xzf ${TSFILE} --strip-components=1
COPY . ./


FROM nginx:1.21-alpine
RUN apk update && apk add ca-certificates iptables ip6tables && rm -rf /var/cache/apk/*
COPY --from=hairyhenderson/gomplate:slim /gomplate /bin/gomplate

COPY --from=tailscale /app/tailscaled /bin/tailscaled
COPY --from=tailscale /app/tailscale /bin/tailscale
RUN mkdir -p /var/run/tailscale /var/cache/tailscale /var/lib/tailscale

COPY files/nginx/ /etc/nginx/templates/
COPY files/startup-scripts/ /docker-entrypoint.d/

RUN chmod +x /docker-entrypoint.d/*
