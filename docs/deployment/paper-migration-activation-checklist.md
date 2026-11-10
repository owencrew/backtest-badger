# Paper trading operator checklist

**Review copy, 10 November 2026.** Production inspection and changes require separate approval. Each market requires its own subsequent activation decision. The executable rehearsal uses generated databases, fabricated observations and test logins. [Stage 4D.2 rehearsal](../stage-04d2-production-readiness.md)

## Before requesting a production change

- [ ] Obtain authorisation for a read-only host inventory. Record the service users, release, interpreter, timers, host UTC discipline, database endpoint/version/revision, owners, memberships, pg_hba rules, default/object ACLs, storage headroom, CPU/RAM peaks, journal sizes and rotation. Record paths and permissions without copying secrets.
- [ ] Resolve the actual collector record and journal roots. Verify safe traversal and read access under the proposed paper UID. Check evidence visibility across release changes. Review original market-specific recipe pins, both approved protocol files, implementation/dependency manifest and canonical configurations.
- [ ] Assign distinct private database logins. Restrict pg_hba access to the intended database. Inventory all users relying on PUBLIC CONNECT, TEMP, schema USAGE, function EXECUTE or large-object functions. Rehearse their exact access on an isolated restore before revoking anything. Include ingestion, collection, scoring, reporting, checkpoint and restore logins. Confirm no untrusted role can create in the search path or assume a runtime login.
- [ ] Obtain approval for the backup extension and demonstrate a recent encrypted checkpoint and independent restore. Compare the existing four-table revision 0001 baseline. Rehearse the new nine-table audit, role recreation with independent credentials, archive hashes and economic replay. Record restore point, measured restore time and the holder of the trusted manifest receipt.
- [ ] Obtain an explicit maintenance window, reviewed release SHA, migration owner and recovery owner. Verify no competing migrator or paper invocation, and check application compatibility at both revisions. Retain actual approvals, timestamps and decisions privately.

## Migration and forward recovery

Use this sequence only in an approved maintenance session with the reviewed release and verified **migration** environment already loaded. First match database identity and endpoint with the approved inventory. Keep credentials outside shell arguments and logs.

```sh
.venv/bin/alembic current
.venv/bin/alembic heads
.venv/bin/alembic upgrade 0002
.venv/bin/alembic current
```

- [ ] Expect current revision 0001 and head 0002 before upgrade. Inventory market/candle/revision fingerprints, indexes, constraints and triggers. On the observed admin-owned 0001, rehearse legacy-owner.sql before the ordinary paper owner runs 0002. Record the upgrade result and verify existing ownership and the same market rows afterward.
- [ ] Assemble the reviewed role-specific SQL in a transaction. Apply explicit legacy privileges **first**, provision the separate paper roles, then apply the reviewed schema grants and policies. Review protected built-in large-object ACLs with the cluster administrator. The template uses identifier placeholders and fresh roles. Translate it to the inspected deployment. [Grant template](../../ops/paper/grants.sql)
- [ ] Verify role attributes, memberships, schema and sequence privileges, pinned function paths, SECURITY DEFINER flags, column grants, row policies, enabled triggers and ownership. Use independent logins for negative tests. Run the collector/scorer's read queries and ingestion drill on the isolated copy. Validate a private reporting read.
- [ ] If upgrade fails, capture SQLSTATE, revision and object inventory. Verify rollback and unchanged market evidence. Preserve conflicts for review and retry only after addressing their cause. An empty downgrade requires separately approved maintenance and verification of emptiness.
- [ ] Once any portfolio exists, stop the paper service/timer, revoke its login/connect access, terminate its existing sessions under operator control, preserve journals and checkpoint the DB and private archive. Restore compatible application code with paper tables intact or apply a separately reviewed forward migration. Investigate discrepancies on an independent restore before approving repair or cutover.
- [ ] To revoke access, disable the relevant login, terminate existing sessions and revoke grants/memberships in the intended database. Retain ownership, triggers, policies and economic rows. Worker shutdown leaves collection and scoring on their existing release.

## Service and backup review

