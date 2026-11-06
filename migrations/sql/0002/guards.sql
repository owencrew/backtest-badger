CREATE FUNCTION paper_immutable() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    RAISE EXCEPTION 'Paper evidence is immutable' USING ERRCODE='23000';
END $$;

CREATE FUNCTION paper_lock(pid uuid) RETURNS paper_portfolio LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio;
BEGIN
    -- Re-read under the lock using READ COMMITTED's fresh statement snapshots.
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'Paper writes require read committed isolation' USING ERRCODE='23000';
    END IF;
    SELECT * INTO STRICT p FROM paper_portfolio WHERE portfolio_id=pid FOR UPDATE;
    RETURN p;
END $$;

CREATE FUNCTION paper_latest(pid uuid) RETURNS timestamptz LANGUAGE sql STABLE
    SET search_path = pg_catalog, public, pg_temp AS $$
    SELECT greatest((SELECT max(recorded_at) FROM paper_market_event WHERE portfolio_id=pid),
                    (SELECT max(created_at) FROM paper_decision WHERE portfolio_id=pid),
                    (SELECT max(submitted_at) FROM paper_order WHERE portfolio_id=pid))
$$;

CREATE FUNCTION paper_pending(pid uuid) RETURNS SETOF uuid LANGUAGE sql STABLE
    SET search_path = pg_catalog, public, pg_temp AS $$
    SELECT decision_id FROM paper_decision d WHERE portfolio_id=pid AND is_exit_obligation
    AND NOT EXISTS (SELECT FROM paper_market_event e WHERE e.decision_id=d.decision_id
        AND e.event_type='EXIT_SATISFIED')
$$;

CREATE FUNCTION paper_guard_portfolio() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF TG_OP='INSERT' THEN
        IF NEW.state<>'DRAFT' OR NEW.ledger_highwater<>0 OR NOT EXISTS (
            SELECT FROM market WHERE market_id=NEW.market_id AND venue='binance'
            AND market_type='spot' AND base_asset=NEW.base_asset AND quote_asset='USDT'
            AND symbol=NEW.base_asset||'USDT' FOR SHARE) THEN
            RAISE EXCEPTION 'Invalid initial portfolio' USING ERRCODE='23000';
        END IF;
    ELSIF TG_OP='DELETE' OR
        to_jsonb(OLD)-ARRAY['state','activated_at','ledger_highwater','state_event_id']
        <> to_jsonb(NEW)-ARRAY['state','activated_at','ledger_highwater','state_event_id']
        OR (ROW(OLD.state,OLD.activated_at,OLD.state_event_id) IS DISTINCT FROM
            ROW(NEW.state,NEW.activated_at,NEW.state_event_id) AND pg_trigger_depth()<>2)
        THEN RAISE EXCEPTION 'Immutable portfolio or unaudited transition' USING ERRCODE='23000';
    END IF;
    IF TG_OP='UPDATE' AND NEW.ledger_highwater<>OLD.ledger_highwater AND
        (NEW.ledger_highwater<>coalesce((SELECT max(ledger_seq) FROM paper_ledger_entry
            WHERE portfolio_id=NEW.portfolio_id),0) OR NEW.ledger_highwater<OLD.ledger_highwater) THEN
        RAISE EXCEPTION 'Invalid high-water advance' USING ERRCODE='23000';
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION paper_preserve_market() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF EXISTS (SELECT FROM paper_portfolio WHERE market_id=OLD.market_id) THEN
        RAISE EXCEPTION 'Market identity pinned by portfolio' USING ERRCODE='23000';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER paper_preserve_market BEFORE UPDATE ON market FOR EACH ROW
    WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION paper_preserve_market();

CREATE FUNCTION paper_guard_decision() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio; held numeric; pending boolean; eligible boolean;
    prev paper_decision; expected_source timestamptz; streak integer; satisfied timestamptz;
    expected_result text; obligation paper_key;
