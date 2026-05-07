FROM temporalio/auto-setup:1.24

# Uses SQLite by default for Railway single-container deploy.
# For production scale, set TEMPORAL_DB=postgresql and wire a Postgres addon.
ENV TEMPORAL_DB=sqlite
ENV SQLITE_FILENAME=/data/temporal.db
ENV TEMPORAL_LOG_LEVEL=info

RUN mkdir -p /data

EXPOSE 7233 7234 7235 8080

CMD ["autosetup"]
