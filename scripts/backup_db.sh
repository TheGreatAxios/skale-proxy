#!/bin/bash
set -e

[ $# -eq 0 ] && { echo "Usage: $0 <backup_directory>"; exit 1; }

BACKUP_DIR="$1"
CONTAINER_NAME="db"
DB_NAME="metrics"


mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

docker exec $CONTAINER_NAME /usr/bin/mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" "$DB_NAME" > "$BACKUP_FILE"

gzip "$BACKUP_FILE"

echo "Backup completed: ${BACKUP_FILE}.gz"