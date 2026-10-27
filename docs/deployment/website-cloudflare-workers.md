# Website launch — Cloudflare Workers Static Assets

Prepared 26 October 2026. **Runbook only: no Cloudflare project, remote preview,
deployment, DNS change or registrar change was made.** Target:
<https://www.backtestbadger.com>. GoDaddy remains the registrar. Local validation
and editorial findings are in the [Stage 5B.2 report](../stage-05b2-history-and-launch-readiness.md).

## Local build and review

Use Node **24.22.1** (`web/.node-version`), pnpm **11.25.0** (packageManager),
and local Wrangler **4.153.0** (exact dev dependency and lockfile). Wrangler's
published engine requirement is Node >=22; the frontend requires >=22.13.
Run from the full repository checkout, not a copy of `web/` alone:

```sh
cd web
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm format:check
pnpm build
pnpm test
pnpm test:export
pnpm test:workers
pnpm preview
```

The last command is **local only**, `wrangler dev --local --ip 127.0.0.1 --port 8787`.
Open <http://127.0.0.1:8787>. The smoke test uses port 8791 and stops its own
local process. No login, token or Cloudflare account is needed. Optional live
Binance verification: `node --import tsx scripts/check-market-live.ts`.

`next build --webpack` exports static files to `web/out/`. The post-build script
removes reserved not-found editorial placeholders and the maintainer asset README.
`wrangler.jsonc` names `backtest-badger-web`, uses compatibility date `2026-10-26`,
and serves `./out` with `auto-trailing-slash` and `404-page`. There is no `main`,
binding, application server, SPA fallback or Next.js server adapter.
Folder indexes redirect to trailing slashes; unknown URLs use `out/404.html`
with HTTP 404. See Cloudflare's [SSG configuration](https://developers.cloudflare.com/workers/static-assets/routing/static-site-generation/).

Review all six primary routes, approved nested articles, direct reloads, fonts,
mascot and licence assets; both markets, all six ranges, chart modes and errors;
and narrow mobile/desktop layouts. Stage 5B.3 approves **four notes and three
guides** by exact source hash; all seven nested routes must return 200, while
unknown/unapproved and publication-pending routes must return genuine 404s.
Keep the forward snapshot URL unset until a genuine
public snapshot is separately reviewed. No website build needs Lightsail access.

## Release workflow: one build system, explicit promotion

**Recommendation:** GitHub Actions verifies commits; Workers Builds uploads
candidates; the owner promotes an exact candidate only after both Actions workflows
are green for that commit. There is no GitHub deployment workflow or automatic
production promotion. This is simple for an initial owner-operated release and
avoids a race between Cloudflare's push trigger and GitHub CI.

Workers Builds normally deploys as soon as its build finishes; it does **not**
wait for independent GitHub checks. Replace its default deploy command with
`pnpm exec wrangler versions upload` **before enabling automatic builds**.
This is still a remote upload and may immediately expose a public Version URL;
it requires separate authorisation. It does not change the active production
version. [Build configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)
distinguishes production and preview commands.

Protect `main` with required `CI / test` and `Frontend / frontend` checks, review,
and no force pushes. Verify the actual check names in GitHub after the first run.
Branch protection helps before merge; the release gate still checks the **exact
post-merge SHA**, since a new merge commit can differ from the PR head. A manual
promotion can bypass this procedure, so restrict deploy access to the owner and
record the check URLs, SHA, version ID and approval with every release. This is
an explicit operational gate, not a claim that Cloudflare enforces GitHub status.

A future Actions deployment job could enforce check dependencies and protected
GitHub environment approval, but would need secret handling and cross-workflow
coordination. Do not add it alongside this process. Reconsider only if manual
promotion becomes burdensome.

### Exact Workers Builds settings (after authorisation)

