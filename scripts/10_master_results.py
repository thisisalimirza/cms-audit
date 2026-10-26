"""Single source of truth for every statistic reported in the letter, paper, abstracts, poster, and appendix.
Reads the analysis outputs (tables/*.csv, tables/*_key_numbers.json, data/*) and writes
  tables/master_results.csv and tables/master_results.json  (one row per statistic: id, value, kind, display, type, source, description)
  tables/exhibits/*.csv                                      (every exhibit table exactly as printed; every numeric cell is also a master row)
The writeup (12_writeup_prospective.py / repro 11_writeup_prospective.py) and the poster read their numbers from these files.
Types: computed = derived from CMS data by this pipeline; parameter = analytic choice; external = quoted from a cited source;
illustrative = hypothetical arithmetic in the appendix worked example (not data)."""
import json, math, pandas as pd, numpy as np
R = []
def disp(v, kind, dec):
    if kind == 'count': return f'{int(round(v)):,}'
    if kind == 'frac': return f'{v*100:.{dec}f}%'
    if kind == 'usdM': return f'${v/1000:.2f} billion' if abs(v) >= 1000 else f'${v:.{dec}f} million'
    if kind == 'num': return f'{v:,.{dec}f}'
    raise ValueError(kind)
def add(id_, v, kind, desc, src, typ='computed', dec=1, display=None):
    v = float(v) if not isinstance(v, str) else v
    R.append({'id': id_, 'value': v, 'kind': kind, 'decimals': dec, 'display': display if display is not None else disp(v, kind, dec), 'type': typ, 'source': src, 'description': desc})
# ---------------- external (cited) and parameters ----------------
add('ext.cms_skin_2019_M', 252, 'usdM', 'CMS-reported Part B skin-substitute spending, 2019', 'Ref 2 (CMS CY2026 PFS final rule fact sheet)', 'external', 0)
add('ext.cms_skin_2024_B', 10, 'num', 'CMS/OIG: skin-substitute spending exceeded $10 billion in 2024', 'Refs 1-2', 'external', 0, '$10 billion')
add('ext.oig_quarterly_start_M', 400, 'usdM', 'OIG: quarterly Part B skin-substitute spending, start of 2-year window', 'Ref 1 (OIG OEI-BL-24-00420, p. with "per quarter")', 'external', 0)
add('ext.oig_quarterly_end_B', 3, 'num', 'OIG: quarterly spending reached nearly $3 billion', 'Ref 1', 'external', 0, '$3 billion')
add('ext.suppression_benes', 11, 'count', 'CMS suppresses cells with fewer than 11 beneficiaries', 'Ref 3-4 (CMS methodology)', 'external')
add('ext.release_lag_years', 2, 'count', 'Approximate release lag of public files, years', 'Ref 3 (release dates)', 'external')
for k, v, d in [('spend_M', 10, 'Spending threshold, $ million'), ('growth', 0.5, 'Growth threshold'), ('hhi', 1500, 'State HHI threshold'), ('providers', 100, 'Rendering-provider threshold'),
                ('doubling', 2, 'Doubling outcome multiplier'), ('top_decile', 0.1, 'Top-decile outcome share'), ('hhi_scale', 10000, 'HHI scale (squared shares x 10,000)')]:
    add('param.' + k, v, {'spend_M': 'usdM', 'growth': 'frac', 'top_decile': 'frac', 'hhi': 'count', 'providers': 'count', 'doubling': 'count', 'hhi_scale': 'count'}[k], d, 'Methods', 'parameter', 0)
