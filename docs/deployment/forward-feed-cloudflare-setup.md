# Owner setup — Cloudflare forward feed

## Stage 5B.10 preparation — 30 October 2026

The [v2 activation record](../stage-05b10-forward-v2-production-activation.md)
supersedes the current-state summary below: v1 remains healthy; v2 publisher,
independent checker and four separate units are implemented locally, with genuine
read-only host timing measured. **V2 is not installed or published.** Gate 1 is
required for installation, private quota qualification, first publication and
new timers. Its exact proposed paths/schedules/rollback are in that record.

The intended bucket will contain the two reviewed public keys `forward-v1.json`
and `forward-v2.json`; no private artifacts. Existing bucket-scoped Object Read &
Write should cover both if its scope is confirmed unchanged. Application destination
checks are not object-scoped credentials. Do not recreate/rotate tokens or enable
r2.dev. The original completed one-key setup below remains historical recovery
context; its v1 rollback commands must not be used to disable v1 for this migration.

## Current live status — 28 October 2026

The permanent feed is active at
<https://data.backtestbadger.com/forward-v1.json>, backed by dedicated R2 bucket
`backtest-badger-forward`, intended public key `forward-v1.json`. The temporary
r2.dev endpoint now returns 401. Cloudflare provides authoritative DNS through
`brit.ns.cloudflare.com` and `weston.ns.cloudflare.com`; GoDaddy remains registrar.
The website is separately live on Workers Static Assets at
<https://www.backtestbadger.com>.

The isolated Lightsail publisher and independent HTTPS checker are both enabled
and repeatedly successful. The [Stage 5B.8 audit](../stage-05b8-post-launch-audit.md)
records exact public-vs-validated bytes, freshness, metadata, www CORS, service
results and resource measurements. The research collector/scorer and their release
remain separate. This is a dated health observation, not continuous monitoring.

Use the permanent URL for `FORWARD_PUBLIC_URL` and the website's build-time
`NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`. Credentials remain privately configured on
Lightsail; do not print environment files or share secrets in chat. No R2 settings,
credentials, services or timers were changed by the audit.

### Routine read-only verification

```sh
systemctl list-timers --all 'backtest-badger-public-feed*'
systemctl is-enabled backtest-badger-public-feed.timer backtest-badger-public-feed-check.timer
sudo journalctl -u backtest-badger-public-feed.service --since '2 hours ago' --no-pager
sudo journalctl -u backtest-badger-public-feed-check.service --since '2 hours ago' --no-pager
/opt/backtest-badger-public-feed/node/bin/node \
  /opt/backtest-badger-public-feed/web/check-forward-endpoint.cjs \
  https://data.backtestbadger.com/forward-v1.json \
  /var/lib/backtest-badger-public-feed/last-success.json
```

Run these on the authorised host (`ssh Ubuntu-1`). A publication crossing the exact
byte comparison can require another read after the natural cycle completes; do not
trigger an export merely to make the comparison pass. Monitor approaching 90-second
wall time / 384 MiB RSS, repeated rejections, stale cutoff and missed issuance.
Systemd logs/checks do not establish external notification delivery.

## Original setup procedure — completed, retained for recovery

The steps below document the original Stage 5B.5 setup, including its temporary
r2.dev acceptance route. They are **not pending activation tasks**. Do not recreate
resources, re-enable the retired development endpoint or rerun write commands as
part of routine verification. Any recovery/configuration action needs separate
authorisation. The [historical activation report](../stage-05b5-forward-feed-activation.md)
retains the original observations and limits.

## 1. Review R2 usage and create the dedicated bucket

