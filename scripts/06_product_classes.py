"""Product-class grouping, class-level look-back validation, and a current (2024) watchlist.
Classes: skin-substitute products; drug/biologic classes keyed on HCPCS descriptions (molecule names), so a molecule's
successor codes, biosimilars and new J-codes stay in one class; lab families (PLA, molecular 81xxx, MAAA, other lab) kept as
a separate stratum; named service families (e.g. extended ECG monitoring). Codes not matched remain their own class.
The prespecified rule (spend >= $10M; growth >= 50% or new; state HHI >= 1500 or <= 100 national rendering providers) is applied
unchanged to class totals. Class provider count = sum over member codes (upper bound; a provider billing two codes counts twice).
Exploratory (not prespecified): class concentration = spend-weighted mean of member-code HHI."""
import pandas as pd, numpy as np, json, re
m = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str})
g = pd.read_pickle('data/geo_all.pkl')
nprov = g[g.Rndrng_Prvdr_Geo_Lvl == 'National'].groupby(['year', 'HCPCS_Cd']).Tot_Rndrng_Prvdrs.sum().rename('nat_provs')
m = m.join(nprov, on=['year', 'HCPCS_Cd'])
st = pd.read_csv('data/state_by_code_year.csv', dtype={'HCPCS_Cd': str})
DRUG = [  # (class, keywords) first match wins
 ('Retinal intravitreal agents (anti-VEGF, complement)', ['aflibercept', 'ranibizumab', 'faricimab', 'brolucizumab', 'pegcetacoplan, intravitreal', 'avacincaptad']),
 ('CAR-T cell therapies', ['autoleucel', 'cabtagene', 'tisagenlecleucel']),
 ('Bispecific T-cell engagers', ['teclistamab', 'talquetamab', 'elranatamab', 'epcoritamab', 'glofitamab', 'mosunetuzumab', 'blinatumomab', 'tarlatamab', 'tebentafusp']),
 ('Antibody-drug conjugates', ['vedotin', 'deruxtecan', 'govitecan', 'emtansine', 'ozogamicin', 'tesirine', 'mafodotin', 'soravtansine']),
 ('Immune checkpoint inhibitors', ['pembrolizumab', 'nivolumab', 'atezolizumab', 'durvalumab', 'ipilimumab', 'cemiplimab', 'avelumab', 'dostarlimab', 'tremelimumab', 'retifanlimab', 'toripalimab', 'tislelizumab']),
 ('Myeloma agents', ['daratumumab', 'carfilzomib', 'bortezomib', 'isatuximab', 'elotuzumab']),
 ('Anti-amyloid antibodies', ['lecanemab', 'aducanumab', 'donanemab']),
 ('Immune globulins', ['immune globulin', 'immune glob']),
 ('Botulinum toxins', ['botulinumtoxin', 'toxina', 'toxinb']),
 ('Bone/osteoporosis agents', ['denosumab', 'romosozumab', 'zoledronic', 'teriparatide', 'abaloparatide', 'ibandronate']),
 ('Complement and FcRn inhibitors', ['eculizumab', 'ravulizumab', 'efgartigimod', 'rozanolixizumab', 'pegcetacoplan', 'sutimlimab']),
 ('MS infusion therapies', ['ocrelizumab', 'natalizumab', 'ublituximab', 'alemtuzumab', 'ofatumumab']),
 ('Respiratory biologics', ['omalizumab', 'mepolizumab', 'benralizumab', 'tezepelumab', 'reslizumab']),
 ('Immunology biologics (TNF, IL, integrin, T-cell)', ['abatacept', 'infliximab', 'tocilizumab', 'golimumab', 'certolizumab', 'vedolizumab', 'ustekinumab', 'risankizumab', 'guselkumab', 'tildrakizumab', 'secukinumab', 'mirikizumab', 'sarilumab', 'anifrolumab', 'belimumab']),
 ('Hematology (factors, ESAs, G-CSF, TPO)', ['factor', 'antihemophilic', 'emicizumab', 'luspatercept', 'romiplostim', 'epoetin', 'darbepoetin', 'filgrastim', 'efbemalenograstim', 'eflapegrastim']),
 ('siRNA therapies', ['inclisiran', 'vutrisiran', 'patisiran', 'givosiran', 'lumasiran']),
 ('Hormonal and somatostatin analogs', ['lanreotide', 'octreotide', 'leuprolide', 'degarelix', 'triptorelin', 'goserelin', 'fulvestrant']),
 ('Vaccines', ['vaccine', 'vac ', 'sarscov2 vac', 'sarscv2 vac', 'toxoid']),
 ('Radiopharmaceuticals and imaging agents', ['tc-99m', 'tc 99m', 'technetium', 'f-18', 'f18', 'fluorine', 'gallium', 'ga-68', 'lutetium', 'radium', 'flortaucipir', 'florbetapir', 'flutemetamol', 'florbetaben', 'piflufolastat', 'rubidium', 'contrast', 'gadolinium', 'regadenoson']),
]
SVC = [('Extended ambulatory ECG monitoring', lambda c: c in {f'9324{i}' for i in range(1, 9)}),
       ('Mobile cardiac telemetry and event monitoring', lambda c: c in {'93224', '93225', '93226', '93227', '93228', '93229', '93268', '93270', '93271', '93272'}),
       ('Remote physiologic monitoring', lambda c: c in {'99453', '99454', '99457', '99458', '99091', '99445'}),
       ('Remote therapeutic monitoring', lambda c: c in {'98975', '98976', '98977', '98978', '98980', '98981', '98984', '98985', '98986'}),
       ('Chronic and principal care management', lambda c: c in {'99487', '99489', '99490', '99491', '99439', '99424', '99425', '99426', '99427', '99437', 'G0506', 'G0556', 'G0557', 'G0558'}),
       ('Skin-substitute application procedures', lambda c: c in {str(x) for x in range(15271, 15279)}),
       ('Office/outpatient E/M visits', lambda c: c in {'99202', '99203', '99204', '99205', '99211', '99212', '99213', '99214', '99215'}),
       ('Cardiac device remote interrogation', lambda c: c in {'93294', '93295', '93296', '93297', '93298', 'G2066'}),
       ('Psychotherapy', lambda c: c in {'90832', '90834', '90837', '90838', '90833', '90836', '90846', '90847', '90853'})]