add('param.n_flag_years', 4, 'count', 'Number of flag years evaluated (2020-2023)', 'Methods', 'parameter')
add('param.n_keyword_lists', 19, 'count', 'Drug keyword lists defined (CAR-T matched none)', 'repro/CLASS_RULES.md', 'parameter')
# ---------------- data totals and skin-substitute trend ----------------
g = pd.read_pickle('data/geo_all.pkl'); nat = g[g.Rndrng_Prvdr_Geo_Lvl == 'National']
n24 = nat[nat.year == 2024]
add('tot.allowed_2024_M', n24.allowed.sum() / 1e6, 'usdM', 'Total allowed spending, national rows, 2024', 'data/geo_all.pkl', dec=2)
add('tot.n_codes_2024', n24.HCPCS_Cd.nunique(), 'count', 'HCPCS codes in 2024 national rows', 'data/geo_all.pkl')
cm = pd.read_csv('tables/i_code_to_class_map.csv', dtype={'HCPCS_Cd': str})
add('tot.n_codes_all_years', len(cm), 'count', 'Distinct HCPCS codes, 2019-2024 (class map rows)', 'tables/i_code_to_class_map.csv')
fsk = pd.read_csv('tables/f_skin_category_by_year.csv'); ck = json.load(open('tables/class_key_numbers.json'))
for r in fsk.itertuples():
    add(f'skin.allowed_{r.year}_M', r.allowed_M, 'usdM', f'Skin-substitute allowed spending, {r.year}', 'tables/f_skin_category_by_year.csv')
    add(f'skin.pooled_hhi_{r.year}', r.hhi, 'count', f'Skin-substitute class pooled state HHI, {r.year}', 'tables/f_skin_category_by_year.csv')
    if not pd.isna(r.growth): add(f'skin.growth_{r.year}', r.growth, 'frac', f'Skin-substitute class growth vs prior year, {r.year}', 'tables/f_skin_category_by_year.csv', dec=0)
for r in ck['skin_class']:
    add(f"skin.wmean_hhi_{r['year']}", r['wmean_code_hhi'], 'count', f"Skin class spend-weighted mean member-code HHI, {r['year']}", 'tables/class_key_numbers.json')
    add(f"skin.n_codes_{r['year']}", r['n_codes'], 'count', f"Skin-substitute codes billed, {r['year']}", 'tables/class_key_numbers.json')