BEGIN
    IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Immutable decision' USING ERRCODE='23000'; END IF;
    p := paper_lock(NEW.portfolio_id);
    IF p.state<>'ACTIVE' OR NEW.strategy_config_sha256<>p.strategy_config_sha256 OR
        NEW.decided_at < greatest(p.activated_at,paper_latest(p.portfolio_id)) THEN
        RAISE EXCEPTION 'Invalid decision state, time or configuration' USING ERRCODE='23000';
    END IF;
    SELECT * INTO prev FROM paper_decision WHERE portfolio_id=p.portfolio_id
        AND decision_result<>'SIGNAL_INELIGIBLE' ORDER BY source_open_time DESC LIMIT 1;
    expected_source := coalesce(prev.source_open_time+interval '4 hours',
        date_bin(interval '4 hours',p.activated_at-interval '16 minutes',timestamptz '2000-01-01 UTC'));
    streak := coalesce(prev.missed_streak,0);
    IF NEW.source_open_time<>expected_source THEN
        RAISE EXCEPTION 'Unexpected source horizon' USING ERRCODE='23000';
    END IF;
    SELECT coalesce(sum(delta_units),0) INTO held FROM paper_ledger_entry
        WHERE portfolio_id=p.portfolio_id AND asset=p.base_asset;
    pending := EXISTS (SELECT FROM paper_pending(p.portfolio_id));
    IF NEW.kind='FORECAST' THEN
        eligible := NEW.forecast_issued_at>p.activated_at
            AND NEW.forecast_issued_at>=NEW.source_open_time+interval '4 hours 1 minute'
            AND NEW.decided_at<NEW.source_open_time+interval '4 hours 16 minutes'
            AND NEW.model_recipe_sha256=p.model_recipe_sha256 AND NEW.automation_sha256 IS NOT NULL
            AND NEW.cohort='primary_timely_automated';
        SELECT max(event_at) INTO satisfied FROM paper_market_event WHERE portfolio_id=p.portfolio_id
            AND event_type='EXIT_SATISFIED';
        expected_result := CASE WHEN NOT eligible THEN 'SIGNAL_INELIGIBLE'
            WHEN pending THEN 'IGNORED_EXIT_PENDING' WHEN NEW.forecast_issued_at<=satisfied THEN 'CASH_NOOP'
            WHEN NEW.target_exposure=1 AND held=0 THEN 'BUY_REQUIRED'
            WHEN NEW.target_exposure=1 THEN 'HOLD' WHEN held>0 THEN 'EXIT_REQUIRED' ELSE 'CASH_NOOP' END;
        IF eligible THEN streak := 0; END IF;
    ELSE
        streak := streak+1;
        expected_result := CASE WHEN NOT pending AND held>0 AND streak>=2 THEN 'EXIT_REQUIRED'
            WHEN held>0 THEN 'SIGNAL_STALE' ELSE 'SIGNAL_MISSED' END;
    END IF;
    IF expected_result='EXIT_REQUIRED' THEN obligation := NEW.decision_key;
    ELSIF expected_result<>'SIGNAL_INELIGIBLE' AND pending THEN
        SELECT decision_key INTO STRICT obligation FROM paper_decision
            WHERE decision_id IN (SELECT paper_pending(p.portfolio_id));
    END IF;
    IF NEW.obligation_key IS DISTINCT FROM obligation OR NEW.decision_result<>expected_result OR NEW.missed_streak<>streak THEN
        RAISE EXCEPTION 'Decision conflicts with durable strategy state' USING ERRCODE='23000';
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION paper_guard_order() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio; d paper_decision; cash numeric; held numeric; last_attempt paper_order;
BEGIN
    IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Immutable order' USING ERRCODE='23000'; END IF;
    p := paper_lock(NEW.portfolio_id);
    IF TG_OP='UPDATE' THEN
        IF to_jsonb(NEW)-'status' <> to_jsonb(OLD)-'status' OR OLD.status<>'SUBMITTED'
            OR NEW.status='SUBMITTED' THEN
            RAISE EXCEPTION 'Illegal order transition' USING ERRCODE='23000';
        END IF;
        RETURN NEW;
    END IF;
    SELECT * INTO STRICT d FROM paper_decision WHERE decision_id=NEW.decision_id
        AND portfolio_id=p.portfolio_id;
    SELECT coalesce(sum(delta_units) FILTER (WHERE asset='USDT'),0),
        coalesce(sum(delta_units) FILTER (WHERE asset=p.base_asset),0)
        INTO cash,held FROM paper_ledger_entry WHERE portfolio_id=p.portfolio_id;
    SELECT * INTO last_attempt FROM paper_order WHERE decision_id=d.decision_id
        ORDER BY attempt_number DESC LIMIT 1;
    IF p.state<>'ACTIVE' OR NEW.status<>'SUBMITTED' OR NEW.policy_sha256<>p.execution_policy_sha256
        OR NEW.snapshot_at<(SELECT max(posted_at) FROM paper_ledger_entry WHERE portfolio_id=p.portfolio_id)
        OR NEW.snapshot_seq<>p.ledger_highwater OR NEW.base_qty_snapshot<>held OR NEW.budget_cash_snapshot<>cash
        OR NEW.submitted_at<d.created_at OR NEW.submitted_at<paper_latest(p.portfolio_id)
        OR NEW.attempt_number<>coalesce(last_attempt.attempt_number,0)+1
        OR NEW.submitted_at<last_attempt.submitted_at+interval '5 minutes'
        OR (NEW.side='SELL' AND (held<=0 OR NOT EXISTS (SELECT FROM paper_pending(p.portfolio_id)
            AS t(id) WHERE t.id=d.decision_id)))
        OR (NEW.side='BUY' AND (held<>0 OR d.decision_result<>'BUY_REQUIRED'
            OR NEW.submitted_at>=d.source_open_time+interval '4 hours 16 minutes'
            OR EXISTS (SELECT FROM paper_pending(p.portfolio_id))
            OR EXISTS (SELECT FROM paper_market_event WHERE portfolio_id=p.portfolio_id
                AND event_type='EXIT_SATISFIED' AND event_at>=d.forecast_issued_at))) THEN
        RAISE EXCEPTION 'Invalid order intent or stale snapshot' USING ERRCODE='23000';
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION paper_fee(n numeric) RETURNS numeric LANGUAGE sql IMMUTABLE STRICT
    SET search_path = pg_catalog, public, pg_temp AS $$
    SELECT ceil(n*100000)*0.00000001
