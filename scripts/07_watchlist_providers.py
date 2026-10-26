"""Pull 2024 'by Provider and Service' rows (CMS API) for watchlist codes; compute reported top-1/top-10 provider shares.
No provider identities are carried into outputs."""
import requests, pandas as pd, time, json, os
DS = '92396110-2aed-4d63-a6a2-5d6207d46a29'
W = pd.read_csv('data/watchlist_2024_raw.csv', dtype={'unit': str})
codes = sorted(W[W.level == 'code'].unit.unique())
out = []
for c in codes:
    cf = f'data/provider_cache/2024_{c}.json'
    if not os.path.exists(cf):
        rows, off = [], 0
        while True:
            for a in range(8):
                r = requests.get(f'https://data.cms.gov/data-api/v1/dataset/{DS}/data', params={'filter[HCPCS_Cd]': c, 'size': 5000, 'offset': off}, timeout=120)
                if r.status_code == 429: time.sleep(10 * (a + 1)); continue
                break
            r.raise_for_status(); j = r.json(); time.sleep(1.0); rows += j
            if len(j) < 5000: break
            off += 5000
        json.dump(rows, open(cf, 'w')); print(c, len(rows), flush=True)
    d = pd.DataFrame(json.load(open(cf)))
    if len(d) == 0: out.append({'unit': c, 'n_reported_npis': 0}); continue
    d['amt'] = d.Avg_Mdcr_Alowd_Amt.astype(float) * d.Tot_Srvcs.astype(float)
    s = d.groupby('Rndrng_NPI').amt.sum().sort_values(ascending=False)
    out.append({'unit': c, 'n_reported_npis': len(s), 'provider_file_allowed': s.sum(),
                'top1_provider_share': s.iloc[0] / s.sum(), 'top10_provider_share': s.iloc[:10].sum() / s.sum()})
pd.DataFrame(out).to_csv('data/watchlist_provider_shares.csv', index=False)
