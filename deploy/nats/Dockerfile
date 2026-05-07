FROM nats:2.10-alpine

# JetStream storage directory
RUN mkdir -p /data

EXPOSE 4222 8222 6222

CMD ["nats-server", "-js", "-p", "4222", "-m", "8222", "--store_dir", "/data", "--max_payload", "8MB"]
