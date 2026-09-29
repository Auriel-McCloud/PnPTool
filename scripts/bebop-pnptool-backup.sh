#!/bin/bash
# Nächtliches PnPTool-Backup auf bebop.
# Täglich 30 Tage behalten; der Stand vom 1. jedes Monats ein Jahr.
# Stoppt Neo4j nur kurz (konsistenter Dump), Backend bleibt stehen.
set -euo pipefail

COMPOSE_DIR=/opt/pnptool
ENV_FILE="$COMPOSE_DIR/.env"
BACKUP_ROOT=/var/backups/pnptool
DAILY="$BACKUP_ROOT/daily"
MONTHLY="$BACKUP_ROOT/monthly"
LOG=/var/log/pnptool-backup.log
VOL_DATA=pnptool_pnptool_neo4j_data
VOL_UPLOADS=pnptool_pnptool_uploads
STAMP=$(date +%F)
DAY=$(date +%d)
MONTH=$(date +%Y-%m)

mkdir -p "$DAILY" "$MONTHLY"
TMP=$(mktemp -d)
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Passwort nur für den Health-Check nach dem Start, nie loggen.
NEO4J_PASSWORD=$(grep '^NEO4J_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)
NEO4J_USER=$(grep '^NEO4J_USER=' "$ENV_FILE" | cut -d= -f2-)
NEO4J_USER=${NEO4J_USER:-neo4j}

cd "$COMPOSE_DIR"
docker compose stop neo4j

docker run --rm \
  -v "${VOL_DATA}:/data:ro" \
  -v "${VOL_UPLOADS}:/uploads:ro" \
  -v "${TMP}:/backup" \
  alpine:3.20 \
  tar czf /backup/bundle.tar.gz -C / data uploads

docker compose start neo4j

ok=0
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 15; do
  if docker exec pnptool-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
      'MATCH (g:GMUser) RETURN count(g) AS n' 2>/dev/null | grep -q '[1-9]'; then
    ok=1
    break
  fi
  sleep 2
done
if [ "$ok" -ne 1 ]; then
  echo "FEHLER: Neo4j nach Dump nicht gesund (kein GMUser). Backup-Datei nicht übernommen." >&2
  exit 1
fi

if [ ! -s "$TMP/bundle.tar.gz" ]; then
  echo "FEHLER: Dump-Datei leer." >&2
  exit 1
fi

cp "$TMP/bundle.tar.gz" "$DAILY/${STAMP}.tar.gz"
if [ "$DAY" = "01" ]; then
  cp "$DAILY/${STAMP}.tar.gz" "$MONTHLY/${MONTH}.tar.gz"
fi

# Nur eigene Backup-Dateien, nie etwas außerhalb.
find "$DAILY" -maxdepth 1 -type f -name '*.tar.gz' -mtime +30 -delete
find "$MONTHLY" -maxdepth 1 -type f -name '*.tar.gz' -mtime +370 -delete

echo "$(date -Iseconds) ok daily=${STAMP} size=$(stat -c%s "$DAILY/${STAMP}.tar.gz")"
