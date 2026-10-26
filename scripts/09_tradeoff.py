"""Sensitivity vs review burden for three screening approaches (non-laboratory stratum), flag years 2020-2023.
Approaches:
  (1) code-level prespecified composite rule (spend >= $10M; growth >= 50% or new; state HHI >= 1500 or <= 100 national providers)
  (2) class-level growth screen (spend >= $10M and growth >= 50% or new; no concentration criterion)  [secondary; rule components]
  (3) class-level composite with spend-weighted mean member-code HHI  [EXPLORATORY, specified after seeing pooled results]
  (also reported: class-level prespecified composite with pooled state HHI)
Outcomes (evaluated with data after t only, through 2024), among non-lab units with >= $10M at t:
  O1 doubling: 2024 allowed >= 2 x allowed at t.   O2 top decile of absolute dollar increase t->2024.
Evaluated at class level (code rule detects a class if any member code is flagged) and at code level (class rules detect a
code if its class is flagged). PPV = share of flagged units (classes; for the code rule at class level, distinct classes
containing >= 1 flagged code) that are outcome units. Spending measures use the national geography files."""
import pandas as pd, numpy as np, json
m = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str})
g = pd.read_pickle('data/geo_all.pkl')
m = m.join(g[g.Rndrng_Prvdr_Geo_Lvl == 'National'].groupby(['year', 'HCPCS_Cd']).Tot_Rndrng_Prvdrs.sum().rename('nat_provs'), on=['year', 'HCPCS_Cd'])
info = pd.read_csv('tables/i_code_to_class_map.csv', dtype={'HCPCS_Cd': str}).set_index('HCPCS_Cd')
cy = pd.read_csv('tables/i_class_by_year.csv')
m = m.join(info[['cls', 'stratum']], on='HCPCS_Cd')
m = m[m.stratum != 'lab']; cy = cy[cy.stratum != 'lab']
A = m.pivot_table(index='HCPCS_Cd', columns='year', values='allowed').fillna(0)
CA = cy.pivot_table(index='cls', columns='year', values='allowed').fillna(0)
def feats(t, level):
    d = (cy[cy.year == t].set_index('cls') if level == 'class' else m[m.year == t].set_index('HCPCS_Cd')).copy()
    P = CA if level == 'class' else A
    prev = P[t - 1].reindex(d.index).fillna(0)
    d['growth'] = np.where(prev > 0, d.allowed / prev.replace(0, np.nan) - 1, np.inf)
    for y in range(t + 1, 2025): d[f'a{y}'] = P[y].reindex(d.index).fillna(0)
    d['inc'] = d['a2024'] - d.allowed
    d['subseq'] = sum(d[f'a{y}'] for y in range(t + 1, 2025))
    return d[d.allowed >= 10e6]
def rule(d, kind):
    s = (d.allowed >= 10e6) & (d.growth >= 0.5)
    if kind == 'growth': return s
    conc = d['wmean_code_hhi'] if kind == 'wmean' else d['hhi']
    return s & ((conc >= 1500) | (d.nat_provs <= 100))
AP = [('code', 'composite', 'Prespecified code rule', 'prespecified'),
      ('class', 'composite', 'Prespecified class rule', 'prespecified'),
      ('class', 'growth', 'Secondary class growth screen', 'secondary'),
      ('class', 'wmean', 'Exploratory weighted-HHI rule', 'exploratory')]
