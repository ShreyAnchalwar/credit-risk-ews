# TODOs

Deferred work items. Each has context so future-you (or a teammate) can pick it up without re-doing the thinking.

---

## TODO-1: Expand smoke_test.py into a pytest suite

**What:** Replace `tests/smoke_test.py` (20-line assertion file) with proper pytest coverage — one test per loader, one per model, one per chart, one per algorithmic transform (market-features math, label construction, time-split semantics).

**Why:** The smoke test covers the risky *new* codepaths from the refactor (shim, stubs, check_loader, provenance header). It does NOT cover the algorithmic logic that Allen and Darren will inadvertently depend on when they plug in real data. A real pytest suite catches subtle regressions at Phase 2 integration time rather than at demo time.

**Pros:**
- Catches regressions in Phase 2 teammate integration
- Documents expected behavior of each loader / model / chart
- Enables confident further refactoring
- Capstone submission with tests is a visible signal to markers

**Cons:**
- Adds `pytest` and possibly `hypothesis` as dev dependencies
- ~1 day of writing fixtures (yfinance mock, small golden-panel fixture, etc.)
- Maintenance burden as Phase 2 changes land

**Context for pickup:**
- `tests/smoke_test.py` is the starting point — 4 assertions for shim + stubs + check_loader + provenance.
- Fixtures: create `tests/fixtures/mini_panel.csv` (2 firms × 24 months); all loader tests read from this rather than hitting yfinance.
- Goldens: snapshot `panel_phase1.csv` outputs for the 10-firm Phase 1 config, compare via SHA256 in the test.
- Models: test that `model_pooled_logit` produces a non-degenerate coefficient vector on the fixture; don't test exact values (numerical noise).
- Charts: test that each plot function writes a PNG of the expected dimensions; don't test visual content.

**Depends on:** Refactor landed; `src/ews/` package importable.

**Blocked by:** Nothing.

---

## TODO-2: Performance optimization of `build_market_features` for 80-firm panel

**What:** Rewrite the nested `for date in monthly_dates: for ticker in ...:` loop in `features.build_market_features` to use vectorized pandas operations. Current pattern does per-cell slicing that scales as O(dates × tickers × history).

**Why:** Fine at Phase 1 (10 firms, ~1500 firm-months, sub-minute). At Phase 2's 80-firm target, scales to ~12000 firm-months and the loop hits ~5× longer runtime — will be a real DX annoyance during Allen's integration loop.

**Pros:**
- 10–50× speedup at Phase 2 scale
- Cleaner, more idiomatic pandas code
- Fewer edge-case bugs from per-cell logic

**Cons:**
- Rewriting vectorized rolling logic is error-prone; high risk of subtle numerical drift
- Requires careful regression testing against the current nested-loop output (hence TODO-1 matters first)

**Context for pickup:**
- Current implementation in `src/ews/features.py` after the refactor (was `compute_market_features` in the monolith at lines 91–142).
- Key operations to vectorize: 1m/3m/6m cumulative returns, 3m/6m annualized vol, 12m peak-to-trough drawdown.
- Pandas `groupby('ticker').rolling(window)` is the standard pattern.
- IMPORTANT: the current code pads windows with `min(21, len(price_series))` — a short-history firm gets a shorter lookback rather than NaN. Preserve that semantics or change it intentionally.

**Depends on:** TODO-1 (need tests before this optimization lands).

**Blocked by:** Phase 2 real-data integration (don't optimize against placeholder data that doesn't reflect real-firm history patterns).

---

## TODO-3: Raw-data caching for Phase 2 loaders (SEC + FRED)

**What:** When Allen's `load_fundamentals(source='sec')` and the FRED macros loader land, each should check `data/raw/<source>_<key>.<ext>` and read from disk if present, otherwise hit the API and write the file.

**Why:** `load_prices` already does this (implemented in the Phase 1 refactor). SEC and FRED calls are slower than yfinance and rate-limited. A clean 80-firm run re-downloading everything is 10+ minutes of waiting.

**Pros:** 10–100× faster iteration at Phase 2 scale; fewer rate-limit issues; reproducible.

**Cons:** Cache-invalidation is subtle. SEC filings are immutable once filed so cache-forever is fine. FRED series revise historical values occasionally (GDP, etc.) — need a manual invalidation story.

**Context for pickup:**
- Mirror the `load_prices` cache implementation: check disk → read / fetch+write.
- `data/raw/` directory is already scaffolded (gitignored) from the Phase 1 refactor.
- Manual invalidation: `rm data/raw/sec_*.json` or similar. No `--refresh` flag unless someone asks.

**Depends on:** Allen's SEC loader shipping; FRED loader shipping.

**Blocked by:** Phase 2 loader work.
