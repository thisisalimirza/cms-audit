"""Prospective-simulation (look-back) test of a prespecified early-warning rule using only data available through year t.
PRESPECIFIED PRIMARY RULE (fixed before looking at outcomes; documented in README):
  At year t, among codes with national allowed >= $10M in t:
   G (rapid growth): allowed_t / allowed_{t-1} - 1 >= 50%   (codes absent in t-1 count as new => growth satisfied)
   C (concentration): state HHI_t >= 1,500  OR  national rendering providers_t <= 100   (provider-count proxy for
     provider concentration, because provider-level files for every code-year were not downloaded)
  Composite = spend & G & C. Variants: growth-only (spend & G), concentration-only (spend & C).
  Lab/PLA codes (8xxxx, ####U, ####M) are reported as a separate stratum because their concentration is structural.
Outcome: subsequent spending through 2024 (data not used for flagging)."""
import pandas as pd, numpy as np, json, itertools
m = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str})
g = pd.read_pickle('data/geo_all.pkl')
nprov = g[g.Rndrng_Prvdr_Geo_Lvl == 'National'].groupby(['year', 'HCPCS_Cd']).Tot_Rndrng_Prvdrs.sum().rename('nat_provs')
m = m.join(nprov, on=['year', 'HCPCS_Cd'])
LAB = {'PLA lab (U)', 'Other lab'}
m['stratum'] = np.where(m.category.isin(LAB), 'lab', np.where(m.category == 'Skin substitute product', 'skin', 'other'))
A = m.pivot_table(index='HCPCS_Cd', columns='year', values='allowed').fillna(0)
info = m.sort_values('year').groupby('HCPCS_Cd').agg(category=('category', 'last'), stratum=('stratum', 'last'), desc=('desc', 'last'))
skin_codes = set(info[info.stratum == 'skin'].index)
def features(t):
    d = m[m.year == t].set_index('HCPCS_Cd')[['allowed', 'hhi', 'nat_provs', 'n_states', 'top1_share']].copy()
    prev = A[t - 1].reindex(d.index).fillna(0) if t - 1 in A else 0
    d['growth'] = np.where(prev > 0, d.allowed / prev.replace(0, np.nan) - 1, np.inf)
    d['allowed_2024'] = A[2024].reindex(d.index).fillna(0)
    return d.join(info)
def flags(d, spend=10e6, growth=0.5, hhi=1500, provs=100):
    s = d.allowed >= spend; G = d.growth >= growth; C = (d.hhi >= hhi) | (d.nat_provs <= provs)
    return {'composite': s & G & C, 'growth_only': s & G, 'concentration_only': s & C}
K = {}; rows = []
for t in [2020, 2021, 2022, 2023]:
    d = features(t); F = flags(d)
    base = d[d.allowed >= 10e6]
    for rule, f in F.items():
        for strat in ['non-lab', 'lab']:
            sel = d[f & ((d.stratum == 'lab') if strat == 'lab' else (d.stratum != 'lab'))]
            un = base[~f.reindex(base.index) & ((base.stratum == 'lab') if strat == 'lab' else (base.stratum != 'lab'))]
            rows.append({'t': t, 'rule': rule, 'stratum': strat, 'n_flagged': len(sel), 'n_skin_flagged': int((sel.stratum == 'skin').sum()),
                         'flagged_allowed_t_M': sel.allowed.sum() / 1e6, 'flagged_allowed_2024_M': sel.allowed_2024.sum() / 1e6,
                         'flagged_ratio_2024_to_t': sel.allowed_2024.sum() / sel.allowed.sum() if len(sel) else np.nan,
                         'flagged_median_code_ratio': (sel.allowed_2024 / sel.allowed).median() if len(sel) else np.nan,
                         'unflagged_ratio_2024_to_t': un.allowed_2024.sum() / un.allowed.sum(),
                         'unflagged_median_code_ratio': (un.allowed_2024 / un.allowed).median(),
                         'share_flagged_doubling': ((sel.allowed_2024 / sel.allowed) >= 2).mean() if len(sel) else np.nan,
                         'share_unflagged_doubling': ((un.allowed_2024 / un.allowed) >= 2).mean(),
                         'n_unflagged_ge10M': len(un)})
    if t in (2021, 2022):
        fl = d[F['composite'] & (d.stratum != 'lab')].sort_values('allowed', ascending=False)
        fl[['category', 'desc', 'allowed', 'growth', 'hhi', 'nat_provs', 'n_states', 'allowed_2024']].to_csv(f'tables/f_lookback_flags_{t}_nonlab.csv')
        sk = d[d.stratum == 'skin']
        later_skin = A.loc[A.index.isin(skin_codes), 2024]
        K[f'lookback_{t}'] = {
            'n_composite_nonlab': int(len(fl)), 'n_composite_skin': int((fl.stratum == 'skin').sum()),
            'skin_codes_flagged': fl[fl.stratum == 'skin'].index.tolist(),
            'nonskin_nonlab_flagged': fl[fl.stratum != 'skin'].index.tolist(),
            'n_skin_codes_ge10M_t': int((sk.allowed >= 10e6).sum()),
            'skin_flagged_allowed_t_M': round(fl[fl.stratum == 'skin'].allowed.sum() / 1e6, 1),
            'skin_flagged_allowed_2024_M': round(fl[fl.stratum == 'skin'].allowed_2024.sum() / 1e6, 1),
            'share_of_2024_skin_spend_in_flagged_codes': round(fl[fl.stratum == 'skin'].allowed_2024.sum() / later_skin.sum(), 3),
            'share_of_2024_skin_spend_in_codes_existing_at_t': round(later_skin[later_skin.index.isin(d.index)].sum() / later_skin.sum(), 3),
            'nonskin_flagged_ratio_2024_to_t': round(fl[fl.stratum != 'skin'].allowed_2024.sum() / max(fl[fl.stratum != 'skin'].allowed.sum(), 1), 2),
            'category_level_skin_allowed_t_M': round(sk.allowed.sum() / 1e6, 1),
            'category_level_skin_growth_t': round(sk.allowed.sum() / A.loc[A.index.isin(skin_codes), t - 1].sum() - 1, 3),
            'category_skin_hhi_t': None}