rows = []
for t in (2020, 2021, 2022, 2023):
    C = feats(t, 'class'); D = feats(t, 'code'); D['cls'] = info.cls.reindex(D.index)
    out_cls = {'O1_doubling': set(C.index[C.a2024 >= 2 * C.allowed]), 'O2_top_decile_increase': set(C.inc.nlargest(int(np.ceil(len(C) * 0.1))).index)}
    out_code = {'O1_doubling': set(D.index[D.a2024 >= 2 * D.allowed]), 'O2_top_decile_increase': set(D.inc.nlargest(int(np.ceil(len(D) * 0.1))).index)}
    tot_pos_inc = C.inc.clip(lower=0).sum(); tot_subseq = C.subseq.sum()
    skin24 = CA.loc['Skin substitute products', 2024]
    for level, kind, label, status in AP:
        U = D if level == 'code' else C
        f = rule(U, kind); sel = U[f]
        fl_cls = set(sel.cls) if level == 'code' else set(sel.index)
        fl_codes = set(sel.index) if level == 'code' else set(D.index[D.cls.isin(fl_cls)])
        r = {'t': t, 'approach': label, 'status': status, 'level': level, 'units_flagged': len(sel), 'classes_touched': len(fl_cls),
             'eligible_units': len(U), 'flagged_spend_t_M': sel.allowed.sum() / 1e6,
             'flagged_subsequent_spend_M': sel.subseq.sum() / 1e6,
             'share_of_subsequent_nonlab_spend_flagged': sel.subseq.sum() / tot_subseq,
             'net_increase_flagged_M': sel.inc.sum() / 1e6,
             'share_of_positive_growth_captured': sel.inc.sum() / tot_pos_inc,
             'skin_2024_captured': (A.loc[A.index.isin(sel.index) & A.index.isin(info.index[info.stratum == 'skin']), 2024].sum() if level == 'code'
                                    else (skin24 if 'Skin substitute products' in sel.index else 0)) / skin24}
        # composition of flagged classes: named multi-code classes vs single-code (unmatched, own-class) codes
        named = [c for c in fl_cls if not str(c).endswith('(unclassified, own class)')]
        r['n_flagged_named_classes'] = len(named); r['n_flagged_single_code_classes'] = len(fl_cls) - len(named)
        Cx = C.drop('Skin substitute products', errors='ignore'); selx = sel[~(sel.cls == 'Skin substitute products' if level == 'code' else sel.index == 'Skin substitute products')]
        r['share_of_positive_growth_captured_excl_skin'] = selx.inc.sum() / Cx.inc.clip(lower=0).sum()
        ocx = out_cls['O1_doubling'] - {'Skin substitute products'}; flx = fl_cls - {'Skin substitute products'}
        r['O1_doubling_class_sens_excl_skin'] = len(ocx & flx) / len(ocx); r['O1_doubling_class_ppv_excl_skin'] = len(ocx & flx) / len(flx) if flx else np.nan
        r['growth_captured_per_unit_pctpts'] = 100 * r['share_of_positive_growth_captured'] / len(sel) if len(sel) else np.nan
        for o in out_cls:
            oc = out_cls[o]; ocd = out_code[o]
            r[f'{o}_n_classes'] = len(oc); r[f'{o}_class_sens'] = len(oc & fl_cls) / len(oc)
            r[f'{o}_class_ppv'] = len(oc & fl_cls) / len(fl_cls) if fl_cls else np.nan
            r[f'{o}_n_codes'] = len(ocd); r[f'{o}_code_sens'] = len(ocd & fl_codes) / len(ocd)
            r[f'{o}_code_ppv'] = (len(ocd & fl_codes) / len(fl_codes) if level == 'code' else
                                 np.mean([len(ocd & set(D.index[D.cls == c])) > 0 for c in fl_cls])) if fl_cls else np.nan
            # spending capture of outcome classes' 2024 spending
            den = C.loc[list(oc), 'a2024'].sum()
            num = (A.loc[A.index.isin(sel.index) & A.index.isin(info.index[info.cls.isin(oc)]), 2024].sum() if level == 'code' else C.loc[list(oc & fl_cls), 'a2024'].sum())
            r[f'{o}_2024_spend_captured'] = num / den
        rows.append(r)
T = pd.DataFrame(rows); T.to_csv('tables/k_tradeoff_by_year.csv', index=False)
S = T.groupby(['approach', 'status'], sort=False).agg(**{c: (c, 'mean') for c in ['units_flagged', 'share_of_positive_growth_captured', 'share_of_subsequent_nonlab_spend_flagged', 'skin_2024_captured',
      'O1_doubling_class_sens', 'O1_doubling_class_ppv', 'O1_doubling_code_sens', 'O1_doubling_code_ppv', 'O2_top_decile_increase_class_sens', 'O2_top_decile_increase_class_ppv', 'O1_doubling_2024_spend_captured', 'share_of_positive_growth_captured_excl_skin', 'O1_doubling_class_sens_excl_skin', 'O1_doubling_class_ppv_excl_skin']}).reset_index()
