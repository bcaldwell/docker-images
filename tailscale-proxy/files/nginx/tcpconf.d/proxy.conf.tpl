stream {
    upstream web_server_ssl {
        # Our web server, listening for SSL traffic
        server {{env.Getenv "UPSTREAM_IP"}}:443;
    }

    upstream web_server {
        # Our web server, listening for SSL traffic
        server {{env.Getenv "UPSTREAM_IP"}}:80;
    }

    server {
        listen 443;
        proxy_pass web_server_ssl;
    }

    server {
        listen 80;
        proxy_pass web_server;
    }
}
