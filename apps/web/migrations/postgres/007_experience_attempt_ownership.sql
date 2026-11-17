-- Enforce retained ownership even when two authorized clients race.
CREATE UNIQUE INDEX experience_attempt_ordinal ON experience_records
(project_id,experiment_id,(payload->>'taskInstanceId'),(payload->>'arm'),(payload->>'planNodeId'),(payload->>'ordinal')) WHERE kind='attempt';
CREATE UNIQUE INDEX experience_terminal_attempt ON experience_records
(project_id,experiment_id,(payload->>'attemptId')) WHERE kind='attempt-event';
CREATE UNIQUE INDEX experience_publication_sequence ON experience_records
(project_id,experiment_id,(payload->>'arm'),(payload->>'sequence')) WHERE kind='barrier';
CREATE FUNCTION experience_assignment_barrier() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.kind IN ('attempt','barrier') THEN
  PERFORM pg_advisory_xact_lock(hashtext(NEW.project_id || '/' || NEW.experiment_id || '/' || (NEW.payload->>'taskInstanceId') || '/' || (NEW.payload->>'arm')));
 END IF;
 IF NEW.kind='attempt' AND EXISTS(SELECT 1 FROM experience_records r WHERE r.project_id=NEW.project_id AND r.experiment_id=NEW.experiment_id AND r.kind='barrier' AND r.payload->>'taskInstanceId'=NEW.payload->>'taskInstanceId' AND r.payload->>'arm'=NEW.payload->>'arm') THEN
  RAISE EXCEPTION 'Assignment already has a publication barrier';
 END IF;
 IF NEW.kind='barrier' AND EXISTS(SELECT 1 FROM experience_records a WHERE a.project_id=NEW.project_id AND a.experiment_id=NEW.experiment_id AND a.kind='attempt' AND a.payload->>'taskInstanceId'=NEW.payload->>'taskInstanceId' AND a.payload->>'arm'=NEW.payload->>'arm' AND (NOT (NEW.payload->'attemptIds' ? a.id) OR NOT EXISTS(SELECT 1 FROM experience_records e WHERE e.project_id=a.project_id AND e.experiment_id=a.experiment_id AND e.kind='attempt-event' AND e.payload->>'attemptId'=a.id AND e.payload->>'status' IN ('accepted','public_failure')))) THEN
  RAISE EXCEPTION 'Publication barrier requires all terminal public attempts';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER experience_assignment_boundary BEFORE INSERT ON experience_records FOR EACH ROW EXECUTE FUNCTION experience_assignment_barrier();
