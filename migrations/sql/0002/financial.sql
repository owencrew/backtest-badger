-- Insert guards pin quote, order, eligible size and policy under the portfolio lock.
-- Deferred checks close the reverse links only once the entire transaction is visible.
CREATE FUNCTION paper_check_commit() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE hi bigint; actual bigint; oid uuid; status_now text; evidence text; cash numeric; base numeric; o paper_order; cash_delta numeric; base_delta numeric;
BEGIN
    IF TG_TABLE_NAME IN ('paper_portfolio','paper_ledger_entry') THEN
        SELECT ledger_highwater INTO hi FROM paper_portfolio WHERE portfolio_id=NEW.portfolio_id;
        SELECT coalesce(max(ledger_seq),0) INTO actual FROM paper_ledger_entry WHERE portfolio_id=NEW.portfolio_id;
        IF hi<>actual THEN RAISE EXCEPTION 'Ledger high-water mismatch' USING ERRCODE='23000'; END IF;
    ELSIF TG_TABLE_NAME='paper_order' THEN
        oid := NEW.order_id;
    ELSIF TG_TABLE_NAME='paper_market_event' THEN
        IF NEW.event_type IN ('ORDER_REJECTED','ORDER_EXPIRED','FILL') THEN oid := NEW.order_id; END IF;
        IF NEW.event_type='FILL' THEN
            SELECT * INTO STRICT o FROM paper_order WHERE order_id=oid;
            SELECT coalesce(sum(delta_units) FILTER (WHERE asset='USDT'),0),
                coalesce(sum(delta_units) FILTER (WHERE asset<>'USDT'),0)
                INTO cash,base FROM paper_ledger_entry WHERE portfolio_id=NEW.portfolio_id
                AND ledger_seq<=NEW.ledger_seq_before;
            IF (cash,base) IS DISTINCT FROM (o.budget_cash_snapshot,o.base_qty_snapshot)
                OR (o.side='SELL' AND (base<>NEW.simulated_qty OR cash+NEW.gross_notional-NEW.fee_usdt<0))
                OR (o.side='BUY' AND (base<>0 OR cash-NEW.gross_notional-NEW.fee_usdt<0)) THEN
                RAISE EXCEPTION 'Fill violates authoritative prefix balances' USING ERRCODE='23000';
            END IF;
            cash_delta := CASE WHEN o.side='BUY' THEN -NEW.gross_notional ELSE NEW.gross_notional END-NEW.fee_usdt;
            base_delta := CASE WHEN o.side='BUY' THEN NEW.simulated_qty ELSE -NEW.simulated_qty END;
            IF NOT EXISTS (
                SELECT FROM paper_ledger_entry c JOIN paper_ledger_entry b
                    ON b.fill_event_id=c.fill_event_id JOIN paper_portfolio p ON p.portfolio_id=c.portfolio_id
                WHERE c.fill_event_id=NEW.event_id AND c.asset='USDT' AND b.asset=p.base_asset
                    AND c.ledger_seq=NEW.ledger_seq_before+1 AND b.ledger_seq=NEW.ledger_seq_after
                    AND c.delta_units=cash_delta AND b.delta_units=base_delta
                    AND c.posted_at=NEW.recorded_at AND b.posted_at=NEW.recorded_at
            ) THEN
                RAISE EXCEPTION 'Fill requires its exact pair of postings' USING ERRCODE='23000';
            END IF;
            IF EXISTS (SELECT FROM paper_order WHERE order_id=oid AND side='SELL')
                AND NOT EXISTS (SELECT FROM paper_market_event WHERE decision_id=NEW.decision_id
                AND reference_event_id=NEW.event_id AND event_type='EXIT_SATISFIED') THEN
                RAISE EXCEPTION 'Flat sale requires exit satisfaction' USING ERRCODE='23000';
            END IF;
        END IF;
        IF NEW.event_type='ORDER_REJECTED' AND NEW.reason_code='EXIT_BLOCKED_DUST'
            AND NOT EXISTS (SELECT FROM paper_market_event WHERE reference_event_id=NEW.event_id
                AND event_type='EXIT_BLOCKED_DUST') THEN
            RAISE EXCEPTION 'Dust rejection requires evidence' USING ERRCODE='23000';
        END IF;
    END IF;
    IF oid IS NOT NULL THEN
        SELECT status INTO STRICT status_now FROM paper_order WHERE order_id=oid;
        SELECT CASE event_type WHEN 'FILL' THEN 'FILLED' WHEN 'ORDER_EXPIRED' THEN 'EXPIRED'
                ELSE 'REJECTED' END INTO evidence FROM paper_market_event WHERE order_id=oid
                AND event_type IN ('FILL','ORDER_REJECTED','ORDER_EXPIRED');
        IF status_now='SUBMITTED' AND EXISTS (
            SELECT FROM paper_order pending JOIN paper_portfolio p USING(portfolio_id)
            WHERE pending.order_id=oid AND pending.snapshot_seq<>p.ledger_highwater
        ) THEN
            RAISE EXCEPTION 'Outstanding intent has stale ledger prefix' USING ERRCODE='23000';
        END IF;
        IF status_now<>coalesce(evidence,'SUBMITTED') THEN
            RAISE EXCEPTION 'Terminal status/evidence mismatch' USING ERRCODE='23000';
        END IF;
    END IF;
    RETURN NULL;
END $$;