add('skin.pooled_hhi_min_2020_2024', fsk[fsk.year >= 2020].hhi.min(), 'count', 'Min pooled skin HHI 2020-2024', 'tables/f_skin_category_by_year.csv')
add('skin.pooled_hhi_max_2020_2024', fsk[fsk.year >= 2020].hhi.max(), 'count', 'Max pooled skin HHI 2020-2024', 'tables/f_skin_category_by_year.csv')
conc = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str}).merge(cm[['HCPCS_Cd', 'cls', 'stratum']], on='HCPCS_Cd')
sc = conc[conc.stratum == 'skin'].groupby('year')[['state_allowed_sum', 'allowed']].sum(); cov = sc.state_allowed_sum / sc.allowed
add('skin.state_coverage_min', cov.min(), 'frac', 'Min share of national skin spending visible in state rows, 2019-2024', 'data/concentration_by_code_year.csv')
add('skin.state_coverage_max', cov.max(), 'frac', 'Max share of national skin spending visible in state rows, 2019-2024', 'data/concentration_by_code_year.csv')
h = pd.read_csv('tables/h_skin_spend_by_code_vintage.csv').set_index('year')
add('skin.vintage_2023plus_in_2024_M', (h.loc[2024, '2023'] + h.loc[2024, '2024']) * 1000, 'usdM', '2024 skin spending in codes first billed 2023 or later', 'tables/h_skin_spend_by_code_vintage.csv')
lk = json.load(open('tables/lookback_key_numbers.json'))
add('churn.share_2024_skin_in_codes_absent_2021', 1 - lk['lookback_2021']['share_of_2024_skin_spend_in_codes_existing_at_t'], 'frac', 'Share of 2024 skin spending billed under codes absent in 2021', 'tables/lookback_key_numbers.json')
# ---------------- look-back (code rule, 2021 and 2022) ----------------
ps = {(r['t'], r['stratum']): r for r in lk['perf_summary']}
add('lb21.n_flagged', lk['lookback_2021']['n_composite_nonlab'], 'count', 'Code rule flags, 2021 data, non-lab', 'tables/lookback_key_numbers.json')
add('lb21.n_eligible', ps[(2021, 'non-lab')]['n_flagged'] + ps[(2021, 'non-lab')]['n_unflagged_ge10M'], 'count', 'Eligible non-lab codes (>= $10M), 2021', 'tables/lookback_key_numbers.json')
add('lb21.n_skin', lk['lookback_2021']['n_composite_skin'], 'count', 'Skin codes among 2021 code flags', 'tables/lookback_key_numbers.json')
add('lb21.flagged_ratio', ps[(2021, 'non-lab')]['flagged_ratio_2024_to_t'], 'num', '2024/2021 spending ratio, flagged codes', 'tables/lookback_key_numbers.json', dec=2)
add('lb21.unflagged_ratio', ps[(2021, 'non-lab')]['unflagged_ratio_2024_to_t'], 'num', '2024/2021 spending ratio, unflagged codes', 'tables/lookback_key_numbers.json', dec=2)
add('lb21.share_2024_skin_captured', lk['lookback_2021']['share_of_2024_skin_spend_in_flagged_codes'], 'frac', 'Share of 2024 skin spending in codes flagged with 2021 data', 'tables/lookback_key_numbers.json')
add('lb22.share_2024_skin_captured', lk['lookback_2022']['share_of_2024_skin_spend_in_flagged_codes'], 'frac', 'Share of 2024 skin spending in codes flagged with 2022 data', 'tables/lookback_key_numbers.json')
add('grid.n_combos', lk['grid_2021']['n_combos'], 'count', 'Threshold combinations in sensitivity grid', 'tables/lookback_key_numbers.json')
add('grid.n_combos_any_skin_2021', lk['grid_2021']['combos_flagging_any_skin'], 'count', 'Combinations flagging >= 1 skin code, 2021', 'tables/lookback_key_numbers.json')
add('grid.n_combos_any_skin_2022', lk['grid_2022']['combos_flagging_any_skin'], 'count', 'Combinations flagging >= 1 skin code, 2022', 'tables/lookback_key_numbers.json')
# ---------------- class map ----------------
named = cm[~cm.cls.str.endswith('(unclassified, own class)')]
add('cls.n_codes_named', len(named), 'count', 'Codes assigned to named (multi-code) classes', 'tables/i_code_to_class_map.csv')
add('cls.share_codes_named', len(named) / len(cm), 'frac', 'Share of codes in named classes', 'tables/i_code_to_class_map.csv')
add('cls.n_codes_single', len(cm) - len(named), 'count', 'Codes that are their own single-code class', 'tables/i_code_to_class_map.csv')
add('cls.n_named', named.cls.nunique(), 'count', 'Named classes', 'tables/i_code_to_class_map.csv')
for s_, k in [('skin', 'skin'), ('lab', 'lab')]: add(f'cls.n_named_{k}', named[named.stratum == s_].cls.nunique(), 'count', f'Named {k} classes', 'tables/i_code_to_class_map.csv')
oth = named[named.stratum == 'other']; ndrug = oth[oth.category.str.startswith('Drug')].cls.nunique()
add('cls.n_named_drug', ndrug, 'count', 'Named drug classes', 'tables/i_code_to_class_map.csv'); add('cls.n_named_service', oth.cls.nunique() - ndrug, 'count', 'Named service families', 'tables/i_code_to_class_map.csv')
# ---------------- tradeoff (flag years 2020-2023) ----------------
T = pd.read_csv('tables/k_tradeoff_by_year.csv')
AP = {'code': 'Prespecified code rule', 'cpre': 'Prespecified class rule', 'cgr': 'Secondary class growth screen', 'cw': 'Exploratory weighted-HHI rule'}
MET = {'units_flagged': ('num', 1), 'classes_touched': ('num', 1), 'share_of_subsequent_nonlab_spend_flagged': ('frac', 1), 'share_of_positive_growth_captured': ('frac', 1),
       'share_of_positive_growth_captured_excl_skin': ('frac', 1), 'O1_doubling_class_sens': ('frac', 1), 'O1_doubling_class_ppv': ('frac', 1),
       'O2_top_decile_increase_class_sens': ('frac', 1), 'O2_top_decile_increase_class_ppv': ('frac', 1), 'skin_2024_captured': ('frac', 1),
       'O1_doubling_code_sens': ('frac', 1), 'O1_doubling_code_ppv': ('frac', 1), 'n_flagged_named_classes': ('num', 1), 'n_flagged_single_code_classes': ('num', 1)}