S.to_csv('tables/k_tradeoff_summary_mean_2020_2023.csv', index=False)
pd.set_option('display.width', 250)
json.dump({'by_year': T.round(4).to_dict('records'), 'mean_2020_2023': S.round(4).to_dict('records')}, open('tables/tradeoff_key_numbers.json', 'w'), indent=1)
# figure
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
def tradeoff_fig(shape, size, out):
    fig, ax = plt.subplots(*shape, figsize=size)
    sty = {'prespecified': 'o', 'secondary': 's', 'exploratory': '^'}
    col = dict(zip([a[2] for a in AP], ['#888888', '#4d4d4d', '#2166ac', '#b2182b']))
    short = dict(zip([a[2] for a in AP], ['Prespecified code rule', 'Prespecified class rule', 'Secondary class growth screen', 'Exploratory weighted-HHI rule']))
    for (lab, st_), d in T.groupby(['approach', 'status'], sort=False):
        for k, (yv, tt) in enumerate([('O1_doubling_class_sens', 'A. Sensitivity: classes that doubled by 2024'), ('share_of_positive_growth_captured', 'B. Share of later spending growth captured'), ('share_of_positive_growth_captured_excl_skin', 'C. Same as B, excluding skin substitutes')]):
            ax[k].plot(d.units_flagged, d[yv] * 100, marker=sty[st_], color=col[lab], ls='none', ms=7, label=short[lab])
            for _, r in d.iterrows(): ax[k].annotate(str(r.t)[2:], (r.units_flagged, r[yv] * 100), fontsize=7, xytext=(3, 3), textcoords='offset points')
            ax[k].set_title(tt, fontsize=10, loc='left'); ax[k].set_xlabel('Units flagged per year (review burden)'); ax[k].set_ylabel('%')
    for a in ax:
        for s in ('top', 'right'): a.spines[s].set_visible(False)
    ax[0].legend(fontsize=7.5, frameon=False)
    for a in ax[1:]: a.axhline(0, color='k', lw=0.5)
    # explanatory notes are in the figure legend in the manuscript (journal requires legends outside image files)
    plt.tight_layout(rect=(0, 0.02, 1, 1)); plt.savefig(out, dpi=300); plt.savefig(out.replace('.png', '.pdf')); plt.close()
tradeoff_fig((1, 3), (15, 4.8), 'figures/fig8_tradeoff.png')
tradeoff_fig((3, 1), (6, 12.5), 'figures/fig8_tradeoff_vertical.png')
# poster version: panels A and C only, larger type
sty = {'prespecified': 'o', 'secondary': 's', 'exploratory': '^'}
col = dict(zip([a[2] for a in AP], ['#888888', '#4d4d4d', '#2166ac', '#b2182b']))
short = dict(zip([a[2] for a in AP], ['Prespecified code rule', 'Prespecified class rule', 'Secondary class growth screen', 'Exploratory weighted-HHI rule']))
plt.rcParams.update({'font.size': 13})
fig, ax = plt.subplots(2, 1, figsize=(7, 8.6))
for (lab, st_), d in T.groupby(['approach', 'status'], sort=False):
    for k, (yv, tt) in enumerate([('O1_doubling_class_sens', 'A. Sensitivity for classes that doubled'), ('share_of_positive_growth_captured_excl_skin', 'B. Later growth captured, excluding skin')]):
        ax[k].plot(d.units_flagged, d[yv] * 100, marker=sty[st_], color=col[lab], ls='none', ms=10, label=short[lab])
        ax[k].set_title(tt, fontsize=14, loc='left'); ax[k].set_ylabel('%')
ax[1].set_xlabel('Units flagged per year (review burden)'); ax[1].axhline(0, color='k', lw=0.6)
for a in ax:
    for s_ in ('top', 'right'): a.spines[s_].set_visible(False)
ax[0].legend(fontsize=10.5, frameon=False, loc='upper left')
plt.tight_layout(); plt.savefig('figures/fig8_tradeoff_poster.png', dpi=200); plt.close()
