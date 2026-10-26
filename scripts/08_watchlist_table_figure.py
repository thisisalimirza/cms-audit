"""Final 2024 watchlist table (+lab stratum), persistence of 2023 flags, and Figure 7 (watchlist + class vs code coverage)."""
import pandas as pd, numpy as np, json, re, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
W = pd.read_csv('data/watchlist_2024_raw.csv', dtype={'unit': str})
P = pd.read_csv('data/watchlist_provider_shares.csv', dtype={'unit': str})
m = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str})
first = m[m.allowed > 0].groupby('HCPCS_Cd').year.min()
info = pd.read_csv('tables/i_code_to_class_map.csv', dtype={'HCPCS_Cd': str}).set_index('HCPCS_Cd')
W = W.merge(P, on='unit', how='left')
def short(s):
    s = re.sub(r'\s*\(code may be used.*', '', str(s)); s = re.sub(r',? per square centimeter', ', per sq cm', s, flags=re.I)
    return s[:80] + ('…' if len(s) > 80 else '')
def caveat(r):
    c = []
    if r.level == 'code':
        fy = first.get(r.unit, np.nan)
        if fy >= 2023: c.append(f'New code (first billed in these files in {int(fy)}); growth reflects launch or recoding, not a change in existing use.')
        elif fy > 2019: c.append(f'Code first billed in {int(fy)}.')
    if r.stratum == 'skin':
        c.append('Skin-substitute product; CMS moved most products to a flat per-sq-cm supply rate in 2026 and LCD policy changed, so 2024 trends may not continue; product-level growth is partly code churn.')
    elif r.stratum == 'lab':
        c.append('Laboratory test; concentration usually reflects one performing laboratory rather than regional use.')
    elif str(r.unit)[0] in 'JQ' or 'own class' in str(r['class']) and str(r.unit)[0] in 'JQ':
        c.append('Drug or biologic; growth may reflect uptake of a new therapy, new indications, or coverage changes.')
    else:
        c.append('Service code; growth may reflect coverage, coding, or practice changes.')
    if r.level == 'code' and r.nat_provs <= 100: c.append('Met concentration criterion through the provider-count threshold.')
    if pd.notna(r.get('provider_file_allowed')) and r.allowed > 0 and r.provider_file_allowed / r.allowed < 0.5: c.append('Provider file reports under half of national dollars because of suppression.')
    if pd.isna(r.hhi): c.append('State rows suppressed; state HHI not computable.')
    return ' '.join(c)
W['plain_description'] = [short(d) if l == 'code' else u for d, l, u in zip(W.desc, W.level, W.unit)]
W['caveats'] = W.apply(caveat, axis=1)
W['first_year'] = W.unit.map(first)
W['provider_file_coverage'] = W.provider_file_allowed / W.allowed
cols = ['level', 'stratum', 'unit', 'plain_description', 'class', 'allowed_2024_M', 'allowed_2023_M', 'growth_pct', 'new_unit', 'state_hhi', 'top_state', 'top_state_share',
        'national_providers', 'n_reported_npis', 'top1_provider_share', 'top10_provider_share', 'provider_file_coverage', 'caveats']
W['allowed_2024_M'] = W.allowed / 1e6; W['allowed_2023_M'] = W.prev / 1e6; W['state_hhi'] = W.hhi; W['national_providers'] = W.nat_provs
W = W[cols].sort_values(['level', 'stratum', 'allowed_2024_M'], ascending=[True, True, False])
W.insert(0, 'rank_in_group', W.groupby(['level', 'stratum']).cumcount() + 1)
W.round(3).to_csv('tables/j_watchlist_2024.csv', index=False)
main = W[(W.level == 'code') & (W.stratum != 'lab')].sort_values('allowed_2024_M', ascending=False)
main.round(3).to_csv('tables/j_watchlist_2024_nonlab_codes.csv', index=False)
# persistence of 2023 flags
f23 = pd.read_csv('tables/i_class_vs_code_lookback.csv')
m = m.join(info[['cls', 'stratum']], on='HCPCS_Cd')
g = pd.read_pickle('data/geo_all.pkl'); npv = g[g.Rndrng_Prvdr_Geo_Lvl == 'National'].groupby(['year', 'HCPCS_Cd']).Tot_Rndrng_Prvdrs.sum().rename('np')
m = m.join(npv, on=['year', 'HCPCS_Cd']); A = m.pivot_table(index='HCPCS_Cd', columns='year', values='allowed').fillna(0)
def flags(t):
    d = m[(m.year == t) & (m.stratum != 'lab')].set_index('HCPCS_Cd'); pr = A[t - 1].reindex(d.index).fillna(0)
    gr = np.where(pr > 0, d.allowed / pr.replace(0, np.nan) - 1, np.inf)
    return set(d.index[(d.allowed >= 10e6) & (gr >= 0.5) & ((d.hhi >= 1500) | (d.np <= 100))])
