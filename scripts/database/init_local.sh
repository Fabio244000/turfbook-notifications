#!/bin/sh
# Local only: run by the Postgres container on its first start (empty volume).
set -eu

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -v service_db="$SERVICE_DB_NAME" \
  -v service_user="$SERVICE_DB_USER" \
  -v service_password="$SERVICE_DB_PASSWORD" \
  -f /sql/create_service_database.sql
