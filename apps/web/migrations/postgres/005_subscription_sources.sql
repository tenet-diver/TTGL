SET search_path TO observatory, public;
ALTER TABLE source_files ADD COLUMN analysis_binding jsonb;
