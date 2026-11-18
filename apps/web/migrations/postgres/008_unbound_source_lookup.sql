SET search_path TO observatory, public;
CREATE INDEX turns_unbound_source_path ON turns((source->>'path')) WHERE NOT (source ? 'analysis_binding');
