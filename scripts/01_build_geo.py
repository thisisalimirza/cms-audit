"""Load CMS 'Medicare Physician & Other Practitioners - by Geography and Service' CSVs (2019-2024),
compute total allowed/paid = avg * Tot_Srvcs, aggregate over place of service, write tidy parquet-like CSV."""
import pandas as pd, glob, re
FILES = sorted(glob.glob('data/MUP_PHY_*_Geo.csv'))
out = []
for f in FILES:
    yr = 2000 + int(re.search(r'_D(\d\d)_Geo', f).group(1))
    d = pd.read_csv(f, dtype={'HCPCS_Cd': str, 'Rndrng_Prvdr_Geo_Cd': str}, low_memory=False)
    d['allowed'] = d.Avg_Mdcr_Alowd_Amt * d.Tot_Srvcs
    d['paid'] = d.Avg_Mdcr_Pymt_Amt * d.Tot_Srvcs
    d['year'] = yr
    out.append(d)
d = pd.concat(out)
d.to_pickle('data/geo_all.pkl')
nat = d[d.Rndrng_Prvdr_Geo_Lvl == 'National'].groupby(['year', 'HCPCS_Cd']).agg(
    allowed=('allowed', 'sum'), paid=('paid', 'sum'), srvcs=('Tot_Srvcs', 'sum'),
    desc=('HCPCS_Desc', 'first'), drug=('HCPCS_Drug_Ind', 'first')).reset_index()
nat.to_csv('data/national_by_code_year.csv', index=False)
st = d[d.Rndrng_Prvdr_Geo_Lvl == 'State'].groupby(['year', 'HCPCS_Cd', 'Rndrng_Prvdr_Geo_Desc']).agg(
    allowed=('allowed', 'sum'), paid=('paid', 'sum'), srvcs=('Tot_Srvcs', 'sum'), provs=('Tot_Rndrng_Prvdrs', 'sum')).reset_index()
st.rename(columns={'Rndrng_Prvdr_Geo_Desc': 'state'}).to_csv('data/state_by_code_year.csv', index=False)
print(d.groupby(['year', 'Rndrng_Prvdr_Geo_Lvl']).size())
print(nat.groupby('year')[['allowed', 'paid']].sum() / 1e9)
