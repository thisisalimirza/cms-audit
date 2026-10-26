# Reproducibility package

Retrospective evaluation of a transparent public-data screen for Medicare Part B spending surges. Author: Ali Mirza, B.S.

## Contents
- `DATA.md`: where to download inputs and how they are used.
- `requirements.txt`: software versions.
- `class_map.csv`, `CLASS_RULES.md`: code-to-class mapping and the rules that produce it.
- `scripts/`: ordered pipeline. `run_all.sh`: runs everything.

## Run
```bash
mkdir work && cd work && mkdir data   # put the six Geo CSVs in data/ (DATA.md)
pip install -r ../repro/requirements.txt
ROOT=$(pwd) bash ../repro/run_all.sh
```
Runtime is about 5-10 minutes after downloads; step 07 needs network access unless `data/provider_cache/` is supplied.

## Scripts
| Order | Script | Purpose | Main outputs |
|---|---|---|---|
| 01 | build_geo.py | Read Geo files; national and state allowed amounts | data/national_by_code_year.csv, data/state_by_code_year.csv, data/geo_all.pkl |
| 02 | concentration.py | Category, state HHI, state coverage | data/concentration_by_code_year.csv |
| 03 | lookback.py | Prespecified code rule by flag year 2020-2023; sensitivity grid | tables/f_lookback_*.csv, tables/g_sensitivity_grid.csv |
| 04 | lookback_figure.py | Skin spending and flagged-vs-unflagged growth | figures/fig5_lookback*.png/.pdf |
| 05 | churn_figure.py | Skin spending by code vintage | figures/fig6_skin_code_churn.png/.pdf, tables/h_skin_spend_by_code_vintage.csv |
| 06 | product_classes.py | Class map, class-level look-back, 2024 watchlist | tables/i_*.csv, data/watchlist_2024_raw.csv |
| 07 | watchlist_providers.py | 2024 provider-file rows for watchlist codes | data/watchlist_provider_shares.csv |
| 08 | watchlist_table_figure.py | Watchlist table with provider-file coverage | tables/j_watchlist_2024*.csv, figures/fig7_*.png |
| 09 | tradeoff.py | Review burden vs detection for the four approaches, 2020-2023 | tables/k_tradeoff_*.csv, figures/fig8_tradeoff*.png/.pdf |
| 10 | master_results.py | **Single source of truth**: every reported statistic, plus exhibit tables whose cells are registered in it | tables/master_results.csv/.json, tables/exhibits/*.csv |
| 11 | writeup.py | Manuscripts, appendix, abstracts generated from master_results (docx, pdf) | writeup/*.docx, writeup/*.pdf, writeup/submission_figures/fig1.pdf, fig2.pdf, writeup/wordcounts.json |
| 12 | poster.js | SGIM poster, numbers read from master_results.json | writeup/poster/poster_SGIM2027_48x36.pptx/.pdf |
| check | check_numbers.py | Extracts every number from the docx texts and tables and the poster, and fails if any is not in master_results | console report; exit code 1 on any unmatched number |

Approach names used everywhere: prespecified code rule (primary), prespecified class rule, secondary class growth screen, exploratory weighted-HHI rule (post hoc).

Legacy scripts from the earlier analysis (original 03_provider_pull, 04_analyses, 07_writeup) are not part of this package.

## Exhibits to sources (research paper)
| Exhibit | File | Script |
|---|---|---|
| Figure 1, code churn | figures/fig6_skin_code_churn.pdf (submitted as fig1.pdf) | 05 |
| Figure 2, review-burden tradeoff | figures/fig8_tradeoff.pdf (submitted as fig2.pdf) | 09 |
| Table 1, tradeoff summary | tables/exhibits/table1_tradeoff.csv | 10 |
| Table 2, watchlist excerpt with provider-file coverage | tables/exhibits/table2_watchlist_top.csv | 10 |
| Appendix A1, 2021 code flags | tables/exhibits/A1_flags_2021.csv | 10 |
| Appendix A2, by year, incl. single-code vs named classes flagged | tables/exhibits/A2_by_year.csv | 10 |
| Appendix A3, full 52-code watchlist | tables/exhibits/A3_watchlist_all.csv | 10 |
| Appendix A4, look-back figure | figures/fig5_lookback.png | 04 |
| Appendix A5, pooled vs weighted HHI worked example | tables/exhibits/A5_worked_example.csv | 10 |
| Poster Figures 1 and 2 | figures/fig6_skin_code_churn.png, figures/fig8_tradeoff_poster.png | 05, 09 |

## Repository
Repository URL: https://github.com/thisisalimirza/cms-audit. License: MIT for code (LICENSE); CMS source data are US government works in the public domain. Citation metadata: CITATION.cff.

## Cautions
Thresholds were chosen with general knowledge of the skin-substitute surge, and there is one known outcome; results are a retrospective evaluation, not validation. Flagged or captured spending is not evidence of improper spending or misconduct.

## Manuscript versions
- writeup/long_paper_HealthAffairsScholar_COMPLETE.docx/.pdf: reader version with all figures and tables inline (Table 1, Figure 2, Table 2 and wide appendix tables in landscape sections) and the appendix exhibits at the end.
- writeup/long_paper_HealthAffairsScholar_SUBMISSION.docx/.pdf: journal upload version; figures are supplied separately in writeup/submission_figures/.