for a, lab in AP.items():
    d = T[T.approach == lab]
    for c, (k, dec) in MET.items():
        add(f'tr.{a}.mean.{c}', d[c].mean(), k, f'{lab}: mean 2020-2023 of {c}', 'tables/k_tradeoff_by_year.csv', dec=dec)
    for c in ['units_flagged', 'classes_touched', 'n_flagged_named_classes', 'n_flagged_single_code_classes']:
        add(f'tr.{a}.min.{c}', d[c].min(), 'count', f'{lab}: min over years of {c}', 'tables/k_tradeoff_by_year.csv'); add(f'tr.{a}.max.{c}', d[c].max(), 'count', f'{lab}: max over years of {c}', 'tables/k_tradeoff_by_year.csv')
    for r in d.itertuples():
        for c in ['units_flagged', 'classes_touched', 'n_flagged_named_classes', 'n_flagged_single_code_classes', 'eligible_units', 'O1_doubling_n_classes']:
            add(f'tr.{a}.{r.t}.{c}', getattr(r, c), 'count', f'{lab}, {r.t}: {c}', 'tables/k_tradeoff_by_year.csv')
        for c in ['share_of_positive_growth_captured', 'share_of_positive_growth_captured_excl_skin', 'skin_2024_captured']:
            add(f'tr.{a}.{r.t}.{c}', getattr(r, c), 'frac', f'{lab}, {r.t}: {c}', 'tables/k_tradeoff_by_year.csv')
    add(f'tr.{a}.n_years_flag_skin', int((d.skin_2024_captured > 0).sum()), 'count', f'{lab}: flag years in which skin substitutes were flagged', 'tables/k_tradeoff_by_year.csv')
g22 = T[T.t == 2022].share_of_positive_growth_captured
add('tr.y2022.min_growth_captured', g22.min(), 'frac', 'Min growth captured across approaches, 2022', 'tables/k_tradeoff_by_year.csv'); add('tr.y2022.max_growth_captured', g22.max(), 'frac', 'Max growth captured across approaches, 2022', 'tables/k_tradeoff_by_year.csv')
add('tr.cgr.sens_ratio_vs_code', T[T.approach == AP['cgr']].O1_doubling_class_sens.mean() / T[T.approach == AP['code']].O1_doubling_class_sens.mean(), 'num', 'Growth screen / code rule mean sensitivity ratio', 'tables/k_tradeoff_by_year.csv', dec=1)
add('tr.cgr.burden_ratio_vs_code', T[T.approach == AP['cgr']].units_flagged.mean() / T[T.approach == AP['code']].units_flagged.mean(), 'num', 'Growth screen / code rule mean units flagged ratio', 'tables/k_tradeoff_by_year.csv', dec=1)
cg = T[T.approach == AP['cgr']]
add('tr.cgr.share_single_code_flags', cg.n_flagged_single_code_classes.sum() / cg.units_flagged.sum(), 'frac', 'Share of growth-screen class flags (pooled over 2020-2023) that are single-code classes', 'tables/k_tradeoff_by_year.csv', dec=0)
# ---------------- 2024 applied demonstration ----------------
wk = json.load(open('tables/watchlist_key_numbers.json'))
for k, kind, d_ in [('n_watch_nonlab_codes', 'count', 'Non-lab codes flagged, 2024'), ('n_watch_skin_codes', 'count', 'Skin codes flagged, 2024'), ('n_watch_other_codes', 'count', 'Other non-lab codes flagged, 2024'),
                    ('n_watch_lab_codes', 'count', 'Lab codes flagged, 2024'), ('watch_nonlab_allowed_2024_M', 'usdM', 'Spending in non-lab flags, 2024'), ('watch_skin_allowed_2024_M', 'usdM', 'Spending in skin flags, 2024'),
                    ('watch_other_allowed_2024_M', 'usdM', 'Spending in other flags, 2024'), ('watch_lab_allowed_2024_M', 'usdM', 'Spending in lab flags, 2024'), ('n_new_codes_nonlab', 'count', 'New codes among 2024 non-lab flags'),
                    ('n_2023_flags', 'count', 'Codes flagged with 2023 data'), ('n_2023_flags_reflagged_2024', 'count', 'Codes flagged in both 2023 and 2024'),
                    ('median_top10_share_skin', 'frac', 'Median top-10 provider share, skin flags'), ('median_top10_share_other', 'frac', 'Median top-10 provider share, other flags')]:
    add('wl.' + k, wk[k], kind, d_, 'tables/watchlist_key_numbers.json')
