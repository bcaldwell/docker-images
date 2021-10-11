#!/bin/bash
set -e

DUMP_FILE=${DUMP_FILE:-/backup_`date +%Y%m%d_%H%M%S`.pgdump}

PGPASSWORD=$POSTGRES_PASSWORD pg_dump -d $POSTGRES_DB -U $POSTGRES_USER -h $POSTGRES_HOST -f $DUMP_FILE

bzip2 -z ${DUMP_FILE}

echo $GPG_PUBLIC_KEY | base64 -d | gpg --import
echo $GPG_OWNER_TRUST | base64 -d | gpg --import-ownertrust
gpg --output ${DUMP_FILE}.bz2.gpg -e -r ${GPG_RECIPIENT} ${DUMP_FILE}.bz2

AWS_ARGS=""
if [[ ! -z "${S3_ENDPOINT_URL}" ]]; then
  AWS_ARGS="--endpoint-url=${S3_ENDPOINT_URL}"
fi

aws s3 cp ${AWS_ARGS} ${DUMP_FILE}.bz2.gpg $S3_BACKUP_PATH

# gpg --output selfops-dump-civo-nyc-1.pgdump.bz2 --decrypt selfops-dump-civo-nyc-1.pgdump.bz2.gpg
# bzip2 -d selfops-dump-civo-nyc-1.pgdump.bz2
