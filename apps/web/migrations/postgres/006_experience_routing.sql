SET search_path TO observatory, public;
CREATE TABLE experience_studies (
 project_id text NOT NULL REFERENCES projects(id), experiment_id text NOT NULL,
 config_hash text NOT NULL CHECK(config_hash ~ '^[a-f0-9]{64}$'), config jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(project_id,experiment_id)
);
CREATE TABLE experience_records (
 project_id text NOT NULL, experiment_id text NOT NULL, kind text NOT NULL,
 id text NOT NULL, payload_hash text NOT NULL, payload jsonb NOT NULL,
 raw_archive_id text NOT NULL REFERENCES raw_archives(id), created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,experiment_id,kind,id), FOREIGN KEY(project_id,experiment_id) REFERENCES experience_studies
);
CREATE INDEX experience_records_scope_time ON experience_records(project_id,experiment_id,kind,created_at DESC,id);
CREATE TABLE experience_analysis_revisions (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, analysis_id text NOT NULL REFERENCES analyses(id),
 source_snapshot_hash text NOT NULL, extraction_configuration_hash text NOT NULL, source_versions jsonb NOT NULL,
 envelope jsonb NOT NULL, raw_archive_id text NOT NULL REFERENCES raw_archives(id), created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,experiment_id,id), FOREIGN KEY(project_id,experiment_id) REFERENCES experience_studies,
 UNIQUE(project_id,experiment_id,source_snapshot_hash,extraction_configuration_hash)
);
CREATE INDEX experience_revision_analysis ON experience_analysis_revisions(analysis_id);
CREATE TABLE work_item_extensions (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, revision_id text NOT NULL,
 parent_id text, source_task_id text NOT NULL REFERENCES tasks(id), payload jsonb NOT NULL,
 PRIMARY KEY(project_id,experiment_id,id),
 FOREIGN KEY(project_id,experiment_id,revision_id) REFERENCES experience_analysis_revisions,
 FOREIGN KEY(project_id,experiment_id,parent_id) REFERENCES work_item_extensions DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX work_items_revision ON work_item_extensions(project_id,experiment_id,revision_id);
CREATE INDEX work_items_parent ON work_item_extensions(project_id,experiment_id,parent_id);
CREATE INDEX work_items_task ON work_item_extensions(source_task_id);
CREATE TABLE event_support_links (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, revision_id text NOT NULL,
 target_id text NOT NULL, source_event_id text NOT NULL REFERENCES event_versions(id), payload jsonb NOT NULL,
 PRIMARY KEY(project_id,experiment_id,id), FOREIGN KEY(project_id,experiment_id,revision_id) REFERENCES experience_analysis_revisions,
 FOREIGN KEY(project_id,experiment_id,target_id) REFERENCES work_item_extensions
);
CREATE INDEX support_links_revision ON event_support_links(project_id,experiment_id,revision_id);
CREATE INDEX support_links_target ON event_support_links(project_id,experiment_id,target_id);
CREATE INDEX support_links_event ON event_support_links(source_event_id);
CREATE TABLE outcome_predictions (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, work_item_id text NOT NULL,
 revision_id text NOT NULL, label text NOT NULL CHECK(label IN ('successful','unsuccessful','abstain')), payload jsonb NOT NULL,
 PRIMARY KEY(project_id,experiment_id,id), FOREIGN KEY(project_id,experiment_id,revision_id) REFERENCES experience_analysis_revisions,
 FOREIGN KEY(project_id,experiment_id,work_item_id) REFERENCES work_item_extensions
);
CREATE INDEX predictions_revision ON outcome_predictions(project_id,experiment_id,revision_id);
CREATE INDEX predictions_work_item ON outcome_predictions(project_id,experiment_id,work_item_id);
CREATE TABLE experience_versions (
 project_id text NOT NULL, experiment_id text NOT NULL, version_id text NOT NULL, experience_id text NOT NULL, version integer NOT NULL CHECK(version>0),
 revision_id text NOT NULL, granularity text NOT NULL CHECK(granularity IN ('task','subtask')),
 admission text NOT NULL CHECK(admission IN ('candidate','publicly_supported','quarantined','superseded','retired')),
 first_available_sequence bigint NOT NULL CHECK(first_available_sequence>=0), source_visibility text NOT NULL CHECK(source_visibility='runtime_public'),
 payload jsonb NOT NULL, search_vector tsvector NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,experiment_id,version_id), UNIQUE(project_id,experiment_id,experience_id,version),
 FOREIGN KEY(project_id,experiment_id,revision_id) REFERENCES experience_analysis_revisions
);
CREATE INDEX experience_versions_eligibility ON experience_versions(project_id,experiment_id,admission,granularity,first_available_sequence,version_id);
CREATE INDEX experience_versions_revision ON experience_versions(project_id,experiment_id,revision_id);
CREATE INDEX experience_versions_fts ON experience_versions USING gin(search_vector);
CREATE TABLE experience_embeddings (
 project_id text NOT NULL, experiment_id text NOT NULL, version_id text NOT NULL, text_kind text NOT NULL CHECK(text_kind IN ('goal','procedure')),
 model_revision text NOT NULL, dimensions integer NOT NULL CHECK(dimensions>0 AND dimensions<=8192), normalization text NOT NULL,
 text_version text NOT NULL, vector_values double precision[] NOT NULL, payload_hash text NOT NULL,
 PRIMARY KEY(project_id,experiment_id,version_id,text_kind,model_revision,text_version),
 FOREIGN KEY(project_id,experiment_id,version_id) REFERENCES experience_versions,
 CHECK(array_length(vector_values,1)=dimensions)
);
CREATE INDEX embedding_model ON experience_embeddings(project_id,experiment_id,model_revision,dimensions);
CREATE TABLE experience_source_links (
 project_id text NOT NULL, experiment_id text NOT NULL, version_id text NOT NULL, work_item_id text NOT NULL,
 PRIMARY KEY(project_id,experiment_id,version_id,work_item_id),
 FOREIGN KEY(project_id,experiment_id,version_id) REFERENCES experience_versions,
 FOREIGN KEY(project_id,experiment_id,work_item_id) REFERENCES work_item_extensions
);
CREATE INDEX source_links_item ON experience_source_links(project_id,experiment_id,work_item_id);
CREATE TABLE memory_snapshots (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, arm text NOT NULL, watermark bigint NOT NULL CHECK(watermark>=0),
 manifest_hash text NOT NULL, payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(project_id,experiment_id,id), FOREIGN KEY(project_id,experiment_id) REFERENCES experience_studies
);
CREATE INDEX snapshots_scope_arm ON memory_snapshots(project_id,experiment_id,arm,watermark DESC);
CREATE TABLE memory_snapshot_members (
 project_id text NOT NULL, experiment_id text NOT NULL, snapshot_id text NOT NULL, version_id text NOT NULL,
 PRIMARY KEY(project_id,experiment_id,snapshot_id,version_id),
 FOREIGN KEY(project_id,experiment_id,snapshot_id) REFERENCES memory_snapshots,
 FOREIGN KEY(project_id,experiment_id,version_id) REFERENCES experience_versions
);
CREATE INDEX snapshot_members_version ON memory_snapshot_members(project_id,experiment_id,version_id);
CREATE TABLE experience_jobs (
 project_id text NOT NULL, experiment_id text NOT NULL, id text NOT NULL, analysis_id text REFERENCES analyses(id), base_job_id text REFERENCES analysis_jobs(id),
 operation text NOT NULL DEFAULT 'envelope-v3' CHECK(operation IN ('base-v2','envelope-v3')), model_invoked boolean NOT NULL DEFAULT false, measurement_origin text NOT NULL DEFAULT 'native' CHECK(measurement_origin IN ('native','fixture')),
 snapshot_hash text NOT NULL, configuration_hash text NOT NULL, source_binding jsonb NOT NULL, input jsonb NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','completed','failed','uncertain')),
 invocation_id text NOT NULL UNIQUE, result jsonb, usage jsonb, error text, artifacts jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz, finished_at timestamptz,
 PRIMARY KEY(project_id,experiment_id,id), FOREIGN KEY(project_id,experiment_id) REFERENCES experience_studies,
 UNIQUE(project_id,experiment_id,snapshot_hash,configuration_hash)
);
CREATE INDEX experience_jobs_analysis ON experience_jobs(analysis_id);
CREATE INDEX experience_jobs_queue ON experience_jobs(created_at,id) WHERE status='queued';
CREATE TABLE experience_analytics_outbox (
 id text PRIMARY KEY, project_id text NOT NULL, experiment_id text NOT NULL, kind text NOT NULL,
 payload jsonb NOT NULL, version bigint GENERATED ALWAYS AS IDENTITY, created_at timestamptz NOT NULL DEFAULT now(), delivered_at timestamptz,
 FOREIGN KEY(project_id,experiment_id) REFERENCES experience_studies
);
CREATE INDEX experience_analytics_pending ON experience_analytics_outbox(version) WHERE delivered_at IS NULL;
-- Structured receipts share an immutable, scoped journal. Dedicated views retain
-- typed names without duplicating records or native usage in analytical totals.
CREATE VIEW public_verification_records AS SELECT * FROM experience_records WHERE kind='verification';
CREATE VIEW plan_revisions AS SELECT * FROM experience_records WHERE kind='plan';
CREATE VIEW plan_nodes AS SELECT r.project_id,r.experiment_id,r.id AS revision_id,n.value AS payload FROM experience_records r CROSS JOIN LATERAL jsonb_array_elements(r.payload->'nodes') n WHERE r.kind='plan';
CREATE VIEW plan_dependencies AS SELECT n.project_id,n.experiment_id,n.revision_id,n.payload->>'nodeId' AS node_id,d.value AS dependency_id FROM plan_nodes n CROSS JOIN LATERAL jsonb_array_elements_text(n.payload->'dependsOn') d;
CREATE VIEW execution_attempts AS SELECT * FROM experience_records WHERE kind='attempt';
CREATE VIEW repository_checkpoints AS SELECT * FROM experience_records WHERE kind='checkpoint';
CREATE VIEW retrieval_decisions AS SELECT * FROM experience_records WHERE kind='retrieval';
CREATE VIEW routing_decisions AS SELECT * FROM experience_records WHERE kind='routing';
CREATE VIEW experience_reuse_outcomes AS SELECT * FROM experience_records WHERE kind='reuse';
CREATE FUNCTION experience_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Experience records are immutable; append a new version or linked receipt'; END $$;
CREATE TRIGGER immutable_study BEFORE UPDATE OR DELETE ON experience_studies FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON experience_records FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_revision BEFORE UPDATE OR DELETE ON experience_analysis_revisions FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_work_item BEFORE UPDATE OR DELETE ON work_item_extensions FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_support BEFORE UPDATE OR DELETE ON event_support_links FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_outcome BEFORE UPDATE OR DELETE ON outcome_predictions FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_experience BEFORE UPDATE OR DELETE ON experience_versions FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_embedding BEFORE UPDATE OR DELETE ON experience_embeddings FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_source_link BEFORE UPDATE OR DELETE ON experience_source_links FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_snapshot BEFORE UPDATE OR DELETE ON memory_snapshots FOR EACH ROW EXECUTE FUNCTION experience_immutable();
CREATE TRIGGER immutable_member BEFORE UPDATE OR DELETE ON memory_snapshot_members FOR EACH ROW EXECUTE FUNCTION experience_immutable();
