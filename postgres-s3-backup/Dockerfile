FROM postgres:14.0-alpine as postgres

RUN apk add gnupg aws-cli bzip2

COPY files/postgres_s3_backup.sh postgres_s3_backup.sh

CMD ["sh", "postgres_s3_backup.sh"]
