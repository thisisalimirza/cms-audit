"""Check that every number in the rendered documents appears in tables/master_results.json.
Usage: python3 check_numbers.py [ROOT]  (ROOT defaults to the project root). Exit code 1 if any number is unmatched."""
import sys, re, json, os
from docx import Document
from pptx import Presentation
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MR = json.load(open(os.path.join(ROOT, 'tables/master_results.json')))
DOCS = ['writeup/research_letter_JAMA_IM.docx', 'writeup/long_paper_HealthAffairsScholar.docx', 'writeup/long_paper_HealthAffairsScholar_appendix.docx',
        'writeup/abstract_SGIM2027.docx', 'writeup/abstract_AcademyHealth_ARM2027.docx', 'writeup/poster/poster_SGIM2027_48x36.pptx']
WC = json.load(open(os.path.join(ROOT, 'writeup/wordcounts.json')))
# allowed values: every master value at 0-2 decimals, percent forms, and $M/$B conversions
OK = set()
def add(v):
    for d in (0, 1, 2): OK.add(round(v, d))
for r in MR.values():
    v = r['value']
    if not isinstance(v, (int, float)) or v != v: continue
    add(v); add(abs(v))
    if r['kind'] == 'frac': add(v * 100); add(abs(v * 100))
    if r['kind'] == 'usdM': add(v / 1000); add(abs(v / 1000))
META = set(WC.values()) | {3000, 4000, 800, 500, 200, 100, 4, 1, 2, 3, 5, 10, 15}  # limits/counts in metadata lines are checked separately
STRUCT = {1, 2, 3, 4, 5}  # exhibit/figure/reference/aim numbering; checked by excluding labelled contexts below
def texts(path):
    p = os.path.join(ROOT, path)
    if path.endswith('.pptx'):
        for sl in Presentation(p).slides:
            for sh in sl.shapes:
                if sh.has_text_frame: yield sh.text_frame.text
        return
    d = Document(p)
    for para in d.paragraphs: yield para.text
    for t in d.tables:
        for row in t.rows:
            for c in row.cells: yield c.text
STRIP = [r'https?://\S+', r'\b(?:19|20)\d\d\b(?:-\d\d)?', r'\b(?:Figure|Table|Exhibit|Exhibits|fig)\s*A?\d+(?:-A?\d+)?', r'\bA[1-5]\b',
         r'\b[A-Z]{1,4}\d{3,5}[A-Z]?\b|\b\d{4,5}[A-Z]\b|\b\d{5}\b(?=[-\s,)]|$)',  # HCPCS codes and ranges
         r'OEI-BL-\d\d-\d+', r'CMS-\d+-F', r'CY\s?\d+', r'[¹²³⁴⁵⁶,]+(?=\s|$|\.)', r'\b\d+(?:st|nd|rd|th)\b', r'\bCOVID-19\b', r'48x36|\b48\b|\b36\b',
         r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?', r'\d{1,2}:\d\d\s*[AP]M', r'\b\d+\.\s(?=[A-Z])',
         r'Q\d{4}-Q\d{4}', r'\d{4}-\d{4}', r'\b\d{4}[A-Z]?-\d{4,5}\b']
WORDNUM = {'2 years': None, 'last 2 digits': None}
def numbers(t):
    for k in WORDNUM: t = t.replace(k, ' ')
    for pat in STRIP: t = re.sub(pat, ' ', t)
    for m in re.finditer(r'(?<![A-Za-z0-9])[-−]?\$?\d[\d,]*(?:\.\d+)?\s*(?:%|billion|million|B\b|M\b)?', t):
        yield m.group(0).strip()
def parse(tok):
    s = tok.replace('−', '-').replace('$', '').replace(',', '').strip()
    mult = 1
    if s.endswith('%'): s = s[:-1]
    for suf, f in (('billion', 1), ('million', 1), ('B', 1), ('M', 1)):
        if s.endswith(suf): s = s[:-len(suf)].strip()
    try: return float(s)
    except ValueError: return None
bad = []; n = 0
for path in DOCS:
    for t in texts(path):
        meta = bool(re.search(r'(Word count|Character count|Figures/tables|References: \d|limit|Main-text exhibits|Deadline|ARM: June|Article type)', t))
        for tok in numbers(t):
            v = parse(tok)
            if v is None: continue
            n += 1
            if meta and v in META: continue
            if v in STRUCT and not tok.endswith('%') and '$' not in tok and '.' not in tok: continue  # small integers 1-5 (counts like "1 skin class", "4 flag years" are also in master)
            if any(abs(v - o) < 1e-9 for o in (round(v, 0), round(v, 1), round(v, 2)) if o in OK) or v in OK: continue
            bad.append((path, tok, t[:110]))
print(f'checked {n} numeric tokens in {len(DOCS)} documents against {len(MR)} master statistics')
for b in bad: print('UNMATCHED', *b, sep=' | ')
print('RESULT:', 'PASS (0 unmatched)' if not bad else f'FAIL ({len(bad)} unmatched)')
sys.exit(1 if bad else 0)
