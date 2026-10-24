SSH connectivity to AWS Lightsail has already been tested successfully in this session using `ssh Ubuntu-1`.
Use this existing SSH alias for remote inspection. Request network approval again if required. Do not modify the active production release, restart services, change timers or perform database writes.
Proceed with Stage D3A as instructed below.

\# Backtest Badger — Stage D3A: Lightsail Production Reconciliation and Release Preparation\
\
\## Objective\
\
Bring Backtest Badger's existing AWS Lightsail infrastructure towards the latest reviewed GitHub release, without compromising production data, forward predictions, scoring, backups or monitoring.\
\
This is a personal quantitative research and portfolio project. Prioritise simplicity, reliability and maintaining an operational system.\
\
We have completed our first genuine historical backtest. The next major development milestone is the public website.\
\
\*\*This task is a focused production health audit and inactive-release preparation, not a new infrastructure project.\*\*\
\
\## Starting point\
\
Repository: \`owencrew/backtest-badger\`\
\
Latest expected GitHub commit:\
\
\`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1\`\
\
Latest GitHub Actions run:\
\
\`40106649560\`\
\
This run was still in progress at the previous check. Independently confirm whether it has completed successfully before staging this release. If it has not passed, complete the read-only inventory but do not prepare or promote that commit.\
\
Read \`AGENTS.md\` first.\
\
Then inspect:\
\
\- \`docs/deployment/production-infrastructure.md\`\
\- \`docs/deployment/lightsail-foundation.md\`\
\- \`docs/deployment/lightsail-migration-runbook.md\`\
\- \`docs/development-handoff.md\`\
\- \`ops/lightsail/prepare-release.sh\`\
\- \`ops/lightsail/status.sh\`\
\- \`ops/lightsail/validate.py\`\
\- Relevant systemd templates, service definitions and release preparation code\
\
Confirm the local checkout and working-tree status.\
\
\## Scope and authorisation\
\
I authorise:\
\
1\. Read-only inspection of the existing Backtest Badger Lightsail host through the previously configured SSH connection.\
2\. Read-only examination of production release metadata, timer status, systemd service results, Docker health, database schema version and backup/restore status.\
3\. Preparation of one new \*\*inactive\*\* release directory for the exact reviewed GitHub commit, only if all relevant prerequisites pass.\
4\. Creation of a concise, sanitised operational report and deployment plan in the local repository.\
\
I do \*\*not\*\* yet authorise activating the new release, changing service configuration, modifying the production database, restarting workers or changing backup policies.\
\
Use the existing SSH alias or established access method. Do not create credentials or change SSH configuration.\
\
If host access is unavailable due to sandbox restrictions, report the blocker and provide narrowly scoped commands for the owner to run. Do not attempt to bypass sandbox controls.\
\
\## Step 1 — Inspect the live Lightsail host\
\
Identify the actual current production state.\
\
Record:\
\
\- Ubuntu version and architecture\
\- Current deployed Git SHA at \`/opt/backtest-badger/current\`\
\- Release-directory structure and symlink target\
\- Python and uv versions\
\- PostgreSQL 17 container health\
\- Current Alembic/database schema revision\
\- Collection and scoring timer states\
\- Recent collection/scoring execution results and errors\
\- Backup and isolated restore-drill results since 16 October\
\- Storage utilisation, checkpoint count and retained recovery evidence\
\- Existing monitoring/retention timer health\
\
Pay particular attention to the previously unresolved unattended verification items:\
\
\- First unattended shared-snapshot backups\
\- First unattended fingerprint-verified restore drill\
\- Local checkpoint retention when four checkpoints accumulated\
\- Missing or failed scheduled executions\
\
A timer being enabled does not prove that the scheduled job succeeded.\
\
Use safe, read-only commands. Do not manually trigger production collection or scoring.\
\
\## Step 2 — Preserve production boundaries\
\
The existing server hosts:\
\
\- PostgreSQL 17 with persistent production volume \`backtest-badger-pg17\`\
\- Genuine forward prediction collection\
\- Genuine outcome scoring\
\- Retained research/forecast artifacts\
\- Encrypted S3 backups\
\- Isolated recovery drills\
\- Monitoring and alerting\
\
Never delete, recreate, restore over or alter the production database volume.\
\
Do not prune Docker volumes/images, delete historical checkpoints, run restic forget/prune, modify S3 lifecycle policies or reset persistent artifacts.\
\
Do not expose credentials, environment contents, private keys, private forecasts or unredacted confidential logs.\
\
Use the established operational procedures rather than inventing replacement scripts.\
\
\## Step 3 — Compare server and GitHub releases\
\
Identify what has changed between the current deployed commit and the latest reviewed GitHub commit.\
\
Summarise:\
\
\- Production-relevant Python changes\
\- Dependency or lockfile changes\
\- Alembic migration changes\
\- Forward collection/scoring code changes\
\- Systemd or deployment script changes\
\- Purely local research modules and documentation\
\- Compatibility implications for existing immutable evidence\
\
Determine whether the proposed release is compatible with the existing database schema, Python environment, workers and data.\
\
Do not assume that every new research module must execute on Lightsail.\
\
The genuine 2024 historical backtest has already been completed locally. \*\*Do not copy its private inputs/evidence to the server or rerun it there.\*\*\
\
\## Step 4 — Prepare an inactive release, if safe\
\
If the exact target commit has successful CI and the deployment compatibility checks pass, prepare it using the existing immutable release layout:\
\
\`/opt/backtest-badger/releases/\<full-commit-sha>\`\
\
Use the established \`ops/lightsail/prepare-release.sh\` procedure.\
\
Important:\
\
\- The existing preparation script expects Python 3.12.15 on Lightsail. Confirm that environment rather than assuming the local Mac's Python version applies.\
\- Require an exact, clean checkout of the reviewed commit.\
\- Preserve the existing persistent artifacts symlink.\
\- Use locked dependencies.\
\- Do not modify the existing active release in place.\
\- Do not modify the \`/opt/backtest-badger/current\` symlink.\
\- Do not restart or reload systemd.\
\- Do not run Alembic migrations against production.\
\- Do not start or stop database containers.\
\- Do not modify production data or evidence.\
\- Do not create a duplicate release if the exact candidate is already properly prepared.\
\
If preparation cannot be completed safely, stop and identify the precise issue.\
\
Do not introduce new server infrastructure, security frameworks, services or deployment automation.\
\
\## Step 5 — Prepare a concise promotion plan\
\
After inspection and any successful staging, provide an exact, minimal procedure for the subsequent D3B activation.\
\
Include:\
\
\- Current release and candidate release\
\- Reason for any necessary service interruption\
\- Preconditions, including recent successful backups\
\- Safe timer/worker pause and resume sequence\
\- Candidate compatibility and verification checks\
\- Post-promotion collection/scoring health checks\
\- Rollback conditions and the known-compatible previous release\
\- Outstanding risks requiring owner approval\
\
Do not execute the promotion in D3A.\
\
Do not automatically enable new application services, public network ports or website hosting.\
\
\## Documentation\
\
Create or update a concise operational review:\
\
\`docs/deployment/lightsail-d3a-release-reconciliation.md\`\
\
Update \`docs/deployment/production-infrastructure.md\` with clearly dated, actually observed facts if you successfully inspected the server.\
\
Distinguish verified observations from historical documentation and unverified claims.\
\
Do not rewrite historical migration reports.\
\
Archive this complete prompt verbatim at:\
\
\`prompts/deployment/003-lightsail-release-reconciliation.md\`\
\
Update \`prompts/README.md\` if appropriate.\
\
\## Boundaries\
\
\- No active production release switch\
\- No production database writes or schema migrations\
\- No manual forward collection/scoring\
\- No service restarts or timer changes\
\- No backup, restore or retention policy changes\
\- No source acquisition, modelling or historical replay\
\- No website deployment yet\
\- No changes to private secrets\
\- No unapproved AWS configuration changes\
\- No local Git commit or push\
\
Prefer a short, accurate operational report over a large new deployment framework.\
\
\## Final response\
\
State whether Lightsail is:\
\
\- HEALTHY / UP TO DATE\
\- HEALTHY / RELEASE UPDATE READY\
\- HEALTHY / UPDATE BLOCKED\
\- OPERATIONAL ISSUE DETECTED\
\- HOST ACCESS UNAVAILABLE\
\
Provide:\
\
1\. Exact current production commit\
2\. Latest reviewed GitHub commit and CI status\
3\. Production worker and database health\
4\. Latest verified backup and restore-drill observations\
5\. Relevant differences between deployed and target revisions\
6\. Whether a new release was prepared, and its exact identity\
7\. Any operational risks or blockers\
8\. Short proposed D3B promotion procedure\
9\. Files changed and checks performed\
10\. Recommended Conventional Commit message\
\
Do not claim a deployment occurred. Stop before switching the active release.
