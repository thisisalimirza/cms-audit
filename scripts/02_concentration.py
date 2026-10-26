"""Geographic concentration (HHI, top-state share, # states) for high-spend codes, by category."""
import pandas as pd, numpy as np, re
nat = pd.read_csv('data/national_by_code_year.csv', dtype={'HCPCS_Cd': str})
st = pd.read_csv('data/state_by_code_year.csv', dtype={'HCPCS_Cd': str})
# 50 states + DC only (exclude territories/'Foreign'/unknown) for state counts
STATES50 = set(pd.read_csv('data/state_by_code_year.csv').state.unique())
def cat(c, drug):
    if re.fullmatch(r'\d{4}U', c): return 'PLA lab (U)'
    if re.fullmatch(r'\d{4}M', c) or re.fullmatch(r'8\d{4}', c) or c.startswith('G04') and False: return 'Other lab'
    if re.fullmatch(r'Q4[1-3]\d\d', c) or re.fullmatch(r'A2\d{3}', c): return 'Skin substitute product'
    if drug == 'Y': return 'Drug (Part B, physician-billed)'
    if c[0] in 'ABEKL': return 'Supply/DME/other'
    return 'Professional/procedural'
nat['category'] = [cat(c, d) for c, d in zip(nat.HCPCS_Cd, nat.drug)]
nat.to_csv('data/national_by_code_year.csv', index=False)
def conc(g):
    s = g.allowed.clip(lower=0); tot = s.sum()
    sh = s / tot if tot > 0 else s * 0
    srt = sh.sort_values(ascending=False)
    return pd.Series({'state_allowed_sum': tot, 'hhi': (sh**2).sum() * 10000,
        'top1_share': srt.iloc[0] if len(srt) else np.nan, 'top2_share': srt.iloc[:2].sum(),
        'top_state': g.state.loc[s.idxmax()] if tot > 0 else None, 'n_states': int((s > 0).sum())})
c = st.groupby(['year', 'HCPCS_Cd']).apply(conc, include_groups=False).reset_index()
m = nat.merge(c, on=['year', 'HCPCS_Cd'], how='left')
m['state_coverage'] = m.state_allowed_sum / m.allowed  # share of national $ visible at state level (suppression)
m.to_csv('data/concentration_by_code_year.csv', index=False)
y = m[m.year == m.year.max()]
flag = y[(y.allowed >= 50e6) & ((y.hhi >= 2500) | (y.n_states <= 10))].sort_values('allowed', ascending=False)
flag.to_csv('data/flagged_latest.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 40)
print('latest', m.year.max(), 'codes >=$50M:', (y.allowed >= 50e6).sum(), 'flagged:', len(flag))
print(flag[['HCPCS_Cd','category','desc','allowed','hhi','top1_share','top_state','n_states','state_coverage']].to_string())
print(flag.groupby('category').allowed.agg(['size','sum']))