$$;

CREATE FUNCTION paper_guard_market_event() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio; o paper_order; q paper_market_event; body jsonb;
    ref paper_market_event; step numeric; next_n numeric; rules jsonb;
BEGIN
    IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Immutable event' USING ERRCODE='23000'; END IF;
    p := paper_lock(NEW.portfolio_id);
    IF NEW.event_at<p.created_at OR (NEW.reference_event_id IS NULL
        AND NEW.event_at<paper_latest(p.portfolio_id)) THEN
        RAISE EXCEPTION 'Event time reversal' USING ERRCODE='23000';
    END IF;
    IF position('?' IN NEW.source_url)>0 AND split_part(NEW.source_url,'?symbol=',2)<>p.base_asset||'USDT' THEN
        RAISE EXCEPTION 'Quote source symbol mismatch' USING ERRCODE='23000';
    END IF;
    IF NEW.order_id IS NOT NULL THEN
        SELECT * INTO STRICT o FROM paper_order WHERE order_id=NEW.order_id AND portfolio_id=p.portfolio_id;
        IF NEW.event_type NOT IN ('EXIT_SATISFIED','EXIT_BLOCKED_DUST') AND o.status<>'SUBMITTED' THEN
            RAISE EXCEPTION 'Attempt already terminal' USING ERRCODE='23000';
        END IF;
        IF NEW.request_started_at IS NOT NULL AND EXISTS (SELECT FROM paper_order
            WHERE order_id=o.order_id AND xmin=pg_current_xact_id()::xid) THEN
            RAISE EXCEPTION 'Quote requires previously committed order' USING ERRCODE='23000';
        END IF;
        IF NEW.request_started_at<o.submitted_at OR NEW.run_id<>o.run_id OR
            (NEW.event_type='ORDER_EXPIRED' AND NEW.event_at<o.expires_at) THEN
            RAISE EXCEPTION 'Invalid attempt time or worker run' USING ERRCODE='23000';
        END IF;
    END IF;
    IF NEW.event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED') THEN
        IF NOT (convert_from(NEW.raw_body,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
            RAISE EXCEPTION 'Invalid original quote' USING ERRCODE='23000';
        END IF;
        body := convert_from(NEW.raw_body,'UTF8')::jsonb;
        IF EXISTS (SELECT FROM jsonb_each(body) WHERE jsonb_typeof(value)<>'string')
            OR NOT (body ?& ARRAY['symbol','bidPrice','askPrice','bidQty','askQty'])
            OR body-ARRAY['symbol','bidPrice','askPrice','bidQty','askQty'] <> '{}'::jsonb
            OR body->>'symbol' IS DISTINCT FROM p.base_asset||'USDT'
            OR (body->>'bidPrice')::numeric IS DISTINCT FROM NEW.bid_price
            OR (body->>'askPrice')::numeric IS DISTINCT FROM NEW.ask_price
            OR (body->>'bidQty')::numeric IS DISTINCT FROM NEW.bid_qty
            OR (body->>'askQty')::numeric IS DISTINCT FROM NEW.ask_qty THEN
            RAISE EXCEPTION 'Quote disagrees with original body' USING ERRCODE='23000';
        END IF;
    END IF;
    IF NEW.event_type='MARK_OBSERVED' AND p.state='DRAFT'
        AND NEW.reason_code IS DISTINCT FROM 'INCEPTION' THEN
        RAISE EXCEPTION 'First mark must establish inception' USING ERRCODE='23000';
    END IF;
    IF NEW.event_type='MARK_OBSERVED' AND EXISTS (
        SELECT FROM paper_market_event WHERE portfolio_id=p.portfolio_id AND event_type='FILL'
            AND ledger_seq_after>p.ledger_highwater) THEN
        RAISE EXCEPTION 'Cannot mark an incomplete financial transition' USING ERRCODE='23000';
    END IF;
    IF NEW.mark_slot IS NOT NULL AND (NEW.valuation_policy_sha256<>p.valuation_policy_sha256
        OR NEW.asof_ledger_seq<>p.ledger_highwater OR NEW.request_started_at<p.inception_at
        OR NEW.response_received_at<(SELECT max(posted_at) FROM paper_ledger_entry WHERE portfolio_id=p.portfolio_id))
        THEN RAISE EXCEPTION 'Invalid mark snapshot' USING ERRCODE='23000';
    END IF;
    IF NEW.event_type IN ('FILL','EXIT_BLOCKED_DUST') THEN
        SELECT * INTO STRICT q FROM paper_market_event WHERE event_id=NEW.quote_event_id
            AND portfolio_id=p.portfolio_id;
        rules := NEW.filter_rules_json;
        IF NOT (rules ?& ARRAY['step','min_quantity','max_quantity','min_notional','max_notional',
            'symbol','version']) OR rules->>'symbol' IS DISTINCT FROM p.base_asset||'USDT'
            OR rules->>'version' IS DISTINCT FROM 'effective-market-filters-v1' THEN
            RAISE EXCEPTION 'Missing effective filter rules' USING ERRCODE='23000';
        END IF;
        step := (rules->>'step')::paper_number;
        IF p.state<>'ACTIVE' OR q.event_type<>'QUOTE_OBSERVED' OR q.order_id IS DISTINCT FROM o.order_id
            OR q.run_id<>NEW.run_id OR NEW.event_at>=o.expires_at OR NEW.event_at<q.recorded_at
            OR NEW.event_at-q.response_received_at>interval '1 second'
            OR NEW.filter_observed_at>o.submitted_at OR NEW.event_at-NEW.filter_observed_at>interval '1 hour'
            OR step IS NULL OR step<=0 THEN
            RAISE EXCEPTION 'Invalid execution quote or filters' USING ERRCODE='23000';
        END IF;
        IF NEW.event_type='EXIT_BLOCKED_DUST' AND NOT coalesce(
            mod(o.base_qty_snapshot,step)<>0 OR o.base_qty_snapshot<(rules->>'min_quantity')::paper_number
            OR o.base_qty_snapshot*q.bid_price*0.9998<(rules->>'min_notional')::paper_number,false) THEN
            RAISE EXCEPTION 'Filters do not establish blocked dust' USING ERRCODE='23000';
        END IF;
    END IF;
    IF NEW.event_type='FILL' THEN
        next_n := (NEW.simulated_qty+step)*NEW.simulated_price;
        IF NEW.policy_sha256<>o.policy_sha256 OR NEW.ledger_seq_before<>p.ledger_highwater
            OR NEW.ledger_seq_before<>o.snapshot_seq
            OR NEW.fee_usdt<>paper_fee(NEW.gross_notional)
            OR step IS NULL OR step<=0 OR mod(NEW.simulated_qty,step)<>0
            OR NOT coalesce(0<=(rules->>'min_quantity')::paper_number AND
                NEW.simulated_qty BETWEEN (rules->>'min_quantity')::paper_number AND (rules->>'max_quantity')::paper_number
                AND (rules->>'min_notional')::paper_number BETWEEN 0 AND NEW.gross_notional,false)
            OR NEW.gross_notional>(rules->>'max_notional')::paper_number
            OR (o.side='BUY' AND (NEW.simulated_price<>q.ask_price*1.0002 OR NEW.simulated_qty>q.ask_qty
                OR NEW.gross_notional+NEW.fee_usdt>o.budget_cash_snapshot
                OR next_n+paper_fee(next_n)<=o.budget_cash_snapshot OR NEW.event_at>=
                (SELECT source_open_time+interval '4 hours 16 minutes' FROM paper_decision WHERE decision_id=o.decision_id)))
            OR (o.side='SELL' AND (NEW.simulated_price<>q.bid_price*0.9998 OR NEW.simulated_qty>q.bid_qty
                OR NEW.simulated_qty<>o.base_qty_snapshot OR NEW.fee_usdt>=NEW.gross_notional)) THEN
            RAISE EXCEPTION 'Invalid fill, quote, size, policy or fee' USING ERRCODE='23000';
        END IF;
    END IF;
    IF NEW.reference_event_id IS NOT NULL THEN
        SELECT * INTO STRICT ref FROM paper_market_event WHERE event_id=NEW.reference_event_id;
        IF ref.order_id IS DISTINCT FROM NEW.order_id OR ref.event_at<>NEW.event_at OR ref.recorded_at<>NEW.recorded_at OR o.side<>'SELL'
            OR (NEW.event_type='EXIT_SATISFIED' AND ref.event_type<>'FILL')
            OR (NEW.event_type='EXIT_BLOCKED_DUST' AND (ref.event_type<>'ORDER_REJECTED'
                OR ref.reason_code<>'EXIT_BLOCKED_DUST')) THEN
            RAISE EXCEPTION 'Invalid exit evidence' USING ERRCODE='23000';
        END IF;
    END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION paper_project_state() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio; target text;
BEGIN
    SELECT * INTO STRICT p FROM paper_portfolio WHERE portfolio_id=NEW.portfolio_id;
    IF NEW.event_type='MARK_OBSERVED' AND NEW.reason_code='INCEPTION' AND p.state='DRAFT'
        AND NEW.asof_ledger_seq=1 AND NEW.mark_slot<=p.inception_at THEN target := 'ACTIVE';
    ELSIF NEW.event_type IN ('PAUSE','EXIT_BLOCKED_DUST') AND p.state='ACTIVE' THEN target := 'PAUSED';
    ELSIF NEW.event_type='RESUME' AND p.state='PAUSED' AND NOT EXISTS (
        SELECT FROM paper_market_event WHERE event_id=p.state_event_id
        AND event_type='EXIT_BLOCKED_DUST') THEN target := 'ACTIVE';
    ELSIF NEW.event_type='RECOVERY_NOTE' AND NEW.reason_code='CLOSE' AND p.state='PAUSED'
        AND NOT EXISTS (SELECT FROM paper_order WHERE portfolio_id=p.portfolio_id AND status='SUBMITTED')
        AND NOT EXISTS (SELECT FROM paper_pending(p.portfolio_id))
        AND coalesce((SELECT sum(delta_units) FROM paper_ledger_entry WHERE portfolio_id=p.portfolio_id
            AND asset=p.base_asset),0)=0 THEN target := 'CLOSED';
    ELSE RAISE EXCEPTION 'Invalid portfolio state transition' USING ERRCODE='23000';
    END IF;
    UPDATE paper_portfolio SET state=target, activated_at=coalesce(activated_at,NEW.event_at),
        state_event_id=NEW.event_id WHERE portfolio_id=p.portfolio_id;
    RETURN NULL;
END $$;
CREATE TRIGGER paper_state AFTER INSERT ON paper_market_event FOR EACH ROW
    WHEN (NEW.event_type IN ('PAUSE','RESUME','EXIT_BLOCKED_DUST') OR NEW.reason_code IN ('INCEPTION','CLOSE'))
    EXECUTE FUNCTION paper_project_state();

CREATE FUNCTION paper_guard_ledger_entry() RETURNS trigger LANGUAGE plpgsql
    SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE p paper_portfolio;
BEGIN
    IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Immutable posting' USING ERRCODE='23000'; END IF;
    p := paper_lock(NEW.portfolio_id);
    IF NEW.entry_type='INITIAL_FUNDING' THEN
        IF NEW.posted_at<>p.inception_at OR p.state<>'DRAFT' OR p.ledger_highwater<>0 THEN
            RAISE EXCEPTION 'Invalid opening funding' USING ERRCODE='23000';
        END IF;
    ELSE
        -- Only two assets are admissible. UNIQUE(fill_event_id,asset) seals
        -- a complete pair against later insertions. Check amounts at commit.
        IF NEW.asset NOT IN ('USDT',p.base_asset) OR NOT EXISTS (
            SELECT FROM paper_market_event WHERE event_id=NEW.fill_event_id
            AND portfolio_id=p.portfolio_id AND event_type='FILL') THEN
            RAISE EXCEPTION 'Posting requires same-portfolio fill and asset' USING ERRCODE='23000';
        END IF;
    END IF;
    RETURN NEW;
END $$;
