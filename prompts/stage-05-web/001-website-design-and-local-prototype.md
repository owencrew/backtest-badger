# Backtest Badger — Stage 5A: Website Design and Local Prototype

## Objective

Design and implement the first polished, locally runnable website prototype for Backtest Badger.

**Product:** Backtest Badger

**Tagline:** A little badger. A lot of backtests.

Create a distinctive, professional quantitative research platform with memorable personality, trustworthy analysis and thoughtful interaction design.

The target audience includes curious investors, quantitative researchers, developers, and hiring managers.

The website should demonstrate high-quality engineering, rigorous research, scientific transparency, excellent data visualisation, and the ability to explain difficult concepts clearly.

This stage is a **local website prototype**, not a production deployment.

Prioritise creating a genuinely attractive and functional website, not another lengthy planning exercise.

## Starting context

Read:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/development-handoff.md`
- `docs/stage-04b2e5g-first-genuine-historical-backtest.md`
- `docs/field-notes/README.md`
- Relevant existing Field Notes and research reports

Understand the distinction between completed historical backtests, genuine prospective forecasts, scored outcomes, future paper trading, and real-money trading.

Lightsail is operating on release:

`cceb6509edbb6e6a9fb577c112bf9c648e81c5a1`

This stage must not access or modify Lightsail.

## 1. Product and visual identity

The website should combine three visual influences:

1. A premium financial research terminal.
2. A beautifully designed technical/editorial publication.
3. A distinctive woodland/badger identity.

The result should feel intelligent, approachable, memorable and trustworthy.

Avoid generic crypto exchange visuals, excessive neon colours, decorative gradients, dashboard clutter and overly playful cartoon aesthetics.

### Colour palette

Use the following starting values, refining them slightly where necessary for contrast or visual quality:

| Role | Starting colour | Token |
| --- | --- | --- |
| Main background | `#121615` | `--color-bg` |
| Card surface | `#1D2522` | `--color-surface` |
| Raised surface | `#26312B` | `--color-surface-raised` |
| Main text | `#F4F1EA` | `--color-text` |
| Secondary text | `#AEB9B1` | `--color-text-muted` |
| Primary accent | `#315943` | `--color-primary` |
| Bright green text/accent | `#A9CFAE` | `--color-primary-light` |
| Sand/beige | `#D8C7A5` | `--color-sand` |
| Slate grey | `#82908D` | `--color-slate` |
| Borders | `#37463E` | `--color-border` |
| Negative metrics | `#E4A19A` | `--color-negative` |
| Positive metrics | `#A9CFAE` | `--color-positive` |

The primary accent should remain forest green, not neon or mint.

Use warm beige as a complementary editorial accent, including illustration treatments, certain labels and occasional featured panels.

Ensure interactive controls and text have appropriate accessibility contrast. Do not place dark forest-green text directly on near-black if it is too low contrast.

Use semantic tokens, rather than scattering colour literals throughout components.

### Typography

Use a polished modern sans-serif font for headings, navigation, body copy, brand messaging and editorial writing.

Use monospace sparingly for:

- Prices and percentage metrics
- Dates and timestamps
- Model identifiers and code-like labels
- Logs and technical readouts
- Compact data tables where aligned numbers improve readability

The overall experience should be predominantly clean sans-serif with technically credible monospace details.

Use tabular numerals for financial metrics.

Avoid decorative serif typography and excessive changes of font family.

## 2. Mascot and illustration system

Use the owner-provided image at:

`design-assets/badger-reference.png`

This is the primary reference for the Backtest Badger mascot.

The image depicts a classic black-and-white woodcut/engraving-style badger digging into the ground.

Preserve the recognisable badger character, bold ink treatment and slightly vintage natural-history aesthetic.

Develop a small family of useful adaptations:

**Hero variation:** A prominent badger illustration integrated into the homepage hero.

**Transparent variation:** A carefully adapted version suitable for charcoal, beige or forest-green backgrounds without an awkward white rectangle.

**Brand mark:** A simplified emblem or badger-head treatment suitable for compact navigation and social/brand contexts.

**Favicon:** A recognisable small-format symbol; simplify if the full woodcut loses definition.

**Animation-ready variation:** A restrained silhouette or small badge that could eventually move along a chart or animate while research runs.

Prefer reusing and transforming the provided artwork over inventing an unrelated badger character.

Create only the variations that can be produced cleanly with available tools. Preserve the original reference, keep derived assets organised, and avoid claiming an independently drawn illustration was created if it was only a processed version of the original.

