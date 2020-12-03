FROM postgres:11.8-alpine as postgres

RUN apk add gnupg aws-cli bzip2

COPY postgres_s3_backup.sh postgres_s3_backup.sh

CMD ["sh", "postgres_s3_backup.sh"]