- [ ] Review an independent oneshot service with a dedicated paper UID, explicit single-cycle command, fresh invocation identity per process and per-portfolio exclusion. Use the Stage 4D.3B.1 production-once entry point and disabled unit templates. Verify actual mount access, cgroup identity, credentials and the independent network policy on the host.
- [ ] Proposed systemd controls include `User=badger-paper`, `UMask=0077`, `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`, `PrivateDevices=true`, `NoNewPrivileges=true`, an empty capability bounding set and `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`. Mount the two source roots read-only. Grant writes only to private evidence/operational state. Exclude Docker, deployment, website/R2 and backup credentials.
- [ ] Use the separate badger-archive publisher and idmapped read-only vault view. The paper UID (including separately authorised inception with operator DB credentials) publishes only through the peer-checked append socket. Give the backup identity independent read access. Test exclusive publication, denied rewrites/unlinks, directory sync, encrypted retention and restored ownership.
- [ ] Schedule one foreground invocation every five minutes UTC with catch-up disabled and bounded shutdown. Proposed review values are a 240 s runtime limit, 15 s stop, 384 MiB memory high, 512 MiB memory max and one CPU per process. Measure cold imports, full archive verification, aged ledgers and journal discovery with collection, scoring, public feed and backup active. Include simultaneous BTC/ETH processing.
- [ ] Require recent verified host synchronisation. The rehearsal gate requires a sample no older than five minutes with uncertainty at most 100 ms. Calibrate the trusted source and bound on the host. Recheck UTC at observation/use. Permit only the two symbol-specific HTTPS GETs on `data-api.binance.vision`, local PostgreSQL and required DNS. Verify DNS/TLS and egress from the service identity. Respect 418/429 and Retry-After across invocations.
- [ ] Extend the protected checkpoint process. Export one consistent PG17 snapshot for rows, schema and dump. Include all paper tables, reviewed role definitions/ACLs without passwords, originals and intent filter references. Protect the manifest hash separately. Preserve all referenced source bytes. Enable encrypted transport and receipt publication only after approval.
- [ ] Restore into isolated storage on a second cluster. Recreate roles with fresh credentials and database ACLs, then use a vetted recovery administrator for the single-transaction restore. Recheck every table, sequence, trigger, permission, source and account prefix. Establish RPO/RTO from actual checkpoint cadence and measured restore time. Verify alert delivery for backup failure, missed receipts and failed restore.

- [ ] Verify the separately pinned deployment manifest, machine identity, DB cluster and OID, effective grant fingerprint and source root device/inode. Run the reviewed identity-grants addendum on an isolated copy. Match the owner decision to exact installation bytes.
- [ ] Validate newly replaced 0600 journals through the read-only source view, root-controlled external clock observation and restricted network namespace. Verify the operational checkpoint receipt covers mutable journals, cooldowns, halts and a bounded systemd incident export.
- [ ] Exercise the per-market timer/service stop and database NOLOGIN/targeted session termination on fabricated resources. Confirm collector/scorer health throughout. [Stage 4D.3B.1 preflight and emergency procedure](../stage-04d3b1-lightsail-preflight.md)

## Per-market activation

- [ ] Record separate owner decisions for BTCUSDT and ETHUSDT. Pin independent keys, recipe/configuration/protocol/implementation hashes and exactly 10,000 simulated USDT per approved cohort. Keep financial execution disabled until its initial evidence commits.
- [ ] Select the next UTC +10-minute four-hour slot. Inside its five-minute window, sample actual start for creation and opening funding. Capture fresh filters and request a new quote after opening. Record original bytes, bid/ask/quantities, acquisition/use times, filter binding and complete ledger prefix. One transaction publishes ACTIVE and the observed mark. Record the actual outcome.
- [ ] If the quote fails, clock is uncertain or the window closes, roll back the entire inception transaction. Record the failed start and next proposed slot. Retain any archived objects. Resolve uncertain commits by stable cohort identity and audit all originals before retry. Equally named keys with different frozen configuration must fail.
- [ ] Verify separate opening balances and inception marks. Use the same first quote and filters for analytical Buy & Hold, or report benchmark unavailability if the full-size counterfactual fails. Cash stays a 10,000-USDT analytical control. Begin Ridge only from qualifying original forecasts issued after activation. Record actual enabled worker identity and first cycle. Public reporting has a separate approval gate.
