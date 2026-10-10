# Frozen HDB replay input

`reviewed-hdb.zip` is a local, immutable replay package, not a fresh download. © Housing & Development Board (HDB), Singapore; source: [data.gov.sg](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view). Data reuse: [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). Independent, unofficial analysis; no HDB endorsement. The licence/source attribution is also retained inside the archive as the original raw README.

- Archive SHA-256: `d00f218786a9b0dd6cf6b6276f631e5858f0e3ee20bffcf0f84155de46c43a42`; 3,167,950 bytes (below the repository size limits).
- Original CSV bytes: 23,940,111; SHA-256 `945e09d75efb2eec1ab1618ce369c0d8eb885ef34158e29426f1af141d4000e4`; 242,032 rows, 118 months, January 2017–partial October 2026.
- Original ignored raw manifest and README are preserved byte-for-byte, alongside all twelve reviewed output CSVs. The raw cache manifest records an identical-byte repull at `2026-10-06T16:39:48+00:00`; the committed source receipt preserves the earlier reviewed acquisition time `2026-10-06T16:24:09+00:00`. These times are historical receipts, not a new acquisition or current-data guarantee.

After the README environment setup, run `python src/download.py --replay` instead of the live download, then the same staging, analysis, figure and test commands. Finish with `python src/verify.py --compare-reviewed` to compare every CSV against the archived receipt. No archive paths are extracted blindly: only the fixed CSV and manifest members are restored with the existing batch publisher. The source lock runs **before staging**; a changed existing raw file is refused and preserved. Preserve a changed-input workspace separately before replaying in a fresh clone. `--force` is the separate live-refresh workflow, not replay.

The comparator checks full table coverage, headers, row multiplicity/order and every cell. Strings, identifiers, integer counts, categories and blanks must match exactly; differing text in the named floating fields must agree within absolute 1e-9 or relative 1e-12 tolerance. This permits floating-point roundoff; it is a receipt comparator, not an independent reimplementation of all models. Three independent raw bands and the four stricter headline anchors remain in the normal verifier. Same-environment CSV/render repeat hashes are a separate check; cross-platform pixel equality is not promised.

Packaged locally only. Anonymous GitHub distribution and exact-commit CI execution require separately authorized publication; neither is established by this local archive.
