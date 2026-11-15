CREATE TABLE raw_archives (
 id text PRIMARY KEY, provider text NOT NULL, source_path text NOT NULL,
 content_sha256 text NOT NULL, bytes bigint NOT NULL,
 manifest_key text NOT NULL, chunks jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','retained')),
 created_at timestamptz NOT NULL DEFAULT now(), verified_at timestamptz
);
CREATE INDEX raw_archives_source ON raw_archives(source_path,created_at DESC);
CREATE INDEX raw_archives_pending ON raw_archives(created_at) WHERE status='pending';
ALTER TABLE source_files ADD COLUMN archive_id text REFERENCES raw_archives(id);
ALTER TABLE migration_manifests ADD COLUMN archive_id text REFERENCES raw_archives(id);
