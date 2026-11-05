#!/usr/bin/env python3
"""Prepare pinned local Langfuse configuration; never pull or execute images."""
import argparse
import json
import os
import re
from pathlib import Path
import secrets


def prepare(destination, public_url=None, media_url=None):
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
    public_url = public_url or (f'https://{codespace}-3000.{domain}' if codespace else c['base_url'])
    media_url = media_url or (f'https://{codespace}-9090.{domain}' if codespace else 'http://localhost:9090')
    config = Path(__file__).resolve().parents[1] / 'config'
    lock = json.loads((config / 'deployment.lock.json').read_text())
    images = {name: item['image'] for name, item in lock['images'].items()}
    if any('@sha256:' not in image for image in images.values()):
        raise ValueError('Every active image must be digest-pinned')
    variables = {
        'PUBLIC_URL': public_url, 'MEDIA_URL': media_url,
        'POSTGRES_PASSWORD': c['postgres_password'], 'REDIS_PASSWORD': c['redis_password'],
        'CLICKHOUSE_PASSWORD': c['clickhouse_password'], 'S3_SECRET': c['s3_secret'],
        'SALT': c['salt'], 'NEXTAUTH_SECRET': c['nextauth_secret'], 'ADMIN_PASSWORD': c['password'],
        'ENCRYPTION_KEY': c['encryption_key'], 'LANGFUSE_PUBLIC_KEY': c['public_key'],
        'LANGFUSE_SECRET_KEY': c['secret_key'], 'S3_USER': c['s3_user'],
        'PROJECT_ID': c['project_id'], 'ADMIN_EMAIL': c['email'],
    }
    variables.update({'IMAGE_' + name.upper().replace('-', '_'): image for name, image in images.items()})
    compose = render(json.loads((config / 'compose.template.json').read_text()), variables)
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


def render(value, variables):
    if isinstance(value, dict):
        return {key: render(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [render(item, variables) for item in value]
    if isinstance(value, str):
        return re.sub(r'\$\{([A-Z][A-Z0-9_]*)\}', lambda match: str(variables[match[1]]), value)
    return value


def write_private(path, value):
    fd = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--public-url')
    parser.add_argument('--media-url')
    args = parser.parse_args()
    prepare(args.destination, args.public_url, args.media_url)
