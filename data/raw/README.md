# Raw acquisition — ignored, never hand-edited

[HDB resale registrations, January 2017 onwards](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view). Dataset `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`; Singapore Open Data Licence, © HDB.

`python src/download.py` independently uses the public v1 poll-download → initiate (if needed) → signed-URL download flow with browser-style headers. Structure/history validate before replacement; raw/manifest swaps roll back ordinary errors. Cache must match byte provenance. `--force` explicitly refreshes; no sibling dependency.

Original build pull: 2026-10-04 08:13:38 SGT. Reviewed refresh: 2026-10-07 00:24:09 SGT; 23,940,111 bytes / 242,032 records, 2017-01–partial 2026-10. Receipt: local `pull_manifest.json`; committed [source_snapshot.json](../../outputs/source_snapshot.json). Source bytes/seed metadata stay ignored. A later revision can change the hash/counts; rerun the pipeline, don't claim old-snapshot identity.

The 2017-onward file is scope, not a claim that earlier official files never recorded remaining lease.