| Setting | Value |
| --- | --- |
| Repository | `owencrew/backtest-badger` via Cloudflare's GitHub integration |
| Worker/config name | `backtest-badger-web` |
| Production branch | `main` |
| Root directory | `web` |
| Node | `NODE_VERSION=24.22.1`; also pinned in `.node-version` |
| pnpm | `PNPM_VERSION=11.25.0`; also `packageManager: pnpm@11.25.0` |
| Automatic dependency installation | `SKIP_DEPENDENCY_INSTALL=1` |
| Build command | `pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm format:check && pnpm build && pnpm test && pnpm test:workers` |
| Deploy command | `pnpm exec wrangler versions upload` — upload only |
| Preview command | `pnpm exec wrangler versions upload` — same candidate/version workflow |
| Static asset directory | `./out`, resolved from `web/wrangler.jsonc` |
| Watch includes | `web/*`, `docs/*`, `.github/workflows/*` |
| Watch excludes | None |
| Build variables | `NEXT_TELEMETRY_DISABLED=1`, `WRANGLER_SEND_METRICS=false` |
| Search indexing | Leave `BADGER_SEARCH_INDEXING` unset for the initial candidate and all previews |
| Forward snapshot | Leave `NEXT_PUBLIC_FORWARD_SNAPSHOT_URL` unset |

