-- PG17, revision 0002. Identifiers are composed by the isolated provisioner.
-- Run transactionally as the ordinary owner on a fresh database or the
-- reviewed bootstrap administrator on a split-owner legacy database.
REVOKE ALL ON DATABASE {database} FROM PUBLIC;
GRANT CONNECT ON DATABASE {database} TO {worker}, {operator}, {reader};
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO {worker}, {operator}, {reader};
ALTER DEFAULT PRIVILEGES FOR ROLE {owner} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;
GRANT SELECT ON market, paper_portfolio, paper_order, paper_decision,
    paper_market_event, paper_ledger_entry TO {worker}, {operator}, {reader};

-- The pinned guard needs FOR SHARE on market. Only the installed trigger
-- can invoke it. No runtime role can attach a trigger, execute this routine,
-- write market, create a temp namespace or replace any referenced object.
ALTER FUNCTION paper_guard_portfolio() SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION paper_lock(uuid), paper_latest(uuid),
    paper_pending(uuid), paper_config_text(jsonb) TO {worker}, {operator};
GRANT EXECUTE ON FUNCTION paper_fee(numeric) TO {worker};

GRANT INSERT ON paper_portfolio TO {operator};
GRANT INSERT ON paper_decision, paper_order TO {worker};
GRANT INSERT ON paper_market_event, paper_ledger_entry TO {operator}, {worker};
GRANT UPDATE (ledger_highwater,state,activated_at,state_event_id)
    ON paper_portfolio TO {operator}, {worker};
GRANT UPDATE (status) ON paper_order TO {worker};

ALTER TABLE paper_ledger_entry ENABLE ROW LEVEL SECURITY;
CREATE POLICY ledger_read ON paper_ledger_entry FOR SELECT USING (true);
CREATE POLICY funding ON paper_ledger_entry FOR INSERT TO {operator}
    WITH CHECK (entry_type = 'INITIAL_FUNDING');
CREATE POLICY postings ON paper_ledger_entry FOR INSERT TO {worker}
    WITH CHECK (entry_type = 'FILL');

ALTER TABLE paper_market_event ENABLE ROW LEVEL SECURITY;
CREATE POLICY event_read ON paper_market_event FOR SELECT USING (true);
CREATE POLICY inception ON paper_market_event FOR INSERT TO {operator}
    WITH CHECK (event_type = 'MARK_OBSERVED' AND reason_code = 'INCEPTION');
CREATE POLICY operational ON paper_market_event FOR INSERT TO {worker}
    WITH CHECK (reason_code IS DISTINCT FROM 'INCEPTION' AND event_type IN
        ('MARK_OBSERVED','MARK_MISSING','QUOTE_OBSERVED','QUOTE_FAILED','FILL',
         'ORDER_REJECTED','ORDER_EXPIRED','EXIT_SATISFIED','EXIT_BLOCKED_DUST'));