WL = pd.read_csv('tables/j_watchlist_2024_nonlab_codes.csv', dtype={'unit': str}); WL['has'] = WL.n_reported_npis.fillna(0) > 0; H = WL[WL.has]
for s_ in ('skin', 'other'):
    add(f'wl.n_with_provider_rows_{s_}', (H.stratum == s_).sum(), 'count', f'{s_} flagged codes with any provider-file rows', 'tables/j_watchlist_2024_nonlab_codes.csv')
    add(f'wl.median_coverage_{s_}', H[H.stratum == s_].provider_file_coverage.median(), 'frac', f'Median provider-file coverage, {s_} flags with rows', 'tables/j_watchlist_2024_nonlab_codes.csv')
add('wl.dollar_coverage_all', (H.provider_file_coverage * H.allowed_2024_M).sum() / WL.allowed_2024_M.sum(), 'frac', 'Provider-file coverage across all 52 codes (dollar-weighted)', 'tables/j_watchlist_2024_nonlab_codes.csv')
# ---------------- worked example: pooled vs weighted concentration (skin class, 2021) ----------------
EX = 2021; x = conc[(conc.year == EX) & (conc.cls == 'Skin substitute products')].copy().sort_values('allowed', ascending=False)
x['share'] = x.allowed / x.allowed.sum(); x['contrib'] = x.share * x.hhi
add('ex.n_codes', len(x), 'count', f'Skin codes in worked example ({EX})', 'data/concentration_by_code_year.csv')
add('ex.wmean_hhi', x.contrib.sum(), 'count', f'Weighted mean member-code HHI, skin {EX}', 'data/concentration_by_code_year.csv')
add('ex.pooled_hhi', fsk.set_index('year').loc[EX, 'hhi'], 'count', f'Pooled HHI, skin {EX}', 'tables/f_skin_category_by_year.csv')
add('ex.n_codes_hhi_ge1500', int((x.hhi >= 1500).sum()), 'count', f'Skin codes with own HHI >= 1500, {EX}', 'data/concentration_by_code_year.csv')
add('ex.share_spend_codes_hhi_ge1500', x[x.hhi >= 1500].share.sum(), 'frac', f'Share of skin class spending in codes with HHI >= 1500, {EX}', 'data/concentration_by_code_year.csv')
top = x.head(5); EXR = []
for r in top.itertuples():
    EXR.append({'HCPCS': r.HCPCS_Cd, 'Allowed, $M': f'{r.allowed/1e6:.1f}', 'Share of class spending, %': f'{r.share*100:.1f}', 'Top state': r.top_state, 'Top-state share, %': f'{r.top1_share*100:.1f}',
                'Code state HHI': f'{r.hhi:.0f}', 'Share x HHI': f'{r.contrib:.0f}'})
rest = x.iloc[5:]
EXR.append({'HCPCS': f'Other {len(rest)} codes', 'Allowed, $M': f'{rest.allowed.sum()/1e6:.1f}', 'Share of class spending, %': f'{rest.share.sum()*100:.1f}', 'Top state': '—', 'Top-state share, %': '—',
            'Code state HHI': '—', 'Share x HHI': f'{rest.contrib.sum():.0f}'})
