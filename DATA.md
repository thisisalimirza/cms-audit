# Data retrieval

All inputs are public CMS files; no restricted data are used. Retrieved 2026-10-26 (America/New_York). Catalog: https://data.cms.gov/data.json

## 1. Medicare Physician & Other Practitioners - by Geography and Service (required)
Download each file into `data/` under the file name shown (for example `curl -L -o data/<name>.csv <url>`).

| Service year | File name | URL |
|---|---|---|
| 2019 | MUP_PHY_R21_P04_V10_D19_Geo.csv | https://data.cms.gov/sites/default/files/2021-08/MUP_PHY_R21_P04_V10_D19_Geo.csv |
| 2020 | MUP_PHY_R22_P05_V10_D20_Geo.csv | https://data.cms.gov/sites/default/files/2022-07/0d730fe9-deb8-453b-a2fd-ce778286d9f6/MUP_PHY_R22_P05_V10_D20_Geo.csv |
| 2021 | MUP_PHY_R23_P05_V10_D21_Geo.csv | https://data.cms.gov/sites/default/files/2023-05/0a47308e-812e-42cb-8ecf-0c1f457ab849/MUP_PHY_R23_P05_V10_D21_Geo.csv |
| 2022 | MUP_PHY_R24_P05_V10_D22_Geo.csv | https://data.cms.gov/sites/default/files/2024-05/3167b4d9-10c0-48f0-a680-1165f4eec064/MUP_PHY_R24_P05_V10_D22_Geo.csv |
| 2023 | MUP_PHY_R25_P05_V20_D23_Geo.csv | https://data.cms.gov/sites/default/files/2025-04/3b718a11-a28d-4c38-a13b-2c6eeb649980/MUP_PHY_R25_P05_V20_D23_Geo.csv |
| 2024 | MUP_PHY_R26_P05_V10_D24_Geo.csv | https://data.cms.gov/sites/default/files/2026-05/e534c74b-79b8-4892-8a95-5a17e2dfec9f/MUP_PHY_R26_P05_V10_D24_Geo.csv |

CMS revises files occasionally (the 2023 file is version V20). If a newer version is posted, results may differ slightly; record the version used.

## 2. Medicare Physician & Other Practitioners - by Provider and Service, 2024 (watchlist provider shares only)
Script `07_watchlist_providers.py` queries the CMS data API for each watchlist code:
`https://data.cms.gov/data-api/v1/dataset/92396110-2aed-4d63-a6a2-5d6207d46a29/data?filter[HCPCS_Cd]=<code>` (file PHY_R26_P05_V10_D24_Prov_Svc).
Responses are cached as `data/provider_cache/2024_<code>.json`; if a cache file exists, the API is not called. This step needs network access on first run.

## Definitions used
- Allowed amount = Avg_Mdcr_Alowd_Amt x Tot_Srvcs, summed over place of service.
- National totals come from the National rows of the geography file. State concentration uses state rows (50 states and DC); state rows cover less than 100% of national spending because of cell suppression and non-state geographies, and the coverage ratio is reported (`state_coverage`).
- Provider-file rows are suppressed for small cells, so provider-file totals cover only part of national spending for many codes; coverage is reported in `tables/j_watchlist_2024_nonlab_codes.csv`.
