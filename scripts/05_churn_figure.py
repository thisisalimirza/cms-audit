import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})
m = pd.read_csv('data/concentration_by_code_year.csv', dtype={'HCPCS_Cd': str}); m = m[m.category == 'Skin substitute product']
first = m[m.allowed > 0].groupby('HCPCS_Cd').year.min().rename('first'); m = m.join(first, on='HCPCS_Cd')
m['vintage'] = np.where(m['first'] <= 2019, '2019 or earlier', m['first'].astype(str))
pv = m.pivot_table(index='year', columns='vintage', values='allowed', aggfunc='sum').fillna(0) / 1e9
pv.to_csv('tables/h_skin_spend_by_code_vintage.csv')
cols = ['#d9d9d9', '#bdbdbd', '#969696', '#fdae6b', '#e6550d', '#a63603']
fig, ax = plt.subplots(figsize=(6.0, 4.8)); bottom = np.zeros(len(pv))
for c, col in zip(pv.columns, cols):
    ax.bar(pv.index, pv[c], bottom=bottom, color=col, label=f'Codes first billed {c}', width=0.65); bottom += pv[c].values
for x, v in zip(pv.index, bottom): ax.text(x, v + 0.15, f'${v:.2f}B', ha='center', fontsize=8.5)
ax.set_ylabel('Allowed amount, $ billions'); ax.set_xlabel('Service year'); ax.legend(frameon=False, fontsize=8.5, loc='upper left'); ax.set_ylim(0, 11.2)
plt.tight_layout(); plt.savefig('figures/fig6_skin_code_churn.png'); plt.savefig('figures/fig6_skin_code_churn.pdf'); print(pv.round(2))
