ALTER TABLE observatory.event_versions ADD COLUMN IF NOT EXISTS routing_key text NOT NULL DEFAULT '';
ALTER TABLE observatory.steering_log ADD COLUMN IF NOT EXISTS task_id text;
CREATE INDEX IF NOT EXISTS steering_log_task ON observatory.steering_log(task_id,at) WHERE task_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS observatory.mutation_receipts (id text PRIMARY KEY, request_hash text NOT NULL, response jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
