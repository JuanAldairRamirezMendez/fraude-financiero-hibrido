#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"

pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" "$BACKUP_FILE"
printf 'Restored %s\n' "$BACKUP_FILE"