def classify(code, desc, cat):
    d = str(desc).lower()
    if cat == 'Skin substitute product': return 'Skin substitute products', 'skin'
    if cat == 'PLA lab (U)': return 'PLA proprietary lab tests (####U)', 'lab'
    if cat == 'Other lab':
        if code.endswith('M'): return 'Multianalyte assays with algorithm (####M)', 'lab'
        if code[:3] in ('812', '813', '814', '815', '816') or code[:3] == '811': return 'Molecular pathology and genomic panels (81xxx)', 'lab'
        return 'Other laboratory (8xxxx)', 'lab'
    for name, f in SVC:
        if f(code): return name, 'other'
    if cat.startswith('Drug') or code[0] in 'JQA9':
        for name, kws in DRUG:
            if any(k in d for k in kws): return name, 'other'
    return f'{code} (unclassified, own class)', 'other'
info = m.sort_values('year').groupby('HCPCS_Cd').agg(desc=('desc', 'last'), category=('category', 'last'))
cl = info.apply(lambda r: pd.Series(classify(r.name, r.desc, r.category), index=['cls', 'stratum']), axis=1)
info = info.join(cl); info.to_csv('tables/i_code_to_class_map.csv')
m = m.join(info[['cls', 'stratum']], on='HCPCS_Cd')
named = info[~info.cls.str.contains('own class')]
print('named classes', named.cls.nunique(), 'codes in named classes', len(named))
# class-year aggregates
st = st.join(info.cls, on='HCPCS_Cd')
def hhi(s): sh = s / s.sum(); return (sh ** 2).sum() * 1e4
cy = m.groupby(['cls', 'year']).agg(allowed=('allowed', 'sum'), nat_provs=('nat_provs', 'sum'), n_codes=('HCPCS_Cd', 'nunique'), stratum=('stratum', 'first')).reset_index()
sh = st.groupby(['cls', 'year', 'state']).allowed.sum().reset_index()
ch = sh.groupby(['cls', 'year']).allowed.apply(hhi).rename('hhi')
tops = sh.groupby(['cls', 'year']).apply(lambda x: pd.Series({'top_state': x.loc[x.allowed.idxmax(), 'state'], 'top_state_share': x.allowed.max() / x.allowed.sum()}))
cy = cy.join(ch, on=['cls', 'year']).join(tops, on=['cls', 'year'])
m['w'] = m.allowed * m.hhi
wh = m.groupby(['cls', 'year']).w.sum() / m.groupby(['cls', 'year']).allowed.sum()
cy = cy.join(wh.rename('wmean_code_hhi'), on=['cls', 'year'])
CA = cy.pivot_table(index='cls', columns='year', values='allowed').fillna(0)
A = m.pivot_table(index='HCPCS_Cd', columns='year', values='allowed').fillna(0)
cy.to_csv('tables/i_class_by_year.csv', index=False)
def unit_feats(level, t):
    if level == 'class':
        d = cy[cy.year == t].set_index('cls'); P = CA
    else:
        d = m[m.year == t].set_index('HCPCS_Cd'); P = A
    prev = P[t - 1].reindex(d.index).fillna(0) if (t - 1) in P else pd.Series(0, index=d.index)
    d = d.copy(); d['prev'] = prev
    d['growth'] = np.where(prev > 0, d.allowed / prev.replace(0, np.nan) - 1, np.inf)
    d['allowed_2024'] = P[2024].reindex(d.index).fillna(0)
    return d
def flag(d, conc='hhi'):
    return (d.allowed >= 10e6) & (d.growth >= 0.5) & ((d[conc] >= 1500) | (d.nat_provs <= 100))
