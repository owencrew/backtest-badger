CREATE DOMAIN paper_key AS text CHECK (btrim(VALUE) <> '' AND length(VALUE) <= 1024);
CREATE DOMAIN paper_hash AS text CHECK (VALUE ~ '^[0-9a-f]{64}$');
CREATE DOMAIN paper_number AS numeric CHECK (VALUE > '-Infinity' AND VALUE < 'Infinity');
CREATE DOMAIN paper_instant AS timestamptz CHECK (isfinite(VALUE));

-- v1 has scalar configuration values and one fixed integer weight array.
-- UTF-8, C-sorted keys and compact separators match paper_records.canonical.
CREATE FUNCTION paper_config_text(config jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT
    SET search_path = pg_catalog, public, pg_temp AS $$
    SELECT '{' || string_agg(to_json(key)::text || ':' ||
        CASE WHEN key='target_weights' THEN replace(value::text,', ',',')
             ELSE value::text END, ',' ORDER BY key COLLATE "C") || '}'
    FROM jsonb_each(config)
$$;

CREATE TABLE paper_portfolio (
    portfolio_id uuid PRIMARY KEY, portfolio_key paper_key NOT NULL UNIQUE,
    market_id smallint NOT NULL REFERENCES market,
    base_asset text NOT NULL CHECK (base_asset IN ('ETH','BTC')),
    quote_asset text NOT NULL CHECK (quote_asset='USDT'),
    strategy_id text NOT NULL CHECK (strategy_id='ridge_sign'),
    strategy_version text NOT NULL CHECK (strategy_version='1'),
    model_id text NOT NULL CHECK (model_id='ridge'),
    strategy_config jsonb NOT NULL CHECK (jsonb_typeof(strategy_config)='object'),
    config_canonical text NOT NULL CHECK (config_canonical=paper_config_text(strategy_config)),
    strategy_config_sha256 paper_hash NOT NULL CHECK (strategy_config_sha256=encode(sha256(convert_to(config_canonical,'UTF8')),'hex')), protocol_sha256 paper_hash NOT NULL,
    implementation_sha256 paper_hash NOT NULL, model_recipe_sha256 paper_hash NOT NULL,
    execution_policy_sha256 paper_hash NOT NULL, valuation_policy_sha256 paper_hash NOT NULL,
    -- Frozen JSON shape for the v1 policy. Cross-check the versioned Python
    -- configuration against this independent contract on every portfolio insert.
    CHECK (strategy_config - ARRAY['cohort','symbol','model_recipe_sha256'] =
        '
        {
          "schema": "stage-4a-v1",
          "venue": "binance",
          "market_type": "spot",
          "strategy": "ridge_sign",
          "strategy_version": "1",
          "model": "ridge",
          "threshold": "1e-12",
          "target_weights": [
            0,
            1
          ],
          "fee_rate": "0.001",
          "fee_quantum": "1E-8",
          "slippage": "0.0002",
          "execution": "stage-4a-execution-v1",
          "valuation": "stage-4a-bid-v1",
          "cost_basis": "weighted_average",
          "filters": "effective-market-filters-v1",
          "filter_ttl_seconds": 3600,
          "order_ttl_seconds": 30,
          "quote_rtt_seconds": 2,
          "receipt_ttl_seconds": 1,
          "exit_retry_seconds": 300,
          "source_interval_seconds": 14400,
          "availability_seconds": 60,
          "deadline_seconds": 960,
          "risk_exit_misses": 2,
          "mark_offset_seconds": 600,
          "mark_window_seconds": 300
        }
        '::jsonb
        AND jsonb_typeof(strategy_config->'cohort') IS NOT DISTINCT FROM 'string'
        AND length(btrim(strategy_config->>'cohort')) BETWEEN 1 AND 1024
        AND (strategy_config->>'symbol') IS NOT DISTINCT FROM base_asset||quote_asset
        AND (strategy_config->>'model_recipe_sha256') IS NOT DISTINCT FROM model_recipe_sha256),
    CHECK (execution_policy_sha256=encode(sha256(convert_to('stage-4a-execution-v1','UTF8')),'hex')
        AND valuation_policy_sha256=encode(sha256(convert_to('stage-4a-bid-v1','UTF8')),'hex')),
    initial_cash paper_number NOT NULL CHECK (initial_cash=10000),
    created_at paper_instant NOT NULL, inception_at paper_instant NOT NULL,
    activated_at paper_instant, state_event_id uuid,
    state text NOT NULL DEFAULT 'DRAFT' CHECK (state IN ('DRAFT','ACTIVE','PAUSED','CLOSED')),
    ledger_highwater bigint NOT NULL DEFAULT 0 CHECK (ledger_highwater >= 0),
    CHECK (created_at <= inception_at AND inception_at <= activated_at),
    CHECK ((state='DRAFT')=(activated_at IS NULL) AND (state='DRAFT')=(state_event_id IS NULL))
);

CREATE TABLE paper_decision (
    decision_id uuid PRIMARY KEY, portfolio_id uuid NOT NULL REFERENCES paper_portfolio,
    decision_key paper_key NOT NULL, UNIQUE (portfolio_id, decision_key),
    UNIQUE (portfolio_id, decision_id),
    kind text NOT NULL CHECK (kind IN ('FORECAST','MISSED_SIGNAL','RISK_EXIT')),
    source_open_time paper_instant NOT NULL, target_close_boundary paper_instant NOT NULL,
    forecast_record_id paper_key, prediction_id paper_key, artifact_relpath paper_key,
    forecast_file_sha256 paper_hash, forecast_content_sha256 paper_hash,
    forecast_issued_at paper_instant, forecast_observed_at paper_instant,
    automation_sha256 paper_hash, model_recipe_sha256 paper_hash, cohort paper_key,
    model_forecast paper_number, target_exposure smallint CHECK (target_exposure IN (0,1)),
    decision_result text NOT NULL CHECK (decision_result IN ('BUY_REQUIRED','EXIT_REQUIRED','HOLD',
        'CASH_NOOP','IGNORED_EXIT_PENDING','SIGNAL_MISSED','SIGNAL_STALE','SIGNAL_INELIGIBLE')),
    is_exit_obligation boolean NOT NULL CHECK (is_exit_obligation=(decision_result='EXIT_REQUIRED')),
    obligation_key paper_key,
    FOREIGN KEY (portfolio_id,obligation_key) REFERENCES paper_decision(portfolio_id,decision_key),
    missed_streak integer NOT NULL CHECK (missed_streak >= 0), reason_code paper_key NOT NULL,
    strategy_config_sha256 paper_hash NOT NULL, decided_at paper_instant NOT NULL,
    created_at paper_instant NOT NULL CHECK (created_at>=decided_at),
    CHECK (mod(extract(epoch FROM source_open_time),14400)=0
        AND target_close_boundary=source_open_time+interval '8 hours'),
    CHECK (artifact_relpath ~ '^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$'
        AND artifact_relpath !~ '(^|/)[.]{1,2}(/|$)'),
    CHECK (forecast_issued_at<=forecast_observed_at AND forecast_observed_at<=decided_at),
    CHECK (num_nonnulls(forecast_record_id,prediction_id,artifact_relpath,forecast_file_sha256,
        forecast_content_sha256,forecast_issued_at,forecast_observed_at,model_forecast,
        target_exposure,model_recipe_sha256,cohort) = CASE WHEN kind='FORECAST' THEN 11 ELSE 0 END),
    CHECK (kind='FORECAST' OR (automation_sha256 IS NULL AND missed_streak>0
        AND decided_at>source_open_time+interval '4 hours 16 minutes')),
    CHECK (kind<>'RISK_EXIT' OR (is_exit_obligation AND missed_streak>=2)),
    CHECK (kind<>'MISSED_SIGNAL' OR decision_result IN ('SIGNAL_MISSED','SIGNAL_STALE')),
    CHECK (target_exposure=(model_forecast>0.000000000001)::int)
);
CREATE UNIQUE INDEX paper_forecast_horizon ON paper_decision(portfolio_id,source_open_time)
    WHERE kind='FORECAST';
CREATE UNIQUE INDEX paper_forecast_original ON paper_decision(portfolio_id,forecast_record_id)
    WHERE kind='FORECAST';
CREATE UNIQUE INDEX paper_missed_horizon ON paper_decision(portfolio_id,source_open_time)
    WHERE kind<>'FORECAST';

CREATE TABLE paper_order (
    order_id uuid PRIMARY KEY, portfolio_id uuid NOT NULL, decision_id uuid NOT NULL,
    client_order_key paper_key NOT NULL, run_id paper_key NOT NULL,
    side text NOT NULL CHECK (side IN ('BUY','SELL')), intent text NOT NULL,
    attempt_number integer NOT NULL CHECK (attempt_number>=1),
    budget_cash_snapshot paper_number NOT NULL CHECK (budget_cash_snapshot>=0),
    base_qty_snapshot paper_number NOT NULL CHECK (base_qty_snapshot>=0),
    snapshot_seq bigint NOT NULL CHECK (snapshot_seq>=1 AND mod(snapshot_seq,2)=1),
    snapshot_at paper_instant NOT NULL CHECK (snapshot_at<=submitted_at),
    submitted_at paper_instant NOT NULL, expires_at paper_instant NOT NULL,
    created_at paper_instant NOT NULL CHECK (created_at=submitted_at),
    policy_sha256 paper_hash NOT NULL, status text NOT NULL DEFAULT 'SUBMITTED'
        CHECK (status IN ('SUBMITTED','FILLED','REJECTED','EXPIRED')),
    CHECK (expires_at=submitted_at+interval '30 seconds'),
    CHECK ((side='BUY' AND intent='SPEND_AVAILABLE_CASH' AND attempt_number=1)
        OR (side='SELL' AND intent='SELL_ALL_BASE')),
    UNIQUE (portfolio_id,client_order_key), UNIQUE (decision_id,side,attempt_number),
    UNIQUE (portfolio_id,order_id), UNIQUE (portfolio_id,order_id,decision_id),
    FOREIGN KEY (portfolio_id,decision_id) REFERENCES paper_decision(portfolio_id,decision_id)
);
CREATE UNIQUE INDEX paper_one_submitted ON paper_order(portfolio_id) WHERE status='SUBMITTED';

CREATE TABLE paper_market_event (
    event_id uuid PRIMARY KEY, portfolio_id uuid NOT NULL REFERENCES paper_portfolio,
    order_id uuid, decision_id uuid, quote_event_id uuid, reference_event_id uuid,
    event_type text NOT NULL CHECK (event_type IN ('QUOTE_OBSERVED','QUOTE_FAILED','FILL',
        'ORDER_REJECTED','ORDER_EXPIRED','MARK_OBSERVED','MARK_MISSING','EXIT_SATISFIED',
        'PAUSE','RESUME','RECOVERY_NOTE','EXIT_BLOCKED_DUST')),
    event_at paper_instant NOT NULL, recorded_at paper_instant NOT NULL CHECK (recorded_at>=event_at),
    run_id paper_key, quote_key paper_key, request_started_at paper_instant,
    response_received_at paper_instant, latency_ms paper_number CHECK (latency_ms>=0),
    source_url paper_key CHECK (source_url ~
        '^https://[A-Za-z0-9.-]+/[A-Za-z0-9/_.-]+([?]symbol=(BTCUSDT|ETHUSDT))?$'),
    http_status integer CHECK (http_status BETWEEN 100 AND 599),
    raw_body bytea CHECK (octet_length(raw_body)<=4096), raw_body_sha256 paper_hash,
    bid_price paper_number CHECK (bid_price>0), ask_price paper_number CHECK (ask_price>=bid_price),
    bid_qty paper_number CHECK (bid_qty>=0), ask_qty paper_number CHECK (ask_qty>=0),
    simulated_qty paper_number CHECK (simulated_qty>0), simulated_price paper_number CHECK (simulated_price>0),
    gross_notional paper_number CHECK (gross_notional=simulated_qty*simulated_price),
    fee_usdt paper_number CHECK (fee_usdt>0), ledger_seq_before bigint, ledger_seq_after bigint,
    mark_slot paper_instant, asof_ledger_seq bigint CHECK (asof_ledger_seq>=1 AND mod(asof_ledger_seq,2)=1),
    valuation_policy_sha256 paper_hash, filter_rules_json jsonb, filter_raw_sha256 paper_hash,
    filter_observed_at paper_instant, reason_code paper_key, policy_sha256 paper_hash,
    UNIQUE (portfolio_id,event_id),
    FOREIGN KEY (portfolio_id,order_id) REFERENCES paper_order(portfolio_id,order_id),
    FOREIGN KEY (portfolio_id,decision_id) REFERENCES paper_decision(portfolio_id,decision_id),
    FOREIGN KEY (portfolio_id,order_id,decision_id) REFERENCES paper_order(portfolio_id,order_id,decision_id),
    FOREIGN KEY (portfolio_id,quote_event_id) REFERENCES paper_market_event(portfolio_id,event_id),
    FOREIGN KEY (portfolio_id,reference_event_id) REFERENCES paper_market_event(portfolio_id,event_id),
    CHECK ((order_id IS NULL)=(decision_id IS NULL)),
    CHECK ((order_id IS NOT NULL)=(event_type IN ('QUOTE_OBSERVED','QUOTE_FAILED','ORDER_REJECTED',
        'ORDER_EXPIRED','FILL','EXIT_SATISFIED','EXIT_BLOCKED_DUST'))),
    CHECK (num_nonnulls(simulated_qty,simulated_price,gross_notional,fee_usdt,
        ledger_seq_before,ledger_seq_after) = CASE WHEN event_type='FILL' THEN 6 ELSE 0 END),
    CHECK (num_nonnulls(quote_event_id,filter_rules_json,filter_raw_sha256,filter_observed_at)
        = CASE WHEN event_type IN ('FILL','EXIT_BLOCKED_DUST') THEN 4 ELSE 0 END),
    CHECK (ledger_seq_before>=1 AND mod(ledger_seq_before,2)=1 AND ledger_seq_after=ledger_seq_before+2),
    CHECK ((policy_sha256 IS NOT NULL)=(event_type='FILL')),
    CHECK ((reference_event_id IS NOT NULL)=(event_type IN ('EXIT_SATISFIED','EXIT_BLOCKED_DUST'))),
    CHECK ((reason_code IS NOT NULL)=(event_type NOT IN ('FILL','QUOTE_OBSERVED','MARK_OBSERVED')
        OR reason_code IS NOT DISTINCT FROM 'INCEPTION')),
    CHECK (num_nonnulls(bid_price,ask_price,bid_qty,ask_qty)=
        CASE WHEN event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED') THEN 4 ELSE 0 END),
    CHECK ((run_id IS NOT NULL)=(event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED','QUOTE_FAILED','FILL','EXIT_BLOCKED_DUST'))),
    CHECK ((quote_key IS NOT NULL)=(event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED','QUOTE_FAILED'))),
    CHECK ((raw_body IS NULL)=(raw_body_sha256 IS NULL)
        AND raw_body_sha256=encode(sha256(raw_body),'hex')),
    CHECK ((request_started_at IS NOT NULL AND source_url IS NOT NULL)
        OR (request_started_at IS NULL AND source_url IS NULL)),
    CHECK ((request_started_at IS NOT NULL)=(event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED','QUOTE_FAILED'))),
    CHECK (response_received_at>=request_started_at AND event_at>=request_started_at
        AND response_received_at<=event_at),
    CHECK (event_type IN ('QUOTE_OBSERVED','MARK_OBSERVED','QUOTE_FAILED')
        OR num_nonnulls(response_received_at,latency_ms,http_status,raw_body)=0),
    CHECK (event_type NOT IN ('QUOTE_OBSERVED','MARK_OBSERVED') OR (
        num_nonnulls(raw_body,response_received_at,http_status)=3 AND http_status=200
        AND latency_ms<=2000 AND response_received_at-request_started_at<=interval '2 seconds'
        AND event_at-response_received_at<=interval '1 second')),
    CHECK ((mark_slot IS NOT NULL)=(event_type IN ('MARK_OBSERVED','MARK_MISSING'))
        AND (valuation_policy_sha256 IS NULL)=(mark_slot IS NULL)
        AND (asof_ledger_seq IS NOT NULL)=(event_type='MARK_OBSERVED')),
    CHECK (mod(extract(epoch FROM mark_slot)-600,14400)=0),
    CHECK (event_type<>'MARK_OBSERVED' OR (request_started_at>=mark_slot
        AND event_at<mark_slot+interval '5 minutes')),
    CHECK (event_type<>'MARK_MISSING' OR event_at>=mark_slot+interval '5 minutes')
);
ALTER TABLE paper_portfolio ADD CONSTRAINT paper_state_evidence
    FOREIGN KEY (portfolio_id,state_event_id) REFERENCES paper_market_event(portfolio_id,event_id);
CREATE UNIQUE INDEX paper_terminal ON paper_market_event(order_id)
    WHERE event_type IN ('FILL','ORDER_REJECTED','ORDER_EXPIRED');
CREATE UNIQUE INDEX paper_fill_quote ON paper_market_event(quote_event_id) WHERE event_type='FILL';
CREATE UNIQUE INDEX paper_quote_identity ON paper_market_event(portfolio_id,quote_key) WHERE quote_key IS NOT NULL;
CREATE UNIQUE INDEX paper_exit_once ON paper_market_event(decision_id) WHERE event_type='EXIT_SATISFIED';
CREATE UNIQUE INDEX paper_exit_reference ON paper_market_event(reference_event_id) WHERE reference_event_id IS NOT NULL;
CREATE UNIQUE INDEX paper_mark_slot ON paper_market_event(portfolio_id,mark_slot,valuation_policy_sha256)
    WHERE mark_slot IS NOT NULL;
CREATE INDEX paper_event_time ON paper_market_event(portfolio_id,event_at);
CREATE INDEX paper_decision_time ON paper_decision(portfolio_id,decided_at);

CREATE TABLE paper_ledger_entry (
    ledger_entry_id uuid PRIMARY KEY, portfolio_id uuid NOT NULL REFERENCES paper_portfolio,
    ledger_seq bigint NOT NULL CHECK (ledger_seq>=1), entry_type text NOT NULL,
    fill_event_id uuid, asset text NOT NULL, delta_units paper_number NOT NULL CHECK (delta_units<>0),
    posted_at paper_instant NOT NULL, UNIQUE (portfolio_id,ledger_seq), UNIQUE (fill_event_id,asset),
    FOREIGN KEY (portfolio_id,fill_event_id) REFERENCES paper_market_event(portfolio_id,event_id),
    CHECK ((entry_type='INITIAL_FUNDING' AND asset='USDT' AND delta_units=10000
        AND ledger_seq=1 AND fill_event_id IS NULL)
        OR (entry_type='FILL' AND fill_event_id IS NOT NULL AND ledger_seq>1))
);
