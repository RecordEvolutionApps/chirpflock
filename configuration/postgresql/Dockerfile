# Stay on major 14: existing deployments have PG14 data in the postgresqldata
# volume, and a major bump refuses to start on the old data dir (needs pg_upgrade).
FROM postgres:14.23-alpine

COPY ./initdb /docker-entrypoint-initdb.d/