K = {}; rows = []
for t in (2020, 2021, 2022, 2023):
    for level in ('code', 'class'):
        d = unit_feats(level, t); d = d[d.stratum != 'lab']
        for rule, f in [('composite', flag(d)), ('growth_only', (d.allowed >= 10e6) & (d.growth >= 0.5))] + ([('composite_wmean_hhi_exploratory', flag(d, 'wmean_code_hhi'))] if level == 'class' else []):
            sel = d[f]; base = d[d.allowed >= 10e6]; un = base[~f.reindex(base.index)]
            # coverage of later spending: classes that at least doubled t->2024 (class-level outcome, same for both levels)
            ct = unit_feats('class', t); ct = ct[(ct.stratum != 'lab') & (ct.allowed >= 10e6) & (ct.allowed_2024 >= 2 * ct.allowed)]
            if level == 'class': covered = ct.allowed_2024[ct.index.isin(sel.index)].sum()
            else:
                mm = info[info.cls.isin(ct.index)]
                covered = A.loc[A.index.isin(sel.index) & A.index.isin(mm.index), 2024].sum()
            skin24 = CA.loc['Skin substitute products', 2024]
            skin_cov = (skin24 if 'Skin substitute products' in sel.index else 0) if level == 'class' else A.loc[A.index.isin(sel.index) & A.index.isin(info[info.stratum == 'skin'].index), 2024].sum()
            rows.append({'t': t, 'level': level, 'rule': rule, 'n_flagged': len(sel), 'flagged_allowed_t_M': sel.allowed.sum() / 1e6,
                         'flagged_allowed_2024_M': sel.allowed_2024.sum() / 1e6,
                         'flagged_ratio_2024_to_t': sel.allowed_2024.sum() / sel.allowed.sum() if len(sel) else np.nan,
                         'unflagged_ratio_2024_to_t': un.allowed_2024.sum() / un.allowed.sum(),
                         'n_doubling_classes': len(ct), 'doubling_classes_2024_M': ct.allowed_2024.sum() / 1e6,
                         'coverage_of_doubling_class_2024_spend': covered / ct.allowed_2024.sum(),
                         'coverage_of_2024_skin_spend': skin_cov / skin24,
                         'skin_class_flagged': ('Skin substitute products' in sel.index) if level == 'class' else None})
perf = pd.DataFrame(rows); perf.to_csv('tables/i_class_vs_code_lookback.csv', index=False)
print(perf.round(3).to_string())
K['lookback'] = perf.round(3).to_dict('records')
skin = cy[cy.cls == 'Skin substitute products'][['year', 'allowed', 'hhi', 'wmean_code_hhi', 'nat_provs', 'n_codes']]
K['skin_class'] = skin.round(1).to_dict('records'); print(skin)
for t in (2021, 2022, 2023):
    d = unit_feats('class', t); d = d[d.stratum != 'lab']
    K[f'class_flags_{t}'] = d[flag(d)].sort_values('allowed', ascending=False)[['allowed', 'growth', 'hhi', 'nat_provs', 'allowed_2024']].round(3).reset_index().to_dict('records')
    K[f'class_flags_wmean_{t}'] = d[flag(d, 'wmean_code_hhi')].index.tolist()
# ---- current watchlist: apply rule to 2024 (growth 2023->2024) at code and class level; labs reported separately
def wl(level):
    d = unit_feats(level, 2024)
    out = d[flag(d)].copy(); out['level'] = level
    if level == 'class':
        out['also_wmean_flag'] = flag(d, 'wmean_code_hhi').reindex(out.index)
        out['desc'] = out.index; out['class'] = out.index
    else:
        out['desc'] = info.desc.reindex(out.index); out['class'] = info.cls.reindex(out.index)
        out['top_state_share'] = out['top1_share']
    out['growth_pct'] = np.where(np.isinf(out.growth), np.nan, out.growth * 100)
    out['new_unit'] = np.isinf(out.growth)
    return out
W = pd.concat([wl('code'), wl('class')])
# exploratory class-level adds (weighted member HHI) shown separately
d = unit_feats('class', 2024); Wx = d[flag(d, 'wmean_code_hhi') & ~flag(d)].copy()
Wx['level'] = 'class (exploratory weighted-HHI only)'; Wx['desc'] = Wx.index; Wx['class'] = Wx.index
Wx['growth_pct'] = np.where(np.isinf(Wx.growth), np.nan, Wx.growth * 100); Wx['new_unit'] = np.isinf(Wx.growth)
W = pd.concat([W, Wx])
W.index.name = 'unit'
W.to_csv('data/watchlist_2024_raw.csv')
print(W[['level', 'stratum', 'class', 'allowed', 'prev', 'growth_pct', 'hhi', 'nat_provs', 'top_state', 'top_state_share']].sort_values(['level', 'allowed'], ascending=[True, False]).to_string())
json.dump(K, open('tables/class_key_numbers.json', 'w'), indent=1, default=str)
