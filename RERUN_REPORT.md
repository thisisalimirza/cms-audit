# Clean rerun, round 2 (2026-10-26, America/New_York)

A new working directory (/tmp/rerun2) was created containing only the six raw Geography CSVs (symlinked) and the cached 2024 provider-API responses (`data/provider_cache/2024_*.json`, copied). `ROOT=/tmp/rerun2 bash repro/run_all.sh` ran all 12 steps plus check_numbers.py without errors in about 80 seconds (log: rerun_log.txt).

Results:
- `tables/master_results.csv` and `tables/master_results.json` are byte-identical to the project copies (1,070 statistics).
- All six exhibit tables in `tables/exhibits/` and `writeup/wordcounts.json` are byte-identical.
- The text and table content of all five generated docx files is identical.
- check_numbers.py in the rerun reported PASS (1,075 numeric tokens, 0 unmatched).

A first round-2 rerun differed in 7 master values in the 16th significant digit (floating-point summation order). The master script now stores values to 12 significant digits; no displayed number changed. The provider-API step was not re-queried; a run without the cache queries the live CMS API, and CMS may have revised the file since retrieval.