1. Sign in at [Cloudflare Dashboard](https://dash.cloudflare.com/) and select the
   account intended for Backtest Badger. Complete MFA yourself.
2. Open **Storage & databases → R2 Object Storage**. Review current account storage
   and operation usage, including any existing private backup bucket. If R2 needs
   activation, complete its official billing/setup interface yourself; choose
   Standard usage within the free allowance, and do not upgrade the account plan.
   Stop if projected account totals exceed the free allowance.
3. This feed adds one object, at most 64 KiB, about 4,320 monthly PUTs and 8,640
   automated reads at a ten-minute cadence. Browser polling adds about 8,640 reads
   per continuously visible tab per 30 days. Public traffic is not a hard-capped
   quantity; review actual usage after activation. Check the current
   [R2 pricing](https://developers.cloudflare.com/r2/pricing/).
4. Select **Create bucket**, name it exactly **`backtest-badger-forward`**, choose
   **Standard** storage and automatic location/default jurisdiction. The installed
   publisher uses the default-jurisdiction S3 endpoint. Do not enable Infrequent
   Access, data catalog features or a paid add-on.
5. Keep this bucket dedicated to the single key **`forward-v1.json`**. Do not upload
   raw evidence, archives, folders, backups, helper code or earlier snapshots.

## 2. Create the narrowly scoped publishing credential

1. In the R2 overview, find **Account Details → API Tokens → Manage**.
2. Create a dedicated R2 Account API token (or an R2 User API token if the account
   interface does not permit account tokens). Name it `backtest-badger-forward-publisher`.
3. Select **Object Read & Write**, then **Apply to specific buckets only**, and
   select **only `backtest-badger-forward`**. Do not select Admin Read & Write,
   All buckets or the private backup bucket.
4. Create the token and securely save its **Access Key ID**, **Secret Access Key**
   and the account ID. The secret is shown once. Use the S3 access-key pair, not a
   Cloudflare account-wide REST token. Do not paste any secret into chat.
5. The provider's object role includes object read/write/list within that bucket.
   The helper itself performs only PUT/GET of `forward-v1.json`. The role cannot
   administer buckets or access other buckets. See [R2 token scopes](https://developers.cloudflare.com/r2/api/tokens/).

In your terminal, connect with `ssh Ubuntu-1`, then use the editor so values do
not enter shell history or command-line arguments:

```sh
sudoedit /etc/backtest-badger-public-feed/publisher.env
```

Enter these three variables with your actual values, with no extra spaces or
placeholder brackets:

```text
R2_ACCOUNT_ID=your_32_character_cloudflare_account_id
R2_ACCESS_KEY_ID=your_dedicated_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_dedicated_r2_secret_access_key
```

Save, then restrict permissions without displaying the file:

```sh
sudo chown root:root /etc/backtest-badger-public-feed/publisher.env
sudo chmod 600 /etc/backtest-badger-public-feed/publisher.env
```

The directory already has root ownership and mode 0700. The service reads this
file through systemd; do not source it in an interactive shell or export it into
the research environment. Keep the credential in your password manager for
revocation/recovery. No Cloudflare admin credential belongs on Lightsail.

## 3. Prepare CORS and the initial public URL

In **R2 → backtest-badger-forward → Settings → CORS Policy**, paste the contents of
[`ops/public-feed/cors.json`](../../ops/public-feed/cors.json):

```json
[
  {
    "AllowedOrigins": [
      "https://www.backtestbadger.com",
      "http://127.0.0.1:3000",
      "http://127.0.0.1:8787"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "ExposeHeaders": ["ETag", "Last-Modified", "Cache-Control"],
    "MaxAgeSeconds": 600
  }
]
```

Do not add wildcard credentials, PUT browser access or extra origins. If the
interface requires the first object before accepting CORS, perform the one-off
upload in step 4, then apply this policy before opening the website.

During the original setup, GoDaddy still served authoritative DNS, so the temporary
route used **Settings → Public Development URL → Enable** for initial local testing. Read and confirm the public
access notice yourself. Record the generated `https://pub-….r2.dev` hostname and
append `/forward-v1.json`. This makes the only intended object public to anyone;
CORS does not restrict direct downloads. The development endpoint is rate-limited
and is not the permanent production endpoint. Do not add a CNAME pointing to it.
[Cloudflare public-bucket guidance](https://developers.cloudflare.com/r2/buckets/public-buckets/).

## 4. Publish one fresh candidate, then verify

On Lightsail, create the public checker's environment file:

```sh
sudoedit /etc/backtest-badger-public-feed/endpoint.env
```

It contains only the actual public URL (not a credential):

```text
FORWARD_PUBLIC_URL=https://pub-YOUR-ACTUAL-HOST.r2.dev/forward-v1.json
```

Then:

```sh
sudo chown root:root /etc/backtest-badger-public-feed/endpoint.env
sudo chmod 600 /etc/backtest-badger-public-feed/endpoint.env
sudo systemctl start backtest-badger-public-feed.service
sudo systemctl status backtest-badger-public-feed.service --no-pager
sudo journalctl -u backtest-badger-public-feed.service -n 12 --no-pager
sudo systemctl start backtest-badger-public-feed-check.service
sudo journalctl -u backtest-badger-public-feed-check.service -n 8 --no-pager
```

A successful oneshot normally becomes `inactive (dead)` with `Result=success` and
exit status 0. The public checker should report `public-feed-healthy`, cutoff,
generation and SHA-256. If either command fails, keep the timers disabled and
inspect the fixed diagnostic category. Do not upload an unvalidated file manually.
The old review candidate must not be used as a fresh live snapshot.

For exact local-vs-public bytes, still on Lightsail, set `feed_url` to your public
URL (safe to enter in shell history), then run:

```sh
feed_url='https://pub-YOUR-ACTUAL-HOST.r2.dev/forward-v1.json'
/opt/backtest-badger-public-feed/node/bin/node \
  /opt/backtest-badger-public-feed/web/check-forward-endpoint.cjs \
  "$feed_url" /var/lib/backtest-badger-public-feed/last-success.json
```

This checks exact bytes, full schema, both markets, freshness, content type, cache
policy and www CORS. The publisher already checked the S3 object bytes. You can
share **this public URL** and the check result with Codex for browser verification;
do not share the credential file or token.

Before scheduling, also verify publicly:

```sh
curl --fail --silent --show-error --head "$feed_url"
curl --fail --silent --show-error --head \
  -H 'Origin: http://127.0.0.1:3000' "$feed_url"
curl --fail --silent --show-error --head \
  -H 'Origin: http://127.0.0.1:8787' "$feed_url"
curl --silent --show-error --head \
  -H 'Origin: https://unapproved.example' "$feed_url"
```

Expect 200, JSON content type and `public, max-age=60, must-revalidate`. Allowed
origins should receive their matching `Access-Control-Allow-Origin`; the unapproved
origin should not. A 200 to an unapproved origin is expected because the object is
public. Check the bucket root and guessed keys such as `/private.json`, `/.env`,
`/previous-success.json` and `/forward-predictions/`; none should expose files or a
listing. In the dashboard, confirm the bucket contains only `forward-v1.json`.

## 5. Enable and observe two publication cycles

Only after the checks above succeed:

```sh
sudo systemctl enable --now backtest-badger-public-feed.timer
sudo systemctl enable --now backtest-badger-public-feed-check.timer
systemctl list-timers --all 'backtest-badger-public-feed*'
```

The publisher runs at minutes 03/13/23/33/43/53 UTC, checker three minutes later.
Observe at least two successive scheduled runs. Compare actual public bytes/hash,
`as_of` and `generated_at` after each. The clocks should advance; original issuance
and target times should remain identical until the existing research system issues
new forecasts. The latest status changes only when the saved outcome is scored or
another genuine forecast is issued. Do not invent a transition for this check.

Review the journal's CPU/RSS/wall time and both unit results. If the source changes
during export, a rejected candidate is expected to preserve the prior snapshot;
retry happens at the next tick. Repeated rejection or stale publication needs
investigation. There is no catch-up burst or automatic restart loop.

## 6. Connect the local Burrow

On the Mac, edit the ignored `web/.env.local` without overwriting any unrelated
settings. Add only this public build-time variable using the verified URL:

```text
NEXT_PUBLIC_FORWARD_SNAPSHOT_URL=https://pub-YOUR-ACTUAL-HOST.r2.dev/forward-v1.json
```

Restart `pnpm dev`. From `web/`, run the production checks and local preview:

```sh
pnpm lint
pnpm typecheck
pnpm format:check
pnpm build
pnpm test
pnpm test:workers
pnpm preview
```

Use Node 24.22.1 and pnpm 11.25.0 as in the frontend README. Inspect both
`http://127.0.0.1:3000/burrow/` and `http://127.0.0.1:8787/burrow/`. Confirm BTC/ETH,
UTC timestamps, current targets, pending versus scored values, all cohorts, matched
counts and undefined statistics. Check refresh and network failure without
substituting fixtures. Binance must remain the market chart's independent source.
This is **local review**, not a deployed Workers website.

## 7. Permanent data hostname migration reference (completed)

Cloudflare requires the R2 custom hostname's zone in the same account. A partial
CNAME zone is a Business/Enterprise feature, so it is not the Free-plan route.
[Partial DNS setup](https://developers.cloudflare.com/dns/zone-setups/partial-setup/).

1. In Cloudflare, add `backtestbadger.com` as a website/zone with the **Free** plan.
   Adding a pending zone does not itself change GoDaddy's authoritative nameservers.
2. Export the **complete** GoDaddy DNS record set. Compare it with Cloudflare's
   imported/quick-scanned records: names, types, values, priorities, TTLs and
   especially all mail, SPF/DKIM/DMARC, validation, wildcard and delegated records.
   Quick scan/public DNS queries are not a complete inventory. Preserve existing
   website/mail routing; use DNS-only for existing website records during this
   data-feed setup. Do not activate a Workers www/apex route.
3. Record the **two actual Cloudflare nameservers assigned to this zone** and
   inventory DNSSEC/DS settings. Do not guess nameservers or switch with an old
   incompatible DS record still installed.
4. Stop before registrar cutover and review the complete record comparison and
   DNSSEC procedure. The exact later GoDaddy action is **Domain → DNS → Nameservers
   → Change → use your own nameservers**, replacing `ns23.domaincontrol.com` and
   `ns24.domaincontrol.com` with the two values from this zone. That entire-domain
   change remained a separate owner decision at the original preparation stage.
5. Once the zone is active and existing website/mail resolution has been verified,
   open **R2 → backtest-badger-forward → Settings → Custom Domains → Add** and enter
   `data.backtestbadger.com`. Review the dedicated DNS record before connecting it.
   Wait until the custom domain is Active with HTTPS.
6. Verify `https://data.backtestbadger.com/forward-v1.json` with the same hash/schema,
   cache and CORS checks. Do not configure Cache Everything for this JSON. Keep any
   later edge cache TTL at most 60 seconds and handle CORS cache variation correctly.
7. Change the checker's public URL and local build variable to the verified custom
   hostname; restart/rebuild locally. Disable **Public Development URL** on the
   bucket and confirm the old r2.dev route no longer serves data. Remove loopback
   CORS origins after local acceptance; keep www.

## Rollback commands — separate production authorisation required

Disable only the new publication timer:

```sh
sudo systemctl disable --now backtest-badger-public-feed.timer
# If cancellation is necessary, stop only the new oneshot:
sudo systemctl stop backtest-badger-public-feed.service
# Optional when retiring the feed entirely:
sudo systemctl disable --now backtest-badger-public-feed-check.timer
```

In Cloudflare, revoke only the dedicated publisher token and disable the bucket's
public development URL **and** custom-domain access as needed. Verify public
access actually fails. Do not touch private backups or research services.

To restore prior approved bytes, first stop publication, then validate the private
backup (no re-export or timestamp change):

```sh
/opt/backtest-badger-public-feed/node/bin/node \
  /opt/backtest-badger-public-feed/web/validator.cjs \
  /var/lib/backtest-badger-public-feed/previous-success.json
```

If the credential is still valid, upload those exact bytes in a transient,
bounded unit whose environment is loaded privately by systemd:

```sh
sudo systemd-run --wait --collect --unit=backtest-badger-public-feed-restore \
  -p Type=oneshot -p User=ubuntu -p Group=ubuntu -p UMask=0077 \
  -p EnvironmentFile=/etc/backtest-badger-public-feed/publisher.env \
  -p TimeoutStartSec=40 -p MemoryMax=256M -p Nice=10 \
  -p NoNewPrivileges=true -p ProtectSystem=strict -p ProtectHome=true \
  /opt/backtest-badger-public-feed/.venv/bin/python \
  /opt/backtest-badger-public-feed/web/scripts/publish_forward_r2.py \
  /var/lib/backtest-badger-public-feed/previous-success.json
```

Verify downloaded bytes against that backup afterward. The freshness checker may
correctly fail because the restored timestamps are old. Re-enable publication only
after the underlying problem is resolved. If the credential was revoked, provision
a new equally scoped credential before any restoration. Do not restore or alter raw
scientific evidence. Activation has occurred; validate the retained prior snapshot
and its original clocks before any separately authorised rollback.

To disconnect the local website, remove only `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL`
from `web/.env.local`, restart dev and rebuild static output.
