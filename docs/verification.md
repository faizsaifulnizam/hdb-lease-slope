# Verification — public repository and reproduction scope

## Public status — 2026-10-04

The repository is **public** and **GitHub Pages is enabled**, serving `main:/docs` at [the report site](https://faizsaifulnizam.github.io/hdb-lease-slope/). The initial clean-history publication was merged as [`a59ade1`](https://github.com/faizsaifulnizam/hdb-lease-slope/commit/a59ade1).

The linked [historical JSON receipt](reproducibility.json) is the **old private-archive run**, head `2359e7812114e4d6aa18ae2d73acfd9fe3f7dbd5`. It reused `card-book-quality`'s installed Windows interpreter with the same pinned dependencies. It is not evidence for this public commit or a fresh dependency setup. Its original artifact hashes and command coverage are retained and explicitly labelled historical.

## Reproduction contract

Use the README's commands from the repository root with Python 3.12.10, DuckDB 1.5.6, NumPy 2.5.3 and matplotlib 3.11.2. If `uv` is missing, install it with `pip install uv` first. The reviewed HDB input is SHA-256 `945e09d75efb2eec1ab1618ce369c0d8eb885ef34158e29426f1af141d4000e4`, 242,032 rows and 118 registration months, January 2017–partial October 2026. [Source receipt](../outputs/source_snapshot.json).

`src/verify.py` independently recomputes three raw band medians, verifies four headline medians, checks relative Markdown/image links and banner XML, and prints artifact hashes. The headline check matches **year × scope × historical group**, requires exactly four distinct expected keys, and compares against the reviewed full-precision anchors with **absolute tolerance <1e-9 percentage points**. Missing/duplicate/wrong-year groups, non-finite values and material numerical changes fail. Rounded ten-decimal spot-checks must remain in the README. It no longer demands exact float text or treats roundoff as proof of a source revision.

The external reviewer reported a Linux refit of identical input bytes changing the mature all-type median from `1.198415688496771` to `1.1984156884967616`. Those last-digit differences are consistent with floating-point linear-algebra roundoff; no headline changes at displayed precision. The regression uses all four independently reported Linux medians and also checks changed headlines, invalid values and group coverage. This is test input, not replacement analysis data.

Same-environment repeat builds have reproduced the reviewed CSV/PNG bytes. **Cross-OS OLS CSV text and PNG bytes may differ**; numeric checks, not cross-platform byte identity, are the acceptance contract. Input identity is still a byte SHA-256 check. Changed official bytes require reviewing and refreshing the analysis, receipts and anchors. The downloader validates its cache; staging preserves the committed retrieval time only when all other source metadata match. The ignored pull manifest records actual acquisition time.

## CI coverage

- **Smoke:** stdlib parser/cache/rollback checks, headline-roundoff regression and committed-artifact ledger/transformation checks.
- **Focused offline:** DuckDB staging and NumPy OLS/HC3 tests, plus the same headline regression. The licensed frozen archive now supports a full offline stage/refit/render and twelve-table receipt comparison before the consumer regressions. Synthetic mutations are tests only; expected historical outputs are authentic receipts.
- **Linux live refit (manual `workflow_dispatch`):** fresh `uv` environment and pinned dependency setup; official download; reviewed source SHA-256 guard; staging, analysis, all six theme figures, focused tests, smoke, `src/verify.py` and the figure mirror/rollback check. This job intentionally fails with a snapshot-review message if the official file changes. PR/main checks use the separate frozen offline replay, so a later official revision does not invalidate the preserved historical analysis. The source guard is retained unchanged; new bytes are never substituted to make a check pass. Live raw cache stays ignored; the separate licensed archive provides historical offline replay. It does not require Windows-produced CSV/PNG bytes to match Linux.

## Local frozen replay assurance

The frozen archive in [data/snapshots](../data/snapshots/README.md) preserves the exact reviewed primary bytes and all twelve CSV receipts. `download.py --replay` validates source identity before staging and refuses a changed raw workspace. Existing identical-byte cache provenance is kept rather than rewritten. The live CI source check remains before staging; a live revision still requires review.

Analysis, normal verification and figures compare the validated raw descriptor with the staged source receipt before consuming artifacts; acquisition-time-only differences are allowed. This is **raw-to-stage source identity**, not a parquet tamper proof or complete analysis/figure generation manifest. Annual model populations, including the previous year and strict-filter subset, require twelve calendar months; the per-segment six-month rule is unchanged. Invalid windows preserve all seven previous analysis finals, but do not undo a staging batch that already completed.

`verify.py --compare-reviewed` additionally compares complete coverage, headers, deterministic row order/multiplicity and every cell of the twelve archived tables. Count/category/identifier/blank fields are exact; named floating fields allow absolute 1e-9 or relative 1e-12 roundoff tolerance. The four original headline anchors retain their stricter absolute <1e-9 tolerance. This comparator is receipt parity, not independent model recomputation; the default verifier remains the documented sampled raw/headline/link/banner check with the new source guard.

Local Windows execution reused the existing pinned environment: no new installation or fresh-setup claim. Historical numeric/artifact bytes remained unchanged in full producer replays, including all six PNGs and report/site mirrors. Public archive delivery, exact-commit hosted CI, current deployed reading surfaces, new native/macOS execution and screen-reader behavior still require separate receipts. No model estimand, uncertainty method or reviewed anchors changed.

## Reviewed source refresh — 2026-10-07

Original build/review: 2026-10-04. Actual refresh acquisition: **2026-10-07 00:24:09 SGT** (`2026-10-06T16:24:09+00:00` in the manifest). The new receipt records 23,940,111 bytes / 242,032 rows, SHA-256 `945e09d75efb2eec1ab1618ce369c0d8eb885ef34158e29426f1af141d4000e4`. Both old and fresh immutable raw snapshots and acquisition manifests were preserved outside the repository, with exact byte hashes verified.

Full-field, multiplicity-preserving CSV comparison found **114 October 2026 additions and two removals (one July, one August 2026)**, net +112. No 2025 or 2024 rows changed. Raw ledger is now **242,031 retained + one inconsistent lease = 242,032**. The former source-hash guard was observed rejecting these new bytes; the existing guard is unchanged and a future official revision still requires review.

The complete README setup created a dedicated Python 3.12.10 environment and installed the existing 12 pinned requirements. Staging, full analysis, all six theme renders, **12 focused tests**, artifact smoke, `src/verify.py` and **two figure mirror/rollback tests** passed. The runner cleared inherited `PYTHONPATH`/`PYTHONHOME` first because this agent host otherwise injected incompatible Python 3.14 NumPy into the 3.12 environment. No project dependency or pipeline code changed.

An independent verifier imported no production helpers: stdlib CSV parsing/quantiles checked all **6,112 historical bucket rows**, **639 baseline bucket rows** and **1,272 annual segment profiles**. Reduced QR plus a separate linear solve and HC3 sandwich checked all **62 reported baseline coefficients/intervals** and every one of the **28 sensitivity summaries**, within 1e-9 percentage points. Three raw band medians and the four group medians were independently reproduced. All nine baseline/sensitivity/lookup/excluded-row CSVs remain byte-identical, so no numerical anchor was rebaselined. Only historical profile/band exports, the raw ledger and source receipt change numerically.

Two full producer replays reproduced **32 artifact hashes** in the same environment: 13 output CSV/JSON files, six report figures, six site figure mirrors and four banner source/mirrors, plus three unchanged social-card assets. All tracked-file hashes also remained unchanged across the final literal README replay. The six renders passed executable margin/overlap/partial-regression checks and mirror checks. Fresh visual inspection was attempted twice but the image-analysis service disconnected; the contact sheet and full-size images are retained for independent parent review. This is candidate evidence, not a merged/deployed-page receipt.

## Remediation replay — 2026-10-04

A fresh remote clone of the public repository, with this remediation diff applied, created its own Python 3.12.10 environment and installed the pinned requirements. It downloaded the same reviewed HDB SHA-256, then ran every README Python command: staging, full analysis, figures, 12 focused tests, smoke, `src/verify.py` and the separate mirror/rollback regression. All **82 tracked/new source and artifact files** retained their pre-run byte hashes. The working-copy full refit also reproduced the committed output and chart bytes. These are Windows same-environment checks; the separate Linux CI job supplies cross-OS execution evidence.

## Hiring-audit repair replay — 2026-10-04

A fresh clone of public `b11637c`, overlaid with the reviewed repair diff, pasted the README Bash block literally in a new Git Bash process. Executable platform selection activated its own Python 3.12.10 environment, and the install resolved all 12 direct/transitive pins. The live download matched the reviewed input SHA-256. All producers, 12 focused tests, smoke, `src/verify.py` and two dependency-backed figure checks passed. All 82 tracked-file hashes stayed unchanged after the first replay and after a second producer replay; all 13 output CSV/JSON files matched the repaired working copy. This is Windows candidate evidence, not evidence for a later merged commit.

Oversized month/year components now become `invalid_lease_text` at the SQL staging seam; a regression first reproduced the INT32 year-multiplication failure, then passed with the bounded guard. The real snapshot's retained population remains 241,919 and every numerical output is byte-unchanged. The figure check renders both themes in isolation, verifies the raw/adjusted panel headings and report/site mirror bytes, and retains the existing later-swap rollback probe. Same-environment rendering repeats pass; cross-OS pixel identity is still not promised.

## Prior public-candidate evidence

Before the original publication, a fresh remote clone at `431dee286eb2f79a0c500f9750123a4c061e0a7f` ran the README environment setup and all Python commands on Windows. Eleven focused tests, the separate figure mirror/rollback check and smoke passed. Twenty-one protected CSV/JSON/PNG/SVG artifacts matched and the tracked tree remained clean. This is dated candidate evidence, not a claim that an old receipt verifies every future commit.

The original private analysis/reviews are preserved in the read-only private archive. The clean public history starts at `0a470ff1522b256f9bc56acce20738c95db5b02c`. Local and live publication checks found no non-noreply identity leakage in that clean history. The publication layer kept the original numerical outputs and plot bytes, added the report/card and synchronized figure/banner copies into `docs/img/`.

## Scope and limits

Figure generation checks text margins, clipping/overlap and the partial-regression identity. The mirror regression injects a later destination-swap failure and confirms original and mirrored files roll back. Ordinary batch swaps are covered; power loss/process kill across the entire pipeline and concurrent writers are not. One writer is required.

The manual GitHub repository social-preview upload remains separate. There is no binary release or social-post claim. Local QA is not proof of deployment; exact-commit Actions results and a live report read-back are required after publishing.

The source-access record remains bounded: HDB Annex A was fetched as a PDF and its full list read; the live data.gov.sg dictionary/total matched the CSV. Failed extraction/browser/obsolete-endpoint attempts were not evidence. No blanket success claim is made for automated access to every external reference.

2025 is the latest complete past year: 25,084 valid transactions / 129 town × type cells; 62 eligible models / 22,048 observations. Historical groups are the 2023 Annex A list, not current project classifications. Storey/area/month controls leave vintage/location confounding; HC3 is not block-clustered and intervals may be too narrow. These are cross-sectional associations, **not causal depreciation or individual-flat forecasts**.