There is no assumed separate “install command” setting: disabling automatic
installation and putting the frozen install in the build command makes it explicit.
The [build image documentation](https://developers.cloudflare.com/workers/ci-cd/builds/build-image/)
confirms the version overrides and custom-install mechanism. Preview builds should
be limited to trusted owner branches; do not run unreviewed contributor code with
deployment credentials. Start with previews disabled and enable deliberately.

Cloudflare's [monorepo root setting](https://developers.cloudflare.com/workers/ci-cd/builds/advanced-setups/)
sets the command working directory, not a separate repository containing only
that folder. The sibling `../docs/field-notes/` loader therefore stays unchanged.
A local build from `web/` in the full checkout passed. **The hosted build has not
been executed**; inspect the first authorised build log for the sibling directory
and publication checks before promotion. Do not upload private artifacts or copy
the research tree into `public/`. `docs/*` watch coverage includes source reports
used by frontend tests. [Watch paths](https://developers.cloudflare.com/workers/ci-cd/builds/build-watch-paths/)
are repository-relative.

The Free plan supports this assets-only setup: [static asset requests and storage](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/)
are free, and [Workers Builds](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/)
currently includes 3,000 build minutes/month, one concurrent build and a 20-minute
build timeout. No paid features, SSR or Worker execution are required. Monitor the
free build quota rather than enabling a paid plan.

## First deployment and later promotion

1. Owner signs in to or creates a Cloudflare account, with MFA, and selects the
   Free plan. Review content approvals, artwork rights and the DNS inventory first.
2. Reverify the [seven approved article identities](../stage-05b3-editorial-publication.md)
   and their linked reports. All four notes and three guides are approved for the
   initial release; any later source edit needs deliberate review and a new exact
   hash. Rebuild and inspect the production export. Keep indexing disabled on the
   initial workers.dev release; page-specific canonical URLs already use www.
   Resolve the original engraving's distribution rights before public deployment.
3. Obtain a clean, reviewed commit on GitHub and verify **both workflows green for
   that exact SHA**. The starting baseline's green run is not approval of new code.
   Review the local Wrangler production export and record the SHA and build output.
4. **Initial bootstrap needs explicit deployment approval.** Installed Wrangler
   4.153.0 refuses `versions upload` for a Worker that does not yet exist. Do not
   treat account/project creation or an initial deployment as a harmless preview.
   After approval, the owner may run `pnpm exec wrangler deploy` from `web/` at the
   verified SHA, with no Custom Domain configured. This creates the Worker and
   immediately serves the website on its workers.dev hostname. It is a public
   release, even before www is connected. Test it from an external network.
5. Connect the existing Worker to GitHub and enter the candidate-only settings
   above before enabling builds. If the connection wizard insists on an immediate
   deployment with its default command, stop and use Settings > Build on the
   existing Worker; do not accept an unchecked default deployment.
6. For later changes, review the Workers Builds candidate and record its version
   ID, build SHA and Version URL. Confirm the same SHA has green Python and frontend
   CI, then obtain owner release approval. Select that **exact version** in
   Deployments and promote it to 100%, or use
   `pnpm exec wrangler versions deploy <VERSION_ID>@100%`. This changes production
   immediately. Never promote “latest” without matching its SHA.
7. [Version URLs](https://developers.cloudflare.com/workers/versions-and-deployments/version-urls/)
   can be public as soon as a version is uploaded. They must always use production
   publication gates; development draft mode is never uploaded. Local `pnpm preview`
   is unrelated to the remote `wrangler preview` command. The latter is not used
   by this runbook's selected candidate workflow.

No command in steps 4–7 was executed during Stage 5B.2. The distinction between
[versions and active deployments](https://developers.cloudflare.com/workers/versions-and-deployments/)
is central to this release gate.

## GoDaddy → Cloudflare DNS, then www

**Separate owner authorisation is required before each DNS cutover or activation.**
No current DNS inventory was fetched or inferred in this stage.

1. Export the existing authoritative zone and retain its nameservers and TTLs.
   Inventory every active service with the owner: apex/subdomain A, AAAA and
   CNAME; MX priorities and targets; TXT verification tokens; SPF; every DKIM
   selector; `_dmarc`; CAA, SRV, subdomain NS delegations and any other records.
   The provider's zone export is essential: public DNS queries cannot enumerate
   unknown DKIM selectors or all subdomains. Note mail/FTP/autodiscovery hosts
   and any provider-specific forwarding services that are not DNS records.
2. Add **backtestbadger.com** to Cloudflare as a full DNS zone on Free. Compare
   the imported records field by field with the source inventory; the automatic
   scan is not a complete backup. Preserve names, values, priorities and TTLs.
   Keep mail/service records DNS-only unless their provider explicitly supports
   proxying. Do not delete, infer or replace unknown records. Flag conflicts at
   `www` and the apex for a separately approved replacement plan.
3. Check DNSSEC/DS status. If active, follow the documented migration procedure
   to disable old DNSSEC at the registrar and wait for the old DS to disappear
   before changing nameservers. Record the rollback implications. Follow
   [Cloudflare full setup](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/).
4. Only after reconciliation and approval, in GoDaddy Domain Portfolio select
   the domain → DNS → Nameservers → use your own nameservers. Enter **only the
   exact pair assigned to this Cloudflare zone**, then save/verify identity.
   Keep GoDaddy registration, renewal and ownership unchanged. Follow
   [GoDaddy's nameserver instructions](https://www.godaddy.com/help/change-my-domain-nameservers-664).
5. Wait for Cloudflare to show the zone Active. Compare authoritative answers
   and at least two recursive resolvers with the inventory, checking A/AAAA,
   CNAME, MX, TXT, SPF, DKIM, DMARC, CAA and service subdomains. Test mail receipt
   and sending, verification-dependent services and existing websites. Once
   stable, enable Cloudflare DNSSEC and add its new DS at GoDaddy; verify it.
6. With the approved Worker serving correctly, select Workers & Pages →
   `backtest-badger-web` → Settings → Domains & Routes → Add → Custom Domain →
   **www.backtestbadger.com**. This activates routing; Cloudflare creates DNS and
   managed certificates. An existing CNAME blocks Custom Domain creation: resolve
   it only under the reviewed replacement plan. Confirm certificate issuance and
   HTTPS. [Workers Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)
   require an active Cloudflare zone; external GoDaddy DNS plus a Pages-style
   CNAME does not satisfy that requirement. Do not route through Lightsail.
7. After confirming the apex has no service that would be displaced, use a
   Cloudflare Single Redirect: match `http.host eq "backtestbadger.com"`, target
   `concat("https://www.backtestbadger.com", http.request.uri.path)`, status 301,
   preserve query string. This covers HTTP and HTTPS without matching www.
   The apex must have a proxied DNS record so the rule runs. Only if approved as
   an originless redirect hostname, create the documented placeholder A record
   `@ → 192.0.2.1`, proxied. Do not overwrite an active record blindly or change
   MX/TXT records. See [originless redirects](https://developers.cloudflare.com/fundamentals/manage-domains/redirect-domain/).
8. Check HTTPS at apex and www, HTTP→HTTPS behaviour, paths and query strings,
   no redirect loops, genuine 404s and certificate validity. Ensure HTTP www
   redirects to HTTPS using the zone's reviewed HTTPS setting; assess other
   existing services before changing a zone-wide setting.

Useful read-only checks **during the separately authorised migration**:

```sh
dig NS backtestbadger.com @1.1.1.1
dig NS backtestbadger.com @8.8.8.8
dig MX backtestbadger.com
dig TXT backtestbadger.com
dig TXT _dmarc.backtestbadger.com
dig DS backtestbadger.com
curl -I 'https://www.backtestbadger.com/burrow/'
curl -I 'http://backtestbadger.com/burrow/?check=1'
curl -I 'https://backtestbadger.com/burrow/?check=1'
curl -I 'https://www.backtestbadger.com/does-not-exist/'
```

Query each known DKIM selector and service host from the inventory as well. Compare
proxy-enabled web records by intended routing, not by expecting their original IP
in recursive answers. Keep the old zone intact through propagation and verification.

## Release checklist and rollback

Before announcing launch, test from an external network on desktop and mobile:
all main/approved article routes and refreshes; mascot/fonts; BTC/ETH 1D, 7D, 30D,
90D, 1Y, ALL; weekly boundary explanation; UTC tooltips; keyboard slider; line and
candlestick modes; pan/zoom/reset; truthful unavailable forecasts; genuine 404s;
www HTTPS and apex redirect with path/query preservation. Binance regional
restrictions must produce the honest error state, never fabricated prices.

Record the production version ID and commit SHA. For subsequent failure, owner
approval to roll back authorises an **immediate production change**: select the
known-good version in Deployments → Rollback, or run
`pnpm exec wrangler rollback <KNOWN_GOOD_VERSION_ID>`. Recheck the public website.
[Rollback](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/)
restores that version's assets/code but does not reverse DNS, Custom Domains or
external resources. Keep this assets-only site free of storage migrations.

The first-ever deployment has no prior good website version: if it fails, do not
attach www or announce launch. Disable the public workers.dev exposure if needed,
then fix and reverify. For DNS trouble, compare the preserved inventory and correct
the specific discrepancy with authorisation; nameserver rollback is slower, must
coordinate DNSSEC/DS and is not a substitute for a Worker version rollback.

## Search activation after the www launch

Stage 5B.3 prepares search metadata; it does **not** authorise indexing. All public
pages use page-specific `https://www.backtestbadger.com` canonical and Open Graph
URLs. Original article dates are retained without declaring a public publication
date. No social artwork was added; the engraving rights decision is still open.

For initial workers.dev and every preview/version review build, leave
`BADGER_SEARCH_INDEXING` unset. Exported HTML must contain `noindex, nofollow`.
`robots.txt` intentionally says `Allow: /`: blocking crawling would prevent robots
from reading HTML noindex. No sitemap is advertised and static preparation removes
`out/sitemap.xml`. This is a discovery policy, not private access control.

After www HTTPS, routing, content and external checks pass, obtain explicit owner
approval to enable indexing. Only for that www release, set the build-time variable
`BADGER_SEARCH_INDEXING=www-live-owner-approved`, then rebuild and run all frontend
checks in the same environment. Any other value stays noindex. The sitemap includes
six existing primary pages plus exact eligible article routes; it omits fabricated
last-modified dates. Future approvals update the list through the production gate.

Inspect the actual files before uploading:

```sh
rg -o '<title>[^<]*|<link rel="canonical"[^>]*|<meta (name|property)="(robots|description|og:[^"]+|twitter:[^"]+)"[^>]*' out/index.html out/field-notes/*/index.html out/field-guide/*/index.html
cat out/robots.txt
# Candidate: this file must be absent. Approved www build: inspect every <loc>.
ls out/sitemap.xml
```

A runtime variable or DNS change cannot alter static metadata. An indexing-enabled
asset bundle must not be served on workers.dev or public Version URLs: before
promoting it, separately authorise disabling those alternate public exposures (or
access-restrict them) and verify that only www can serve the enabled bundle.
Keep preview build configuration unset; do not globally enable the variable for
all branches. If candidate URLs cannot be isolated, retain noindex until the owner
resolves that hosting decision. No dynamic Worker is needed for metadata.

After exact-SHA green Python and Frontend Actions, reviewed output and explicit
release approval, deploy the intended version using the existing procedure. Check
www HTML, robots.txt and sitemap.xml externally, then submit the www sitemap to
search engines if desired. To reverse indexing, rebuild without the variable and
promote that verified version under owner approval; do not merely change a runtime
setting. Search engine processing is not immediate or guaranteed.
