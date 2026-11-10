-- Future maintenance only, after verifying an existing admin-owned 0001.
-- Execute as administrator. The new ordinary migration owner creates 0002
-- without taking ownership of the database, market, candles or revision log.
GRANT CONNECT ON DATABASE {database} TO {owner}, {collector};
GRANT USAGE ON SCHEMA public TO {collector};
GRANT USAGE, CREATE ON SCHEMA public TO {owner};
GRANT SELECT, REFERENCES, TRIGGER ON public.market TO {owner};
-- PostgreSQL requires UPDATE on at least one column for the guard's FOR SHARE.
GRANT UPDATE (market_id) ON public.market TO {owner};
GRANT SELECT, UPDATE (version_num) ON public.alembic_version TO {owner};
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION pg_catalog.lo_create(oid), pg_catalog.lo_creat(integer),
    pg_catalog.lo_from_bytea(oid, bytea) FROM PUBLIC;
