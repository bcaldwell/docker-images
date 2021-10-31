#!/bin/sh

tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock &
until tailscale up --authkey=${TAILSCALE_AUTHKEY} --hostname=tailscale-proxy --accept-routes
do
    sleep 0.1
done