EXR.append({'HCPCS': 'Class total', 'Allowed, $M': f'{x.allowed.sum()/1e6:.1f}', 'Share of class spending, %': '100.0', 'Top state': '—', 'Top-state share, %': '—',
            'Code state HHI': f"Pooled: {fsk.set_index('year').loc[EX,'hhi']:.0f}", 'Share x HHI': f'Weighted: {x.contrib.sum():.0f}'})
# illustrative toy: four equal-spend products, each billed entirely in a different state
add('toy.n_products', 4, 'count', 'Toy example: products, each in one distinct state with equal spend', 'Appendix worked example', 'illustrative')
add('toy.code_hhi', 10000, 'count', 'Toy: each product HHI (100% in one state)', 'Appendix worked example', 'illustrative')
add('toy.pooled_hhi', 4 * (0.25 ** 2) * 10000, 'count', 'Toy: pooled HHI with four states at 25%', 'Appendix worked example', 'illustrative')
add('toy.state_share', 0.25, 'frac', 'Toy: each state share of pooled spending', 'Appendix worked example', 'illustrative', 0)
# ---------------- exhibit tables (every numeric cell registered) ----------------
def P(v, d=1): return '—' if pd.isna(v) else f'{v*100:.{d}f}%'
SM = T.groupby('approach', sort=False).mean(numeric_only=True)
LAB = {'code': 'Prespecified code rule (codes)', 'cpre': 'Prespecified class rule (classes)', 'cgr': 'Secondary class growth screen (classes)', 'cw': 'Exploratory weighted-HHI rule (classes)'}
STAT = {'code': 'Prespecified (primary)', 'cpre': 'Prespecified', 'cgr': 'Prespecified secondary', 'cw': 'Exploratory (post hoc)'}
EXH = {}
rows = []
for a, lab in AP.items():
    s, d = SM.loc[lab], T[T.approach == lab]
    rows.append({'Analysis status': STAT[a], 'Approach (unit flagged)': LAB[a], 'Units flagged per year, mean (range)': f"{s.units_flagged:.1f} ({d.units_flagged.min():.0f}-{d.units_flagged.max():.0f})",
                 'Single-code classes among flags, mean per year': '—' if a == 'code' else f'{s.n_flagged_single_code_classes:.1f}',
                 'Doubling outcome, sensitivity, %': f'{s.O1_doubling_class_sens*100:.1f}', 'Doubling outcome, PPV, %': f'{s.O1_doubling_class_ppv*100:.1f}',
                 'Top-decile outcome, sensitivity, %': f'{s.O2_top_decile_increase_class_sens*100:.1f}', 'Top-decile outcome, PPV, %': f'{s.O2_top_decile_increase_class_ppv*100:.1f}',
                 'Growth captured, %': f'{s.share_of_positive_growth_captured*100:.1f}', 'Growth captured excluding skin substitutes, %': f'{s.share_of_positive_growth_captured_excl_skin*100:.1f}',
                 'Share of 2024 skin-substitute spending captured, %': f'{s.skin_2024_captured*100:.1f}'})
EXH['table1_tradeoff'] = pd.DataFrame(rows)
rows = []
for r in T.itertuples():
    a = [k for k, v in AP.items() if v == r.approach][0]
    rows.append({'Flag year': str(r.t), 'Approach': LAB[a], 'Eligible units': f'{r.eligible_units}', 'Units flagged': f'{r.units_flagged}', 'Named classes flagged': f'{r.n_flagged_named_classes}', 'Single-code classes flagged': f'{r.n_flagged_single_code_classes}',
                 'Flagged spending at flag year, $M': f'{r.flagged_spend_t_M:.0f}', 'Doubling outcome classes, n': f'{r.O1_doubling_n_classes}',
                 'Doubling outcome, sensitivity, %': f'{r.O1_doubling_class_sens*100:.1f}', 'Doubling outcome, PPV, %': f'{r.O1_doubling_class_ppv*100:.1f}',
                 'Top-decile outcome, sensitivity, %': f'{r.O2_top_decile_increase_class_sens*100:.1f}', 'Top-decile outcome, PPV, %': f'{r.O2_top_decile_increase_class_ppv*100:.1f}',
                 'Growth captured, %': f'{r.share_of_positive_growth_captured*100:.1f}', 'Growth captured excluding skin substitutes, %': f'{r.share_of_positive_growth_captured_excl_skin*100:.1f}'})
