import pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})
cat = pd.read_csv('tables/f_skin_category_by_year.csv'); perf = pd.read_csv('tables/f_lookback_performance.csv')
import sys
V = len(sys.argv) > 1
fig, (a, b) = (plt.subplots(2, 1, figsize=(6.0, 6.4)) if V else plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={'width_ratios': [1.15, 1]}))
a.bar(cat.year, cat.allowed_M / 1e3, color='#b2182b', width=0.6)
for x, v in zip(cat.year, cat.allowed_M / 1e3): a.text(x, v + 0.15, f'{v:.2f}', ha='center', fontsize=7.5)
a.set_ylim(0, 11); a.set_ylabel('Allowed amount, $ billions'); a.set_title('A. Skin-substitute product spending', loc='left', fontsize=9)
c = perf[(perf.rule == 'composite') & (perf.stratum == 'non-lab')]
x = range(len(c)); w = 0.38
b.bar([i - w / 2 for i in x], c.flagged_ratio_2024_to_t, w, color='#2166ac', label='Flagged by prespecified code rule')
b.bar([i + w / 2 for i in x], c.unflagged_ratio_2024_to_t, w, color='#bdbdbd', label='Not flagged (≥$10M)')
for i, (f_, u_) in enumerate(zip(c.flagged_ratio_2024_to_t, c.unflagged_ratio_2024_to_t)):
    b.text(i - w / 2, f_ + 0.06, f'{f_:.2f}', ha='center', fontsize=7.5); b.text(i + w / 2, u_ + 0.06, f'{u_:.2f}', ha='center', fontsize=7.5)
b.axhline(1, color='k', lw=0.6, ls=':'); b.set_xticks(list(x)); b.set_xticklabels([f'{t}' for t in c.t])
b.set_xlabel('Flag year t (data through t only)'); b.set_ylabel('2024 spending ÷ year-t spending')
b.set_title('B. Growth to 2024, flagged vs not', loc='left', fontsize=9); b.legend(frameon=False, fontsize=7.5, loc='upper right'); b.set_ylim(0, 4.4)
plt.tight_layout(); plt.savefig('figures/fig5_lookback_vertical.png' if V else 'figures/fig5_lookback.png'); plt.savefig('figures/fig5_lookback_vertical.pdf' if V else 'figures/fig5_lookback.pdf'); plt.close()