If an accurate transparent/vector derivation is impractical, retain the artwork in a tasteful warm-sand illustration panel rather than using a poor-quality automatic conversion.

The mascot should be memorable but should never obscure critical analytical information.

## 3. Site navigation and information architecture

Build six main destinations:

- Home
- The Burrow
- The Dig
- Field Notes
- The Field Guide
- About / Methodology

The desktop navigation should prominently feature the brand mark and sections.

Mobile navigation should be simple, usable by keyboard and touch, and visually consistent with desktop.

Do not add empty navigation destinations that imply implemented features that do not exist.

Provide appropriate breadcrumbs, section headings, active navigation states and a cohesive footer.

## 4. Homepage — page design

The homepage should immediately communicate both personality and scientific credibility.

Suggested opening headline:

**Dig into the evidence.**

Official tagline beneath it:

**A little badger. A lot of backtests.**

You may improve the marketing headline if you find a stronger alternative, but preserve the official tagline.

### Homepage wireframe

**A. Navigation**

Compact badger mark, Backtest Badger wordmark, primary navigation and optional GitHub link.

**B. Hero**

Two-column desktop layout:

Left side:

- Short quantitative-research eyebrow
- Large, confident headline
- Official tagline
- Concise explanation of the research platform
- Primary action: Explore The Dig
- Secondary action: Read Field Notes

Right side:

- Large adapted badger illustration
- Subtle visual framing in sand/charcoal/forest green
- Optional restrained decorative chart motif, clearly nonfinancial

Stack elegantly on mobile.

**C. Featured research**

Show the real 2024 Ridge Sign backtest compared with independently funded Cash and Buy & Hold.

Use transparent research labels and source links.

Example verified BTC figures:

- Ridge: −60.69%
- Cash: 0.00%
- Buy & Hold: +120.81%

Identify these as historical simulations rather than realised or live trading returns.

**D. How Backtest Badger works**

A concise visual journey:

Market data → Predictive models → Backtesting → Evaluation

Explain that forward forecasts and historical simulations are separate evidence streams.

**E. Explore the platform**

Featured cards linking to The Burrow, The Dig, Field Notes and The Field Guide.

**F. Featured discoveries**

Feature genuine research articles such as:

- The Price of Changing Your Mind
- One Minute Can Change a Backtest

These are currently drafts. Use a clearly labelled local editorial preview, not an implied public publication.

**G. Learn the fundamentals**

A few educational cards linking to introductory Field Guide content.

**H. Footer**

About, methodology, open-source repository, limitations and appropriate research disclaimers.

The homepage must not feel like a long generic landing-page template. Use balanced spacing, restrained motion, excellent typography and interesting editorial composition.

## 5. The Burrow — forward research dashboard

The Burrow is the place to understand Backtest Badger's current research activity.

Eventually it will include richer prospective performance and paper-portfolio information.

For the initial prototype, design sections for:

- Market and model overview
- Forward forecast activity
- Scored versus pending observations
- Forecast accuracy summaries
- Timely versus late observation cohorts
- Recent research-system activity
- Clear links to methodology

Use only verified, public-safe figures available locally.

If current statistics have not been exported and reviewed for publication, show a clearly labelled preview, empty state or example of the component layout.

Never fabricate actual forecast counts, error metrics, model rankings, live updates or paper-trading returns.

A static snapshot must have an explicit **as-of date** and should never be labelled live unless it genuinely updates from a verified feed.

Do not connect directly to production PostgreSQL or private production artifacts.

## 6. The Dig — historical backtest research

The Dig should be one of the strongest visual sections of the website.

It is where readers examine strategies, performance, benchmarks and methodology.

Initial dataset: the genuine 2024 BTCUSDT and ETHUSDT native-minute historical backtest.

Include:

- Market selection
- Strategy and benchmark comparison
- Clearly labelled cumulative return metrics
- Final portfolio values
- Independent initial capital
- Maximum observed drawdown
- Trade counts and turnover
- Transaction cost explanation
- Research methodology
- Limitations and evidence provenance
- Links to related Field Notes

Verified rounded cumulative returns:

| Market | Ridge | Cash | Buy & Hold |
| --- | ---: | ---: | ---: |
| BTCUSDT | −60.69% | 0.00% | +120.81% |
| ETHUSDT | −57.96% | 0.00% | +46.18% |

Each account begins with 10,000 USDT independently.

The Ridge strategy recorded 570 buys and 570 sells on BTC; 499 buys and 499 sells on ETH.

Its attributed trading costs were approximately 9,932.12 USDT and 9,239.49 USDT respectively.

