#!/bin/sh
echo "Waiting for postgres..."
until pg_isready -h db -p 5432; do
  sleep 1
done
echo "Postgres is up!"
exec "$@"