s23, s24 = flags(2023), flags(2024)
K = {'n_watch_nonlab_codes': len(main), 'n_watch_skin_codes': int((main.stratum == 'skin').sum()), 'n_watch_other_codes': int((main.stratum == 'other').sum()),
     'n_watch_lab_codes': int(((W.level == 'code') & (W.stratum == 'lab')).sum()),
     'watch_nonlab_allowed_2024_M': round(main.allowed_2024_M.sum(), 1), 'watch_skin_allowed_2024_M': round(main[main.stratum == 'skin'].allowed_2024_M.sum(), 1),
     'watch_other_allowed_2024_M': round(main[main.stratum == 'other'].allowed_2024_M.sum(), 1),
     'watch_lab_allowed_2024_M': round(W[(W.level == 'code') & (W.stratum == 'lab')].allowed_2024_M.sum(), 1),
     'n_new_codes_nonlab': int(main.new_unit.sum()), 'n_2023_flags': len(s23), 'n_2023_flags_reflagged_2024': len(s23 & s24),
     'median_top10_share_skin': round(main[main.stratum == 'skin'].top10_provider_share.median(), 3),
     'median_top10_share_other': round(main[main.stratum == 'other'].top10_provider_share.median(), 3),
     'top10': main.head(10)[['unit', 'plain_description', 'allowed_2024_M', 'allowed_2023_M', 'growth_pct', 'state_hhi', 'national_providers', 'top10_provider_share']].round(3).to_dict('records'),
     'other_codes': main[main.stratum == 'other'][['unit', 'plain_description', 'allowed_2024_M', 'growth_pct', 'state_hhi', 'national_providers', 'top10_provider_share']].round(3).to_dict('records'),
     'class_level_flags_2024': W[W.level != 'code'][['level', 'unit', 'allowed_2024_M', 'growth_pct', 'state_hhi']].round(3).to_dict('records')}
json.dump(K, open('tables/watchlist_key_numbers.json', 'w'), indent=1, default=str)
print(json.dumps(K, indent=1, default=str))
# Figure 7
L = pd.read_csv('tables/i_class_vs_code_lookback.csv')
fig, ax = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={'width_ratios': [1.25, 1]})
top = main.head(15).iloc[::-1]
col = np.where(top.stratum == 'skin', '#b2182b', '#2166ac')
ax[0].barh(top.unit, top.allowed_2024_M, color=col)
for i, (v, g_, n) in enumerate(zip(top.allowed_2024_M, top.growth_pct, top.new_unit)):
    ax[0].text(v + 8, i, 'new code' if n else f'+{g_:.0f}%', va='center', fontsize=8)
ax[0].set_xlabel('2024 allowed amount, $ millions'); ax[0].set_title('A. Top 15 non-laboratory codes flagged in 2024', fontsize=10, loc='left')
ax[0].set_xlim(0, top.allowed_2024_M.max() * 1.18)
from matplotlib.patches import Patch
ax[0].legend(handles=[Patch(color='#b2182b', label='Skin-substitute product'), Patch(color='#2166ac', label='Other drug or service')], fontsize=8, loc='lower right', frameon=False)
for s in ('top', 'right'): ax[0].spines[s].set_visible(False); ax[1].spines[s].set_visible(False)
ts = [2020, 2021, 2022, 2023]
series = [('code', 'composite', 'Code level, prespecified rule', '#888888'), ('class', 'composite', 'Class level, prespecified rule', '#4d4d4d'),
          ('class', 'growth_only', 'Class level, spend + growth only', '#2166ac'), ('class', 'composite_wmean_hhi_exploratory', 'Class level, weighted code HHI (exploratory)', '#b2182b')]
w = 0.2
for k, (lv, ru, lab, c) in enumerate(series):
    v = [L[(L.t == t) & (L.level == lv) & (L.rule == ru)].coverage_of_2024_skin_spend.iloc[0] * 100 for t in ts]
    ax[1].bar(np.arange(4) + (k - 1.5) * w, v, w, color=c, label=lab)
ax[1].set_xticks(range(4)); ax[1].set_xticklabels(ts); ax[1].set_xlabel('Flag year t (data through t only)')
ax[1].set_ylabel('% of 2024 skin-substitute spending\nin units flagged at t'); ax[1].set_ylim(0, 112)
ax[1].set_title('B. Coverage of later skin-substitute spending', fontsize=10, loc='left'); ax[1].legend(fontsize=7.5, frameon=False, loc='upper left', bbox_to_anchor=(0, 1.0))
ax[1].set_ylim(0, 140); ax[1].set_yticks([0, 25, 50, 75, 100])
plt.tight_layout(); plt.savefig('figures/fig7_watchlist_and_class_coverage.png', dpi=200)
