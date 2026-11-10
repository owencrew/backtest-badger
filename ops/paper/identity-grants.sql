-- Separate administrator-reviewed PG17 addendum, inside the selected database.
-- Allows the restricted login to verify the server and schema before every cycle.
GRANT EXECUTE ON FUNCTION pg_catalog.pg_control_system() TO {worker};
GRANT SELECT (version_num) ON public.alembic_version TO {worker};