EXH['A2_by_year'] = pd.DataFrame(rows)
def pct0(x): return '—' if pd.isna(x) else f'{x*100:.0f}'
def wrow(r): return {'HCPCS': r.unit, 'Description': r.plain_description.replace('…', '')[:40], '2023 allowed, $M': f'{r.allowed_2023_M:.1f}', '2024 allowed, $M': f'{r.allowed_2024_M:.1f}',
                     'Growth, %': 'New code' if r.new_unit else f'{r.growth_pct:.0f}', 'State HHI': f'{r.state_hhi:.0f}' if pd.notna(r.state_hhi) else 'Suppressed', 'Rendering providers': f'{r.national_providers:.0f}',
                     'Provider-file coverage, %': pct0(r.provider_file_coverage) if r.has else 'No rows', 'Top-10 share of provider-file spending, %': pct0(r.top10_provider_share) if r.has else '—'}
EXH['table2_watchlist_top'] = pd.DataFrame([wrow(r) for r in WL[WL.stratum == 'skin'].head(5).itertuples()] + [wrow(r) for r in WL[WL.stratum == 'other'].head(5).itertuples()])
EXH['A3_watchlist_all'] = pd.DataFrame([wrow(r) for r in WL.itertuples()])
f = pd.read_csv('tables/f_lookback_flags_2021_nonlab.csv', dtype={'HCPCS_Cd': str})
CAT = {'Skin substitute product': 'Skin substitute', 'Drug (Part B, physician-billed)': 'Part B drug', 'Professional/procedural': 'Procedure/service', 'Supply/DME/other': 'Supply/other'}
EXH['A1_flags_2021'] = pd.DataFrame([{'HCPCS': r.HCPCS_Cd, 'Category': CAT.get(r.category, r.category), '2021 allowed, $M': f'{r.allowed/1e6:.1f}', 'Growth vs 2020, %': 'New code' if r.growth == float('inf') else f'{r.growth*100:.0f}',
                                      'State HHI': f'{r.hhi:.0f}', 'Rendering providers': f'{r.nat_provs:.0f}', '2024 allowed, $M': f'{r.allowed_2024/1e6:.1f}'} for r in f.itertuples()])
EXH['A5_worked_example'] = pd.DataFrame(EXR)
import re
NUM = re.compile(r'-?\d[\d,]*\.?\d*')
for name, df in EXH.items():
    df.to_csv(f'tables/exhibits/{name}.csv', index=False)
    for i, row in df.iterrows():
        for c, v in row.items():
            for j, m_ in enumerate(NUM.findall(str(v))):
                if c in ('HCPCS', 'Description') or (c == 'Flag year'): continue
                add(f'exh.{name}.r{i}.{c}.{j}', float(m_.replace(',', '')), 'num', f'{name} row {i} column {c}', f'tables/exhibits/{name}.csv', dec=len(m_.split('.')[1]) if '.' in m_ else 0, display=m_)
# store values to 12 significant digits so reruns are byte-identical despite floating-point summation order
for r in R:
    if isinstance(r['value'], float) and r['value'] == r['value']: r['value'] = float(f"{r['value']:.12g}")
M = pd.DataFrame(R); assert M.id.is_unique
M.to_csv('tables/master_results.csv', index=False)
json.dump({r['id']: r for r in R}, open('tables/master_results.json', 'w'), indent=1, default=float)
print(len(M), 'statistics;', (M.type.value_counts().to_dict()))