perf = pd.DataFrame(rows); perf.to_csv('tables/f_lookback_performance.csv', index=False)
# category-level screen: treat the skin-substitute product class as one unit (sum across codes) each year
st = pd.read_csv('data/state_by_code_year.csv', dtype={'HCPCS_Cd': str})
cat_rows = []
for t in range(2019, 2025):
    s = st[(st.year == t) & st.HCPCS_Cd.isin(skin_codes)].groupby('state').allowed.sum(); sh = s / s.sum()
    cat_rows.append({'year': t, 'allowed_M': A.loc[A.index.isin(skin_codes), t].sum() / 1e6, 'hhi': (sh ** 2).sum() * 1e4, 'top5_state_share': sh.sort_values().iloc[-5:].sum()})
cat = pd.DataFrame(cat_rows); cat['growth'] = cat.allowed_M.pct_change(); cat.to_csv('tables/f_skin_category_by_year.csv', index=False)
K['skin_category_by_year'] = cat.round(3).to_dict('records')
# sensitivity grid at t=2021 and 2022 (non-lab)
grid = []
for t in (2021, 2022):
    d = features(t)
    for sp, gr, hh, pv in itertools.product([5e6, 10e6, 25e6], [0.25, 0.5, 1.0], [1000, 1500, 2500], [50, 100, 250]):
        f = flags(d, sp, gr, hh, pv)['composite'] & (d.stratum != 'lab')
        sel = d[f]
        grid.append({'t': t, 'spend_M': sp / 1e6, 'growth': gr, 'hhi': hh, 'max_provs': pv, 'n_flagged': len(sel), 'n_skin': int((sel.stratum == 'skin').sum()),
                     'share_flagged_skin': (sel.stratum == 'skin').mean() if len(sel) else np.nan,
                     'share_flagged_doubling_by_2024': ((sel.allowed_2024 / sel.allowed) >= 2).mean() if len(sel) else np.nan})
grid = pd.DataFrame(grid); grid.to_csv('tables/g_sensitivity_grid.csv', index=False)
for t in (2021, 2022):
    gg = grid[grid.t == t]
    K[f'grid_{t}'] = {'n_combos': len(gg), 'combos_flagging_any_skin': int((gg.n_skin > 0).sum()), 'n_flagged_range': [int(gg.n_flagged.min()), int(gg.n_flagged.max())],
                      'n_skin_range': [int(gg.n_skin.min()), int(gg.n_skin.max())], 'median_share_flagged_skin': round(gg.share_flagged_skin.median(), 3)}
# suppression impact: HHI recomputed restricted to codes with >=90% state coverage
y = m[(m.year == 2024) & (m.allowed >= 50e6)]
K['suppression'] = {'n_ge50M_2024': int(len(y)), 'median_state_coverage': round(y.state_coverage.median(), 3),
                    'share_coverage_lt90': round((y.state_coverage < 0.9).mean(), 3),
                    'coverage_lt90_by_category': y[y.state_coverage < 0.9].category.value_counts().to_dict(),
                    'skin_median_state_coverage_2024': round(y[y.stratum == 'skin'].state_coverage.median(), 3),
                    'flagged_2024_robust_to_coverage_ge90': int(((y.hhi >= 2500) | (y.n_states <= 10))[y.state_coverage >= 0.9].sum()),
                    'flagged_2024_all': int(((y.hhi >= 2500) | (y.n_states <= 10)).sum())}
# 2019 reconciliation pieces
g19 = g[(g.year == 2019) & (g.Rndrng_Prvdr_Geo_Lvl == 'National') & g.HCPCS_Cd.isin(skin_codes)]
K['recon_2019'] = {'allowed_M': round(g19.allowed.sum() / 1e6, 1), 'paid_M': round(g19.paid.sum() / 1e6, 1),
                   'by_pos_paid_M': (g19.groupby('Place_Of_Srvc').paid.sum() / 1e6).round(1).to_dict(), 'n_codes': int(g19.HCPCS_Cd.nunique()),
                   'state_sum_paid_M': round(m[(m.year == 2019) & (m.stratum == 'skin')].state_allowed_sum.sum() / 1e6, 1)}
K['perf_summary'] = perf[(perf.rule == 'composite')].round(3).to_dict('records')
json.dump(K, open('tables/lookback_key_numbers.json', 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in K.items() if k != 'perf_summary'}, indent=1, default=str))
print(perf.round(2).to_string())
