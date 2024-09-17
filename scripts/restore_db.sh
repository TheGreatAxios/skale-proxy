#!/bin/bash

set -e

[ $# -eq 0 ] && { echo "Usage: $0 <backup_file>"; exit 1; }

BACKUP_FILE=$1
CONTAINER_NAME="db"
DB_NAME="metrics"

[ ! -f "$BACKUP_FILE" ] && { echo "Backup file not found: $BACKUP_FILE"; exit 1; }

if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME /usr/bin/mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "$DB_NAME"
else
    docker exec -i $CONTAINER_NAME /usr/bin/mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "$DB_NAME" < "$BACKUP_FILE"
fi

echo "Database restored successfully from $BACKUP_FILE"