Do not double-count spread or slippage when explaining these costs.

Use the authoritative research report for exact details.

### Charting

Prioritise one excellent, accurate comparison chart over several decorative charts.

A grouped return bar chart or dot plot comparing Ridge, Cash and Buy & Hold for both markets would be useful and is supported by the verified summary.

Include readable hover and keyboard-focus states, tooltips, legends and a labelled zero line.

Do not fabricate historical equity curves, drawdown series or price histories from summary metrics.

Only introduce time-series charts when the underlying verified observations are available through an approved public data export.

Do not introduce a fake backtest execution flow.

A future backtest-running interface can be visually anticipated, but it must remain clearly labelled as planned or unavailable.

## 7. Field Notes — research journal

Create a polished editorial index and article reading experience.

The design should include:

- Featured article area
- Readable article cards
- Research topics and dates
- Publication status
- Strong heading hierarchy
- Optional table of contents
- Related articles
- Links to methodology and supporting reports

Use the existing `docs/field-notes/` content as the editorial source of truth.

Do not silently change research conclusions or create new evidence.

The existing articles are drafts. In local development, permit editorial previews, but do not make draft content automatically eligible for public production publishing.

Implement a simple explicit publication approval mechanism or allowlist so a later deployment cannot accidentally expose unapproved draft articles.

Keep this mechanism lightweight and file-based.

## 8. The Field Guide — educational knowledge base

The Field Guide should help visitors understand financial markets and quantitative research.

Plan categories for:

- Trading strategies
- Asset classes and instruments
- Backtesting fundamentals
- Risk and performance metrics
- Predictive modelling and signals
- Market data and execution

Initial guide examples:

**Understanding Trading Strategies:** Trend following, momentum, mean reversion, Buy & Hold and machine-learning-generated signals.

**Asset Classes Explained:** Crypto, equities, ETFs, bonds, currencies and commodities, with clear explanations of futures and options as instruments.

**What Is Backtesting?:** Historical simulation, data leakage, overfitting, benchmarks, execution assumptions and transaction costs.

**Understanding Performance Metrics:** Return, volatility, drawdown, Sharpe ratio, turnover, fees, spread and slippage.

**From Forecasts to Trades:** Distinguish model forecasts, strategy decisions, hypothetical execution, prospective paper trading and real trades.

Write only a small number of concise, carefully reviewed introductory drafts where useful for the prototype. Build sensible navigation for the remaining topics.

Clearly distinguish **educational explanations**, **implemented strategies** and **planned research**.

Do not imply Backtest Badger currently supports equities, futures or options backtesting.

## 9. About and Methodology

Provide a concise introduction to the project and what makes its methodology rigorous.

Highlight:

- Reproducible data and model provenance
- Causal feature construction
- Transparent execution assumptions
- Verified evidence and auditability
- Honest negative research findings
- Open-source engineering
- Distinction between historical and prospective research

Avoid exaggerated claims of profitability, predictive power or financial suitability.

Include a GitHub repository link.

## 10. Reusable frontend components

Implement a small, coherent component system.

Suggested components include:

**Layout:** SiteHeader, MobileNavigation, PageContainer, SectionHeading, SiteFooter.

**Brand:** BadgerMark, Wordmark, HeroIllustration, ResearchStatusLabel.

**Research:** MetricCard, PerformanceComparisonChart, StrategySummary, MethodologyPanel, ResearchDisclaimer, DataTimestamp.

**Editorial:** ArticleCard, ArticleLayout, TopicTag, ReadingMetadata, RelatedArticles.

**Interaction:** MarketSelector, TabGroup, Tooltip, LoadingState, EmptyState.

**Future concepts:** BacktestProgressVisual, BadgerTrailAnimation.

The future concepts should remain lightweight and should not imply actual computation.

Use shared primitives and design tokens, but do not create a large internal component framework.

## 11. Motion and interaction

Create subtle, purposeful interactions that make the website feel alive.

Explore:

- Polished navigation hover/focus states
- Responsive chart hover tooltips
- Animated metric counters using verified values
- Smooth reveal of research results
- Subtle chart drawing where verified chart data exist
- Small mascot hover or motion details
- Light scroll-based transitions
- Tasteful research-loading states

All motion must respect `prefers-reduced-motion`.

Animations must not delay navigation unnecessarily.

### Backtest badger concept

A signature future interaction is a small badger following a historical price trend backwards when a backtest begins.

For Stage 5A, explore this visually without implying the website can currently execute backtests.

