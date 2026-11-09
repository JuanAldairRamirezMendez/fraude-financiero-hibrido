#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

pg_dump --format=custom --file="$BACKUP_DIR/fraud_detection-$STAMP.dump" "$DATABASE_URL"
printf 'Backup written to %s\n' "$BACKUP_DIR/fraud_detection-$STAMP.dump"