# Chile Property Watch

Phone-first web app aggregating southern-Chile real estate listings plus market news. Static SPA on GitHub Pages, rebuilt daily by a Claude cloud routine.

- App shell + data contract: this repo's `index.html` + `src/`.
- Data lives in `data/*.json` (fixtures now, routine-generated later).
- Run tests: `npm test`

## Running the daily routine (cloud)

The routine regenerates `data/*.json` and self-publishes. A scheduled cloud run invokes:

```
python3 -m routine.build
```

That runs `main(run_date=today, publish=True)`: fetch FX (falls back to the cached
`data/fx.json` if mindicador is down), scrape BuenasParcelas + (when wired) extract
Yapo/Portal alerts — each source isolated so one failure doesn't abort the run —
build the data, skip the write if it would blank the site, then commit, push, and
confirm the GitHub Pages deploy (re-triggering the known transient deploy failure).

**What the cloud environment must provide:**
- A git checkout of this repo on `main` with push credentials (a token in the
  environment so `git push` works unattended).
- Python 3.9+ (stdlib only at runtime).

**Not yet wired (the alert half):** `main()` skips alerts until it's called with
`alert_csv_url` (the published-CSV URL of the Make→Sheet alert inbox) and a
`model_call` (a function `prompt -> reply_text` wrapping the routine's Claude).
Until then the routine publishes BuenasParcelas listings only.
