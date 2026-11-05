#!/usr/bin/env python3
"""Prepare pinned local Langfuse configuration; never pull or execute images."""
import argparse
import json
import os
from pathlib import Path
import secrets


def prepare(destination):
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination, 0o700)
    access = destination / 'local-access.json'
    if access.exists():
        credentials = json.loads(access.read_text())
    else:
        credentials = {key: secrets.token_hex(24) for key in
                       ('postgres_password', 'redis_password', 'clickhouse_password', 's3_secret', 'salt', 'nextauth_secret', 'password')}
        credentials.update(encryption_key=secrets.token_hex(32), s3_user='ttgl',
                           public_key='pk-lf-' + secrets.token_hex(16), secret_key='sk-lf-' + secrets.token_hex(24),
                           base_url='http://localhost:3000', project_id='ttgl-codex', email='local@ttgl.test')
        write_private(access, credentials)
    c = credentials
    codespace = os.environ.get('CODESPACE_NAME')
    domain = os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
    public_url = f'https://{codespace}-3000.{domain}' if codespace else c['base_url']
    media_url = f'https://{codespace}-9090.{domain}' if codespace else 'http://localhost:9090'
    candidates = json.loads((Path(__file__).resolve().parents[1] / 'observability/candidate-images.json').read_text())
    images = {name: candidates[name]['image'] for name in ('langfuse-web', 'langfuse-worker', 'postgres', 'redis', 'clickhouse')}
    images['minio'] = 'cgr.dev/chainguard/minio@sha256:cee9a8e35885e93f14b3cb32960e5017aff74e2adfb52ba87c65003b0163886b'
    common = dict(
        NEXTAUTH_URL=public_url, DATABASE_URL=f"postgresql://postgres:{c['postgres_password']}@postgres:5432/postgres",
        SALT=c['salt'], ENCRYPTION_KEY=c['encryption_key'], TELEMETRY_ENABLED='false',
        LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES='false', LANGFUSE_IN_APP_AGENT_ENABLED='false',
        CLICKHOUSE_MIGRATION_URL='clickhouse://clickhouse:9000', CLICKHOUSE_URL='http://clickhouse:8123',
        CLICKHOUSE_USER='clickhouse', CLICKHOUSE_PASSWORD=c['clickhouse_password'], CLICKHOUSE_CLUSTER_ENABLED='false',
        REDIS_HOST='redis', REDIS_PORT='6379', REDIS_AUTH=c['redis_password'], REDIS_TLS_ENABLED='false',
        LANGFUSE_S3_BATCH_EXPORT_ENABLED='false')
    for kind, prefix in [('EVENT', 'events/'), ('MEDIA', 'media/')]:
        for key, value in dict(BUCKET='langfuse', REGION='auto', ACCESS_KEY_ID=c['s3_user'],
                               SECRET_ACCESS_KEY=c['s3_secret'], ENDPOINT='http://minio:9000',
                               FORCE_PATH_STYLE='true', PREFIX=prefix).items():
            common[f'LANGFUSE_S3_{kind}_UPLOAD_{key}'] = value
    def service(name, memory, cpus):
        return dict(image=images[name], pull_policy='never', restart='unless-stopped',
                    mem_limit=memory, cpus=cpus, security_opt=['no-new-privileges:true'],
                    logging=dict(driver='json-file', options={'max-size': '10m', 'max-file': '3'}))
    def health(command):
        return dict(test=command, interval='5s', timeout='5s', retries=30, start_period='20s')
    services = {}
    services['postgres'] = dict(service('postgres', '512m', 1),
        environment=dict(POSTGRES_USER='postgres', POSTGRES_DB='postgres', POSTGRES_PASSWORD=c['postgres_password']),
        volumes=['postgres_data:/var/lib/postgresql/data'], healthcheck=health(['CMD', 'pg_isready', '-U', 'postgres']))
    services['redis'] = dict(service('redis', '256m', .5),
        environment=dict(REDISCLI_AUTH=c['redis_password']),
        command=['redis-server', '--requirepass', c['redis_password'], '--maxmemory-policy', 'noeviction', '--appendonly', 'yes'],
        volumes=['redis_data:/data'], healthcheck=health(['CMD', 'redis-cli', 'ping']))
    services['clickhouse'] = dict(service('clickhouse', '1536m', 1), user='101:101',
        environment=dict(CLICKHOUSE_DB='default', CLICKHOUSE_USER='clickhouse', CLICKHOUSE_PASSWORD=c['clickhouse_password']),
        volumes=['clickhouse_data:/var/lib/clickhouse', 'clickhouse_logs:/var/log/clickhouse-server'],
        healthcheck=health(['CMD', 'wget', '--no-verbose', '--tries=1', '--spider', 'http://127.0.0.1:8123/ping']))
    services['minio'] = dict(service('minio', '384m', .5), entrypoint='sh',
        command=['-c', 'mkdir -p /data/langfuse && exec minio server --address :9000 --console-address :9001 /data'],
        environment=dict(MINIO_ROOT_USER=c['s3_user'], MINIO_ROOT_PASSWORD=c['s3_secret']),
        ports=['127.0.0.1:9090:9000', '127.0.0.1:9091:9001'], volumes=['minio_data:/data'],
        healthcheck=health(['CMD', 'mc', 'ready', 'local']))
    dependencies = {name: {'condition': 'service_healthy'} for name in services}
    services['langfuse-worker'] = dict(service('langfuse-worker', '1g', 1), environment=common, depends_on=dependencies)
    web_env = dict(common, NEXTAUTH_SECRET=c['nextauth_secret'],
        LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT=media_url, LANGFUSE_S3_MEDIA_UPLOAD_INTERNAL_ENDPOINT='http://minio:9000',
        LANGFUSE_INIT_ORG_ID='ttgl', LANGFUSE_INIT_ORG_NAME='TTGL', LANGFUSE_INIT_PROJECT_ID=c['project_id'],
        LANGFUSE_INIT_PROJECT_NAME='Codex Observatory', LANGFUSE_INIT_PROJECT_PUBLIC_KEY=c['public_key'],
        LANGFUSE_INIT_PROJECT_SECRET_KEY=c['secret_key'], LANGFUSE_INIT_USER_EMAIL=c['email'],
        LANGFUSE_INIT_USER_NAME='Local analyst', LANGFUSE_INIT_USER_PASSWORD=c['password'])
    services['langfuse-web'] = dict(service('langfuse-web', '1536m', 1), environment=web_env,
        ports=['127.0.0.1:3000:3000'], depends_on=dependencies)
    compose = dict(name='ttgl-langfuse', services=services,
                   volumes={name: {} for name in ('postgres_data', 'redis_data', 'clickhouse_data', 'clickhouse_logs', 'minio_data')})
    write_private(destination / 'compose.json', compose)
    # Non-secret inventory is suitable for security review; configuration stays private.
    previous_review = json.loads((destination / 'review.json').read_text()) if (destination / 'review.json').exists() else {}
    write_private(destination / 'review.json', dict(status=previous_review.get('status', 'pending_security_review'),
        services=images, ports=['127.0.0.1:3000', '127.0.0.1:9090', '127.0.0.1:9091'],
        installed=previous_review.get('installed', False), started=previous_review.get('started', False),
        authorization=previous_review.get('authorization'), upstream='https://github.com/langfuse/langfuse/blob/v4.75.0/docker-compose.yml',
        outstanding=['Full Node and base OS inventory/advisories', 'Worker and infrastructure dependency review',
                     'Publisher provenance and automatic execution review', 'MinIO candidate dependency review']))
    print(f'Prepared six services in {destination}. This command did not pull or start images. Credentials are in local-access.json (private).')


def write_private(path, value):
    fd = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    prepare(parser.parse_args().destination)
