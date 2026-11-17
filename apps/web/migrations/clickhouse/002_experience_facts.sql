CREATE TABLE IF NOT EXISTS observatory.experience_facts (
 id String, project_id String, experiment_id String, kind LowCardinality(String),
 payload String, recorded_at DateTime64(3,'UTC'), version UInt64
) ENGINE=ReplacingMergeTree(version) ORDER BY (project_id,experiment_id,kind,id);