If useful, create a clearly labelled design-preview interaction, with an abstract decorative path and user-triggered motion.

Do not attach simulated completion percentages or synthetic performance curves to real historical results.

The animation should later be able to reflect actual backtest progress once an execution API exists.

### Loading microcopy

Potential messages:

- The badger is backtesting...
- Digging through historical candles...
- Replaying market history...
- Sniffing out overfitting...
- Following the trail backward...

Use these only in genuinely appropriate states.

For example, do not show “The badger is backtesting” during ordinary page loading when no backtest is running.

## 12. Frontend technology

Provisional preference:

- Next.js
- React
- TypeScript
- Tailwind CSS
- A lightweight charting library where justified
- Markdown-based editorial content

Briefly compare Next.js against Astro for this project's mix of editorial pages, research dashboards and future interactivity.

Prefer a straightforward technical choice that supports excellent visual quality and later extension.

Place the frontend within the existing repository, preferably under `web/`.

The Python research package and website must remain separately understandable.

Do not change the existing backend package layout merely to accommodate the prototype.

### Initial data architecture

Use small, typed, static public-facing data modules derived from verified research reports.

Keep content separate from UI presentation.

Record source references and data dates.

Design a simple future path towards approved read-only API integration.

Do not create a public API, production database user, CMS, authentication system, queue service or new database at this stage.

## 13. Future extensibility

The platform should eventually accommodate:

- Additional assets and trading markets
- Stocks, futures, options and other instruments
- Different strategies and model families
- Multiple market-data providers
- Parameterised backtest requests
- New risk and performance metrics
- Prospective paper portfolios

Avoid hard-coding BTC/ETH into universal chart and layout components.

However, do not implement speculative strategy registries, plugin frameworks, generic financial schemas or complex orchestration merely for hypothetical future use.

Add abstractions when actual new strategies or data sources require them.

## 14. Responsive design and accessibility

Prioritise desktop data exploration while providing an excellent mobile experience.

Check:

- Responsive hero layout
- Navigation behaviour
- Chart responsiveness
- Accessible comparison tables
- Keyboard focus and tooltips
- Contrast of forest green and sand accents
- Reduced-motion support
- Readable long-form articles
- Clear positive/negative metric semantics without relying on colour alone
- Sensible loading and empty states

Avoid horizontal overflow and tiny financial labels.

## 15. Implementation priorities

Build a genuinely runnable, navigable prototype.

Suggested delivery order:

1. Project scaffolding and design tokens
2. Shared site navigation and typography
3. Homepage and mascot treatment
4. The Dig's verified research comparison
5. Burrow dashboard structure
6. Field Notes article experience
7. Field Guide structure and initial content
8. About/Methodology
9. Responsive polish and interactions

Do not spend excessive time generating decorative assets before the basic site works.

Aim for a coherent first product experience rather than maximum feature count.

## 16. Validation

Install dependencies locally if necessary.

Run the development server, lint/type checking and production build.

If browser inspection is available, inspect desktop and mobile layouts and correct visible problems.

Provide local preview instructions.

Validate the displayed numerical research results against the authoritative report.

Check significant navigation routes and editorial links.

Record missing assets, inaccessible features or unsupported interactions honestly.

Do not claim screenshot, accessibility or browser testing occurred unless it did.

## 17. Documentation and prompt archive

Create:

`docs/stage-05a-website-design.md`

Include:

- Technology decision
- Information architecture
- Design-token palette
- Typography and mascot treatment
- Page and component structure
- Verified research data sources
- Local preview instructions
- Known limitations
- Next implementation priorities

Archive this entire prompt **verbatim** at:

`prompts/stage-05-web/001-website-design-and-local-prototype.md`

Update `prompts/README.md` as needed.

## 18. Hard boundaries

- No AWS or Lightsail access
- No changes to backtestbadger.com or DNS
- No production deployment
- No production database connection
- No new trading research or historical replay
- No model fitting or evidence modification
- No prospective paper trading activation
- No real-money trading
- No fabricated financial data or results
- No publication of unapproved draft articles
- No Git commit or push

Do not modify the scientific Python code or historical research evidence.

## Final response

Report:

1. Implemented frontend structure and routes
2. Visual identity and mascot variations created
3. Framework decision and rationale
4. Working pages and components
5. Verified research figures used
6. Interactions and animations implemented versus planned
7. Local preview commands
8. Tests, linting, builds and browser checks actually performed
9. Limitations and proposed next development increment
10. Recommended Conventional Commit message

Stop for owner review before committing, pushing or deploying anything.