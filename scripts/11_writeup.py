"""Builds the letter, paper (+ separate appendix), SGIM and ARM abstracts from tables/master_results.json and tables/exhibits/*.csv.
Every number in the text is taken from master_results via N(); repro/scripts/check_numbers.py verifies the rendered documents."""
import re, json, subprocess, os, shutil
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches
W = 'writeup/'
MR = json.load(open('tables/master_results.json'))
def N(i, dec=None):
    r = MR[i]
    if dec is None: return r['display']
    v, k = r['value'], r['kind']
    return f'{v*100:.{dec}f}%' if k == 'frac' else f'{v:,.{dec}f}'
def NR(a, c): return f"{N(f'tr.{a}.min.{c}')} to {N(f'tr.{a}.max.{c}')}"
def X(name): return pd.read_csv(f'tables/exhibits/{name}.csv', dtype=str, keep_default_na=False)
def rows(df): return [list(df.columns)] + df.values.tolist()
AUTH = 'Ali Mirza, B.S.¹; [ALI TO CONFIRM: coauthor name, degree, and agreement to authorship — currently listed as Christopher Steele, MD]²'
AFF = ['¹University of Connecticut School of Medicine, Farmington, Connecticut', '²[ALI TO CONFIRM: coauthor affiliation]']
REFS = [
 'US Department of Health and Human Services Office of Inspector General. Medicare Part B payment trends for skin substitutes raise major concerns about fraud, waste, and abuse. Report OEI-BL-24-00420. September 3, 2025. Accessed October 26, 2026. https://oig.hhs.gov/reports/all/2025/medicare-part-b-payment-trends-for-skin-substitutes-raise-major-concerns-about-fraud-waste-and-abuse/',
 'Centers for Medicare & Medicaid Services. Calendar Year (CY) 2026 Medicare Physician Fee Schedule final rule (CMS-1832-F) fact sheet. October 31, 2025. Accessed October 26, 2026. https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2026-medicare-physician-fee-schedule-final-rule-cms-1832-f',
 'Centers for Medicare & Medicaid Services. Medicare Physician & Other Practitioners – by Geography and Service, data years 2019-2024. Accessed October 26, 2026. https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-geography-and-service',
 'Centers for Medicare & Medicaid Services. Medicare Physician & Other Practitioners – by Provider and Service, data year 2024. Accessed October 26, 2026. https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service',
 'Centers for Medicare & Medicaid Services. Final local coverage determinations (LCDs) for certain skin substitutes withdrawn. Updated December 24, 2025. Accessed October 26, 2026. https://www.cms.gov/newsroom/fact-sheets/upcoming-update-final-local-coverage-determinations-lcds-certain-skin-substitutes',
]
def wc(paras): return sum(len(re.findall(r"[A-Za-z0-9$%.,'’\-–/≥×]+", p)) for p in paras)
def table(d, cap, rws, note=None):
    p = d.add_paragraph(); p.add_run(cap).bold = True
    tb = d.add_table(rows=len(rws), cols=len(rws[0])); tb.style = 'Table Grid'
    for i, row in enumerate(rws):
        for j, v in enumerate(row):
            c = tb.cell(i, j); c.text = str(v)
            for pp in c.paragraphs:
                for rr in pp.runs: rr.font.size = Pt(9); rr.bold = (i == 0)
    if note: d.add_paragraph(note)
def build(fname, title, sections, refs, figs=(), tables=(), front_extra=(), counted=None, legends=(), exhibit_list=None, authors=True):
    d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
    for s in d.sections: s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    h = d.add_paragraph(); r = h.add_run(title); r.bold = True; r.font.size = Pt(14)
    if authors:
        d.add_paragraph(AUTH)
        for a in AFF: d.add_paragraph(a)
    for x in front_extra: d.add_paragraph(x)
    for head, paras in sections:
        if head: p = d.add_paragraph(); rr = p.add_run(head); rr.bold = True
        for t in paras: d.add_paragraph(t)
    if refs:
        p = d.add_paragraph(); p.add_run('References').bold = True
        for i, r_ in enumerate(refs, 1): d.add_paragraph(f'{i}. {r_}')
    if exhibit_list:
        p = d.add_paragraph(); p.add_run('List of Exhibits').bold = True
        for e in exhibit_list: d.add_paragraph(e)
    for t_ in tables: table(d, *t_)
    for img, cap in figs:
        d.add_page_break(); d.add_picture(img, width=Inches(6.5)); d.add_paragraph(cap)
    if legends:
        p = d.add_paragraph(); p.add_run('Figure Legends').bold = True
        for lg in legends: d.add_paragraph(lg)
    d.save(W + fname + '.docx')
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', W, W + fname + '.docx'], capture_output=True)
    return wc([t for h_, ps in sections for t in ps] if counted is None else counted)

from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
def _orient(d, landscape):
    sec = d.add_section(WD_SECTION.NEW_PAGE); w, h = Inches(8.5), Inches(11)
    sec.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = (h, w) if landscape else (w, h)
    for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(sec, m, Inches(0.8 if landscape else 1))
def _table(d, cap, rws, note=None, fs=9):
    p = d.add_paragraph(); p.add_run(cap).bold = True; p.paragraph_format.keep_with_next = True
    tb = d.add_table(rows=len(rws), cols=len(rws[0])); tb.style = 'Table Grid'
    tr = tb.rows[0]._tr.get_or_add_trPr(); e = OxmlElement('w:tblHeader'); e.set(qn('w:val'), 'true'); tr.append(e)
    for i, row in enumerate(rws):
        for j, v in enumerate(row):
            c = tb.cell(i, j); c.text = str(v)
            for pp in c.paragraphs:
                pp.paragraph_format.space_after = Pt(0)
                for rr in pp.runs: rr.font.size = Pt(fs); rr.bold = (i == 0)
    sec = d.sections[-1]; tw = sec.page_width - sec.left_margin - sec.right_margin
    wt = [max(max(min(max([len(w) for w in str(r_[j]).split()] or [1]), 16) for r_ in rws), 8) + 0.12 * max(min(len(str(r_[j])), 70) for r_ in rws[1:] or rws) for j in range(len(rws[0]))]
    tb.autofit = False
    for j, c in enumerate(tb.columns):
        for cell in c.cells: cell.width = int(tw * wt[j] / sum(wt))
    tblPr = tb._tbl.tblPr; tw_ = OxmlElement('w:tblW'); tw_.set(qn('w:w'), str(int(tw / 635))); tw_.set(qn('w:type'), 'dxa')
    for old in tblPr.findall(qn('w:tblW')): tblPr.remove(old)
    tblPr.append(tw_); lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    for j, gc in enumerate(tb._tbl.tblGrid.findall(qn('w:gridCol'))): gc.set(qn('w:w'), str(int(tw * wt[j] / sum(wt) / 635)))
    if note: q = d.add_paragraph(note); [setattr(r.font, 'size', Pt(10)) for r in q.runs]
    d.add_paragraph()
def _fig(d, path, cap, width):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(width))
    q = d.add_paragraph(); r = q.add_run(cap); r.font.size = Pt(10)
def _exhibits(d, exs, cur_land):
    """exs: list of dicts kind=fig|tab, land=bool. Returns final orientation (always back to portrait)."""
    for ex in exs:
        if ex.get('land', False) != cur_land: _orient(d, ex.get('land', False)); cur_land = ex.get('land', False)
        if ex['kind'] == 'fig': _fig(d, ex['path'], ex['cap'], ex.get('w', 9.0 if cur_land else 6.5))
        else: _table(d, ex['cap'], ex['rows'], ex.get('note'), ex.get('fs', 9))
    return cur_land
def build_inline(fname, title, sections, refs, inline, appendix=(), front_extra=(), app_title=None):
    d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
    for s_ in d.sections: s_.left_margin = s_.right_margin = s_.top_margin = s_.bottom_margin = Inches(1)
    h = d.add_paragraph(); r = h.add_run(title); r.bold = True; r.font.size = Pt(14)
    d.add_paragraph(AUTH); [d.add_paragraph(a) for a in AFF]
    for x in front_extra: d.add_paragraph(x)
    done = set(); land = False
    for head, paras in sections:
        if head:
            if land: _orient(d, False); land = False
            p = d.add_paragraph(); rr = p.add_run(head); rr.bold = True; p.paragraph_format.keep_with_next = True
        for t in paras:
            if land: _orient(d, False); land = False
            d.add_paragraph(t)
            for trig, exs in inline:
                if trig not in done and trig in t:
                    done.add(trig); land = _exhibits(d, exs, land)
    assert done == {t for t, _ in inline}, set(t for t, _ in inline) - done
    if land: _orient(d, False); land = False
    if refs:
        p = d.add_paragraph(); p.add_run('References').bold = True
        for i, r_ in enumerate(refs, 1): d.add_paragraph(f'{i}. {r_}')
    if appendix:
        p = d.add_paragraph(); p.paragraph_format.page_break_before = True; r = p.add_run(app_title or 'Supplementary Appendix'); r.bold = True; r.font.size = Pt(14)
        land = _exhibits(d, appendix, False)
    d.save(W + fname + '.docx')
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', W, W + fname + '.docx'], capture_output=True)
# ---------------- shared statements ----------------
NAMES = 'prespecified code rule, prespecified class rule, secondary class growth screen, and exploratory weighted-HHI rule'
OUT_DEF = ('the doubling outcome (class spending in 2024 at least twice its flag-year spending) and the top-decile outcome (an absolute increase from the flag year to 2024 in the top decile among eligible classes)')
GROWTH_DEF = ('growth captured, defined as the net change in spending of flagged units from the flag year to 2024 divided by the summed positive change across all eligible classes')
NOTPROOF = 'Spending captured within flagged units does not establish that any of it was improper, and the screen does not predict misconduct.'
THRESH = ('The thresholds are round values chosen by the authors during this study, before the look-back was computed, to yield a short review list. They were not preregistered, and they were chosen with general knowledge that skin-substitute spending had surged. Because the evaluation also contains one known outcome, it is a retrospective evaluation of a transparent screening approach, not an independent validation of predictive performance.')
DEM = (f"Demonstrated: grouping all skin-substitute codes into one class addressed code churn within that category. The secondary class growth screen flagged the class in {N('tr.cgr.n_years_flag_skin')} of {N('param.n_flag_years')} flag years and therefore covered all of its 2024 spending in those years, whereas codes flagged with 2021 data covered {N('lb21.share_2024_skin_captured')}.")
NOTDEM = (f"Not demonstrated: that class grouping generalizes to other categories. Only {N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes ({N('cls.share_codes_named')}) belonged to the {N('cls.n_named')} named classes; the other {N('cls.n_codes_single')} codes were single-code classes, for which class screening is identical to code screening. "
          f"Of the {NR('cgr', 'units_flagged')} classes flagged each year by the secondary class growth screen, {NR('cgr', 'n_flagged_single_code_classes')} were single-code classes and {NR('cgr', 'n_flagged_named_classes')} were named classes. Excluding skin substitutes, no class approach captured more later growth than the prespecified code rule ({N('tr.code.mean.share_of_positive_growth_captured_excl_skin')}).")
WEIGHTED = (f"The exploratory weighted-HHI rule is a post hoc proposal, not an established solution: outside skin substitutes it captured {N('tr.cw.mean.share_of_positive_growth_captured_excl_skin')} of later growth, compared with {N('tr.code.mean.share_of_positive_growth_captured_excl_skin')} for the prespecified code rule, so its advantage largely disappears outside the category that motivated it.")
CONC = (f"Concentration measures. For a code, the state HHI is the sum over states of the squared state share of the code's state-attributed spending, multiplied by {N('param.hhi_scale')}. The prespecified class rule uses the pooled state HHI: member-code spending is first summed within each state, and the HHI is computed from the pooled state shares. The exploratory weighted-HHI rule instead uses the spending-weighted mean of member-code HHIs, the sum over member codes of the code's share of class spending multiplied by the code's own state HHI. "
        "Pooling dilutes concentration when different products in a class are concentrated in different states, because the pooled state shares average across products; because HHI is a convex function of shares, the pooled HHI cannot exceed the weighted mean when the weights are state-attributed spending shares (our weights use national spending, which differs only through small-cell suppression). "
        f"For skin substitutes in 2021, the pooled HHI was {N('ex.pooled_hhi')} while the weighted mean of member-code HHIs was {N('ex.wmean_hhi')}; {N('ex.n_codes_hhi_ge1500')} of {N('ex.n_codes')} member codes, with {N('ex.share_spend_codes_hhi_ge1500')} of class spending, had their own HHI of at least {N('param.hhi')} (worked example in Appendix Exhibit A5).")
DS = 'Data availability: All data are public CMS files. Analysis code, the code-to-class mapping, the master results file, and data retrieval instructions are in the reproducibility package at [ALI TO ADD repository URL].'
AI = ('Use of AI tools [ALI TO CONFIRM]: AI tools assisted the authors with writing and debugging analysis code, running and checking analyses, and drafting and editing the manuscript text. [ALI TO CONFIRM: name the specific tools.] '
      'The authors reviewed the code, verified all reported numbers against the reproducible analysis outputs, checked every reference against its original source, and take full responsibility for the content.')
RULE = (f"In year t, the rule flagged a unit with at least {N('param.spend_M')} in allowed spending, at least {N('param.growth')} growth from year t−1 (units with no spending in t−1 met this criterion), and a state Herfindahl-Hirschman Index (HHI) of at least {N('param.hhi')} or no more than {N('param.providers')} rendering providers.")
# ---------------- Research letter ----------------
TITLE = 'A Transparent Public-Data Screen for Medicare Part B Spending Surges: A Retrospective Evaluation'
P_TITLE = 'Code Churn and Review Burden in Public-Data Screening of Medicare Part B Spending Surges'
assert len(TITLE) <= 100 and len(P_TITLE) <= 100
L = [
('Introduction', [
 f"Medicare Part B spending on skin substitutes grew from {N('ext.cms_skin_2019_M')} in 2019 to more than {N('ext.cms_skin_2024_B')} in 2024, prompting an Office of Inspector General warning and a payment overhaul in the 2026 Physician Fee Schedule.¹,² We retrospectively evaluated a transparent screen combining spending, growth, and concentration, applied only to public data available at each time, and quantified the tradeoff between screening codes and product classes."]),
('Methods', [
 f"We used the public Medicare Physician & Other Practitioners files by Geography and Service for 2019 through 2024 and by Provider and Service for 2024.³,⁴ Allowed spending was the average allowed amount multiplied by services in national rows. {RULE} " + THRESH +
 f" We compared four approaches: the {NAMES}. Classes grouped all skin substitutes, {N('cls.n_named_drug')} drug classes, and {N('cls.n_named_service')} service families ({N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes); every other code was its own single-code class. The prespecified class rule used the pooled state HHI of the class, the secondary class growth screen omitted concentration, and the exploratory weighted-HHI rule, added after viewing results, used the spending-weighted mean HHI of member codes. Laboratory codes were analyzed separately. For flag years 2020 through 2023, among non-laboratory units with at least {N('param.spend_M')}, we measured units flagged per year, {GROWTH_DEF}, and sensitivity and positive predictive value (PPV) for the doubling outcome (2024 class spending at least twice flag-year spending). The study used public aggregate data and was not human participants research."]),
('Results', [
 f"Skin-substitute spending in these files rose from {N('skin.allowed_2019_M')} in 2019 to {N('skin.allowed_2024_M')} in 2024. Using 2021 data, the prespecified code rule flagged {N('lb21.n_flagged')} of {N('lb21.n_eligible')} eligible codes, {N('lb21.n_skin')} of them skin substitutes, but {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes absent in 2021, so these flags captured {N('lb21.share_2024_skin_captured')} of it. Across flag years, the prespecified code rule flagged a mean of {N('tr.code.mean.units_flagged')} codes per year, with {N('tr.code.mean.O1_doubling_class_sens')} sensitivity and {N('tr.code.mean.O1_doubling_class_ppv')} PPV (Table).",
 f"The prespecified class rule never flagged skin substitutes, because pooling products across states lowered the class HHI to {N('skin.pooled_hhi_min_2020_2024')} to {N('skin.pooled_hhi_max_2020_2024')}. The secondary class growth screen raised sensitivity to {N('tr.cgr.mean.O1_doubling_class_sens')} but flagged {NR('cgr','units_flagged')} classes per year, {NR('cgr','n_flagged_single_code_classes')} of them single-code classes, and PPV fell to {N('tr.cgr.mean.O1_doubling_class_ppv')} (Figure). The exploratory weighted-HHI rule flagged {N('tr.cw.min.units_flagged')} classes per year and captured {N('tr.cw.mean.share_of_positive_growth_captured')} of later growth, but {N('tr.cw.mean.share_of_positive_growth_captured_excl_skin')} excluding skin substitutes, compared with {N('tr.code.mean.share_of_positive_growth_captured_excl_skin')} for the code rule. Every approach missed the surge using 2022 data, when class growth slowed to {N('skin.growth_2022')}. Applied to 2024 data, the prespecified code rule flagged {N('wl.n_watch_nonlab_codes')} non-laboratory codes ({N('wl.watch_nonlab_allowed_2024_M')}), {N('wl.n_watch_skin_codes')} of them skin substitutes."]),
('Discussion', [
 f"Grouping skin-substitute codes into one class addressed code churn within that category, at about twice the review burden and lower PPV. Generalization to other categories was not demonstrated: {N('cls.n_codes_single')} of {N('tot.n_codes_all_years')} codes were single-code classes, most class flags were single-code classes, and outside skin substitutes no class approach captured more later growth than the code rule. The weighted-HHI measure is a post hoc proposal that needs prospective testing. " + NOTPROOF +
 ' Limitations include small-cell suppression, exclusion of Medicare Advantage and facility claims, rendering-state attribution, an approximately 2-year release lag, a single known outcome, and thresholds chosen with knowledge of that outcome.']),
]
FIGCAP = ('Figure. Review Burden vs Detection, Flag Years 2020-2023. Each point is one approach in one flag year (label, last 2 digits of the year). Units are non-laboratory codes or classes with at least $10 million in spending at the flag year. '
 'A, Sensitivity for the doubling outcome (class spending in 2024 at least twice flag-year spending). B, Growth captured: net change in spending of flagged units from the flag year to 2024 divided by the summed positive change across eligible classes. C, Panel B excluding skin substitutes. '
 'The exploratory weighted-HHI rule was specified after viewing results. HHI indicates Herfindahl-Hirschman Index.')
TCAP = ('Table. Review Burden and Detection by Screening Approach, Mean of Flag Years 2020-2023. Eligible units are non-laboratory codes or classes with at least $10 million in spending at the flag year. A code flag detects a class if any member code is flagged; '
        'PPV for the prespecified code rule is computed over distinct classes containing a flagged code. Captured spending does not indicate improper payment. PPV indicates positive predictive value.')
TT = rows(X('table1_tradeoff'))
TT_L = [[r[1], r[2], r[3], r[4], r[5], r[8], r[9]] for r in TT]  # letter: compact columns
def letter(wcv):
    build_inline('research_letter_JAMA_IM', TITLE, L, REFS[:4],
      inline=[('(Table)', [dict(kind='tab', cap=TCAP, rows=TT_L)]), ('(Figure)', [dict(kind='fig', path='figures/fig8_tradeoff.png', cap=FIGCAP, land=True)])],
      front_extra=['Article type: Research Letter (JAMA Internal Medicine)', 'Study type: Cross-sectional observational study with a retrospective evaluation', DS, AI,
                   f'Word count (main text, excluding title, references, table, and figure legend): {wcv}', 'Figures/tables: 1 figure, 1 table; References: 4'])
    return wc([t for h_, ps in L for t in ps])
letter_wc = letter(0); letter(letter_wc); print('letter words', letter_wc); assert letter_wc <= 800, letter_wc
# ---------------- Long paper ----------------
ABS = [f"Objective: To retrospectively evaluate a transparent public-data screen for rapidly growing, concentrated Medicare Part B spending, comparing code-level and product-class screening.",
 f"Methods: Using Medicare Physician & Other Practitioners files (2019-2024), we applied a prespecified rule (≥{N('param.spend_M')}, ≥{N('param.growth')} growth, and state Herfindahl-Hirschman Index ≥{N('param.hhi')} or ≤{N('param.providers')} providers) to codes and classes for flag years 2020-2023, measuring units flagged, sensitivity, and positive predictive value (PPV) for later doubling.",
 f"Results: {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes absent in 2021. The prespecified code rule flagged {N('tr.code.mean.units_flagged')} codes per year (sensitivity {N('tr.code.mean.O1_doubling_class_sens')}, PPV {N('tr.code.mean.O1_doubling_class_ppv')}); the secondary class growth screen raised sensitivity to {N('tr.cgr.mean.O1_doubling_class_sens')} but flagged {N('tr.cgr.mean.units_flagged')} classes per year (PPV {N('tr.cgr.mean.O1_doubling_class_ppv')}), mostly single-code classes. Grouping skin-substitute codes addressed churn within that category; generalization was not demonstrated, because only {N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes belonged to named classes. An exploratory weighted-HHI rule added little outside skin substitutes.",
 'Conclusions: Class-level screening trades review burden for sensitivity; its benefit here rests on one category.']
KT = ['Key Takeaways:',
      f"• Code churn limited a transparent code-level screen: {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes that did not exist in 2021.",
      f"• Demonstrated: grouping skin-substitute codes into one class addressed churn within that category. Not demonstrated: generalization to other categories, because {N('cls.n_codes_single')} of {N('tot.n_codes_all_years')} codes were single-code classes and most class flags ({NR('cgr','n_flagged_single_code_classes')} per year) were single-code classes.",
      f"• The secondary class growth screen raised sensitivity from {N('tr.code.mean.O1_doubling_class_sens')} to {N('tr.cgr.mean.O1_doubling_class_sens')} at about twice the review burden; the exploratory weighted-HHI rule is a post hoc proposal whose advantage largely disappears outside skin substitutes."]
KW_ = ['Keywords: Medicare Part B; skin substitutes; program integrity; code churn; screening; public data']
P_ = [('Abstract', ABS),
('Introduction', [
 f"Medicare Part B spending on skin substitutes, which are biologic and synthetic wound-care products billed per square centimeter or per unit, grew from {N('ext.cms_skin_2019_M')} in 2019 to more than {N('ext.cms_skin_2024_B')} in 2024, according to the Centers for Medicare & Medicaid Services (CMS).² In 2025, the Department of Health and Human Services Office of Inspector General (OIG) reported that quarterly Part B spending on these products had risen from about {N('ext.oig_quarterly_start_M')} to nearly {N('ext.oig_quarterly_end_B')} in 2 years and concluded that the trend raised major concerns about fraud, waste, and abuse.¹ CMS responded with a new payment approach in the calendar year 2026 Physician Fee Schedule, and Medicare contractors withdrew planned skin-substitute local coverage determinations before they took effect.²,⁵",
 'This episode raises a design question for anyone who screens public claims data for emerging spending problems. Public Medicare files are free, standardized, and open to independent review, but they are released with a lag and organized by billing code.³,⁴ Skin-substitute manufacturers obtained new product codes faster than older codes grew, so a surge that is obvious in the aggregate can be fragmented across many short-lived codes. Screening broader product classes can follow a product across codes, but it enlarges the review list and can dilute concentration signals.',
 f"We therefore retrospectively evaluated a transparent screening approach rather than attempting to validate a predictive model. We had three aims: first, to describe how code churn affected a prespecified code-level rule; second, to quantify the tradeoff between sensitivity and review burden for four approaches (the {NAMES}) across {N('param.n_flag_years')} flag years; and third, to demonstrate the rule on the most recent public data. The thresholds were chosen with general knowledge of the skin-substitute surge, and the evaluation contains one known outcome, so the results describe the behavior of the approach rather than its expected predictive accuracy."]),
('Data and Methods', [
 f"Data sources. We used the CMS Medicare Physician & Other Practitioners by Geography and Service files for data years 2019 through 2024, the latest year available.³ These files summarize fee-for-service Part B professional claims by Healthcare Common Procedure Coding System (HCPCS) code, place of service, and rendering-provider state, with national summary rows. They exclude Medicare Advantage encounters, institutional claims, and durable medical equipment supplier claims. For codes flagged in 2024, we queried the 2024 by Provider and Service file through the CMS data application programming interface.⁴ Cells representing fewer than {N('ext.suppression_benes')} beneficiaries are suppressed in both files. All files were downloaded on October 26, 2026; dataset names, URLs, and retrieval steps are listed in the reproducibility package.",
 f"Measures and denominators. Allowed spending was the average Medicare allowed amount multiplied by the number of services, summed across places of service. National totals used the national rows of the geography file. Because of suppression, state rows represent less than the national total; for skin substitutes they represented between {N('skin.state_coverage_min')} and {N('skin.state_coverage_max')} of national spending in each year. Provider shares were computed only from rows present in the provider file and are reported with the share of national spending that those rows represent (provider-file coverage). The look-back used the national count of rendering providers as a provider-concentration proxy, because provider files were not retrieved for every code and year.",
 f"Product classes. Classes were intended to follow a product across successive codes. Assignment was deterministic and applied in a fixed order, with the first match taking precedence. All skin-substitute products (Q4100-Q4399 and A2001-A2999) formed one class. Laboratory codes (four digits followed by U, codes ending in M, and 80000-89999) formed {N('cls.n_named_lab')} laboratory families in a separate stratum. {N('cls.n_named_service')} named service families were defined by explicit code lists, such as extended ambulatory electrocardiographic monitoring (93241-93248) and remote therapeutic monitoring. Drug and biologic codes were assigned to {N('cls.n_named_drug')} therapeutic classes when the HCPCS descriptor contained a listed molecule name, so that successor codes, new formulations, and biosimilars stayed together. "
 f"This approach has an important limit: only {N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes ({N('cls.share_codes_named')}) were assigned to the {N('cls.n_named')} named classes, and the remaining {N('cls.n_codes_single')} codes are single-code classes, for which class-level and code-level screening are identical. The mapping, keyword lists, and code lists are published as a CSV file. Class spending was the sum over member codes, and the class provider count was the sum across member codes, which overstates unique providers.",
 CONC,
 f"Screening approaches. {RULE} Units with no spending in year t were not eligible. " + THRESH + f" We report four approaches with consistent names. The prespecified code rule applies the rule to HCPCS codes and is the primary analysis. The prespecified class rule applies the same rule to classes using the pooled state HHI. The secondary class growth screen, also prespecified, applies only the spending and growth criteria to classes. The exploratory weighted-HHI rule applies the rule to classes using the spending-weighted mean member-code HHI; it was added after we observed that the pooled HHI was low for skin substitutes, is labeled exploratory throughout, and is a proposed approach rather than an established one. Laboratory codes were excluded from the primary analysis because single-laboratory billing makes them concentrated by design.",
 f"Outcomes and performance measures. For each flag year from 2020 through 2023, the eligible units were non-laboratory codes or classes with at least {N('param.spend_M')} in spending in year t. Review burden was the number of units flagged per year. We evaluated two class-level outcomes, {OUT_DEF}. Sensitivity was the share of outcome classes that were flagged, and PPV was the share of flagged classes that were outcome classes; a code flag detected a class when any member code was flagged, and PPV for the code rule was computed over the distinct classes containing a flagged code. We also report {GROWTH_DEF}; the flagged units are codes for the code rule and classes otherwise. Capture is also reported excluding skin substitutes, because that outcome informed the thresholds. Threshold sensitivity was assessed by varying all four code-level thresholds ({N('grid.n_combos')} combinations) for 2021 and 2022.",
 'Applied demonstration, ethics, and AI use. We applied the prespecified code rule to 2024 data, with growth measured from 2023. Providers are not identified. ' + NOTPROOF + ' Because the study used publicly available aggregate data, it did not constitute human participants research. Reporting followed the STROBE guideline where applicable. All reported numbers are generated by one script into a master results file and checked programmatically against the manuscript. ' + AI]),
('Results', [
 f"Code churn. Total allowed spending in the national rows of the 2024 file was {N('tot.allowed_2024_M')} across {N('tot.n_codes_2024')} codes. Skin-substitute allowed spending rose from {N('skin.allowed_2019_M')} ({N('skin.n_codes_2019')} codes) in 2019 to {N('skin.allowed_2020_M')} in 2020, {N('skin.allowed_2021_M')} in 2021, {N('skin.allowed_2022_M')} in 2022, {N('skin.allowed_2023_M')} in 2023, and {N('skin.allowed_2024_M')} ({N('skin.n_codes_2024')} codes) in 2024, consistent with CMS and OIG estimates of more than {N('ext.cms_skin_2024_B')}.¹,² The 2019 value is lower than the CMS figure of {N('ext.cms_skin_2019_M')}, which is based on more complete claims data. Codes first billed in 2023 or later accounted for {N('skin.vintage_2023plus_in_2024_M')} of 2024 spending, and {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes absent in 2021 (Figure 1).",
 f"Prespecified code rule. Using data through 2021, the rule flagged {N('lb21.n_flagged')} of {N('lb21.n_eligible')} eligible non-laboratory codes, {N('lb21.n_skin')} of them skin substitutes (Appendix Exhibit A1). Flagged-code spending rose {N('lb21.flagged_ratio')}-fold between 2021 and 2024, compared with {N('lb21.unflagged_ratio')}-fold for unflagged codes, but because of churn the 2021 flags captured {N('lb21.share_2024_skin_captured')} of 2024 skin-substitute spending, and the 2022 flags captured {N('lb22.share_2024_skin_captured')}. All {N('grid.n_combos')} threshold combinations flagged at least 1 skin-substitute code using 2021 data. Across flag years 2020 through 2023, the rule flagged {NR('code','units_flagged')} codes per year (mean, {N('tr.code.mean.units_flagged')}) and captured {N('tr.code.mean.share_of_positive_growth_captured')} of later growth (Table 1; Figure 2). For the doubling outcome, mean sensitivity was {N('tr.code.mean.O1_doubling_class_sens')} and PPV {N('tr.code.mean.O1_doubling_class_ppv')}; for the top-decile outcome, sensitivity was {N('tr.code.mean.O2_top_decile_increase_class_sens')} and PPV {N('tr.code.mean.O2_top_decile_increase_class_ppv')}.",
 f"Prespecified class rule and secondary class growth screen. Pooling products across states made the skin-substitute class look dispersed: its pooled HHI ranged from {N('skin.pooled_hhi_min_2020_2024')} to {N('skin.pooled_hhi_max_2020_2024')} between 2020 and 2024. The prespecified class rule flagged {NR('cpre','units_flagged')} classes per year, never flagged skin substitutes, and captured {N('tr.cpre.mean.share_of_positive_growth_captured')} of later growth. The secondary class growth screen flagged skin substitutes in {N('tr.cgr.n_years_flag_skin')} of {N('param.n_flag_years')} flag years (2020, 2021, and 2023), capturing all 2024 skin-substitute spending in those years. Its sensitivity for the doubling outcome was {N('tr.cgr.mean.O1_doubling_class_sens')}, compared with {N('tr.code.mean.O1_doubling_class_sens')} for the code rule, and it captured {N('tr.cgr.mean.share_of_positive_growth_captured')} of later growth, but it flagged {NR('cgr','units_flagged')} classes per year (mean, {N('tr.cgr.mean.units_flagged')}) and its PPV was {N('tr.cgr.mean.O1_doubling_class_ppv')}. "
 f"Of these flags, {NR('cgr','n_flagged_single_code_classes')} per year were single-code classes and {NR('cgr','n_flagged_named_classes')} were named classes ({N('tr.cgr.share_single_code_flags')} single-code across all years), so most of its added burden came from codes that class grouping did not change. Excluding skin substitutes, the classes it flagged declined on net between the flag year and 2024 ({N('tr.cgr.mean.share_of_positive_growth_captured_excl_skin')} of later growth), largely because they included time-limited COVID-19 pandemic surges, such as laboratory testing and telephone visits flagged in 2020, vaccine administration flagged in 2021, and over-the-counter test kits flagged in 2023.",
 f"Exploratory weighted-HHI rule. With concentration measured within products, the class rule flagged {N('tr.cw.min.units_flagged')} classes in every flag year, of which {NR('cw','n_flagged_named_classes')} were named classes, and flagged skin substitutes in {N('tr.cw.n_years_flag_skin')} of {N('param.n_flag_years')} flag years. It captured {N('tr.cw.mean.share_of_positive_growth_captured')} of later growth. " + WEIGHTED + f" Its sensitivity for the doubling outcome ({N('tr.cw.mean.O1_doubling_class_sens')}) was lower than that of the code rule, with a PPV of {N('tr.cw.mean.O1_doubling_class_ppv')}.",
 f"Flag year 2022. No approach flagged skin substitutes using 2022 data, when class growth slowed to {N('skin.growth_2022')}, and all approaches captured little of the later growth (range, {N('tr.y2022.min_growth_captured')} to {N('tr.y2022.max_growth_captured')}). Results for each year, including the number of single-code and named classes flagged, are in Appendix Exhibit A2.",
 f"Applied demonstration, 2024 data. The prespecified code rule flagged {N('wl.n_watch_nonlab_codes')} non-laboratory codes with {N('wl.watch_nonlab_allowed_2024_M')} in allowed spending (Table 2; full list in Appendix Exhibit A3). {N('wl.n_watch_skin_codes')} were skin-substitute products ({N('wl.watch_skin_allowed_2024_M')}), and {N('wl.n_new_codes_nonlab')} of the {N('wl.n_watch_nonlab_codes')} were first billed in 2024. The {N('wl.n_watch_other_codes')} other codes ({N('wl.watch_other_allowed_2024_M')}) were mostly recently coded drugs and biologics, together with complex chronic care management add-on time, tumor hyperthermia, and electronic brachytherapy. Only {N('wl.n_2023_flags_reflagged_2024')} of the {N('wl.n_2023_flags')} codes flagged in 2023 were flagged again in 2024. Provider-file rows existed for {N('wl.n_with_provider_rows_skin')} of {N('wl.n_watch_skin_codes')} skin-substitute codes and {N('wl.n_with_provider_rows_other')} of {N('wl.n_watch_other_codes')} other codes. For those codes, the rows represented a median of {N('wl.median_coverage_skin')} and {N('wl.median_coverage_other')} of national spending, respectively, and {N('wl.dollar_coverage_all')} of national spending across all {N('wl.n_watch_nonlab_codes')} codes. Reported top-10 provider shares (median, {N('wl.median_top10_share_skin')} for skin-substitute codes and {N('wl.median_top10_share_other')} for other codes) describe only this represented spending and are upper-biased where coverage is low. In the separate laboratory stratum, {N('wl.n_watch_lab_codes')} codes with {N('wl.watch_lab_allowed_2024_M')} in spending were flagged; these mainly reflect single-laboratory billing."]),
('Discussion', [
 'The central finding is a tradeoff created by code churn. A transparent, prespecified code-level rule placed skin substitutes on a short list using data through 2021, which CMS released in 2023, before 2024 spending more than doubled. However, most of the later spending was billed under codes that did not yet exist, so code-level flags captured little of it. Screening product classes followed the product across codes and recovered most of that spending, but without a concentration criterion it roughly doubled the review list and lowered PPV, and with pooled concentration it missed skin substitutes entirely.',
 'What was and was not shown. ' + DEM + ' ' + NOTDEM + ' The class map therefore functions as a skin-substitute grouping plus a small number of drug and service families, and its value elsewhere is untested.',
 f"The exploratory weighted-HHI rule kept the review list at {N('tr.cw.min.units_flagged')} classes per year while flagging skin substitutes in {N('tr.cw.n_years_flag_skin')} of {N('param.n_flag_years')} years. " + WEIGHTED + ' The measure was chosen after viewing the pooled results, and the thresholds were chosen with knowledge of the skin-substitute surge. A credible test requires prospective application with fixed definitions, for example to the 2025 and 2026 releases.',
 'Outside skin substitutes, no approach captured much later growth, and the secondary class growth screen often flagged surges that later reversed. This is an expected property of growth-based screens, and it argues for treating flags as prompts for review rather than as predictions. ' + NOTPROOF + ' Many flags reflect legitimate uptake of newly coded therapies, and laboratory codes are concentrated by design. The 2024 demonstration list should be read in that light, particularly because the 2026 payment change will reshape skin-substitute spending.',
 'Timeliness remains a constraint. The public files are released about 2 years after the service year. CMS and its contractors hold the same aggregates in near real time and could run published class-level rules internally, while independent researchers can audit them against public releases.',
 'Limitations. The files exclude Medicare Advantage, institutional, and supplier claims, suppress small cells, and attribute spending to the rendering-provider state. Provider files represented less than half of national spending for most flagged skin-substitute codes, so provider shares are imprecise. Allowed amounts are reconstructed from averages. Class assignment used descriptor keywords and explicit code lists and may misclassify some codes, and most codes remained single-code classes. The class provider count overstates unique providers. The evaluation includes one known outcome, the thresholds were chosen with knowledge of it, and the four flag years share overlapping follow-up periods ending in 2024, so they are not independent tests.']),
('Conclusion', [
 'Code churn limits code-level screening of public Medicare data. Grouping skin-substitute codes into one class addressed churn within that category, at a cost in review burden, but generalization to other categories was not demonstrated. The weighted-HHI measure is a post hoc proposal that should be tested prospectively before use.']),
]
EXLIST = ['Table 1. Review burden and detection by screening approach, mean of flag years 2020-2023.', 'Table 2. Applied demonstration: largest codes flagged by the prespecified code rule in 2024 data.',
          'Figure 1. Skin-substitute spending by code vintage, 2019-2024 (file fig1.pdf).', 'Figure 2. Review burden vs detection, flag years 2020-2023 (file fig2.pdf).',
          'Appendix Exhibits A1-A5 are in the separate supplementary file.']
T1CAP = ('Table 1. Review Burden and Detection by Screening Approach, Mean of Flag Years 2020-2023. Eligible units are non-laboratory codes or classes with at least $10 million in spending at the flag year. Doubling outcome: class spending in 2024 at least twice flag-year spending. '
         'Top-decile outcome: absolute increase from the flag year to 2024 in the top decile among eligible classes. A code flag detects a class if any member code is flagged; PPV for the code rule is computed over distinct classes containing a flagged code. '
         'Growth captured: net change in spending of flagged units from the flag year to 2024 divided by the summed positive change across eligible classes. The exploratory row was not prespecified. Captured spending does not indicate improper payment. PPV indicates positive predictive value.')
T2CAP = 'Table 2. Applied Demonstration: Largest Skin-Substitute and Other Non-Laboratory Codes Flagged by the Prespecified Code Rule in 2024 Data. Provider-file coverage is the share of national allowed spending represented in the provider file; top-10 shares describe only that represented spending. Flags indicate review priority, not improper payment. HHI indicates Herfindahl-Hirschman Index.'
LEG = ['Figure 1. Medicare Part B Allowed Spending on Skin-Substitute Products by the Year Each Product Code Was First Billed, 2019-2024. Source: CMS Medicare Physician & Other Practitioners by Geography and Service files, national rows.',
       'Figure 2. ' + FIGCAP.split('. ', 1)[1]]
paper_wc = build('long_paper_HealthAffairsScholar_SUBMISSION', P_TITLE, P_, REFS, tables=[(T1CAP, TT), (T2CAP, rows(X('table2_watchlist_top')))], legends=LEG, exhibit_list=EXLIST,
   front_extra=['Article type: Research article (Health Affairs Scholar). Main-text exhibits: 2 tables and 2 figures (limit 4); figures are supplied as separate files (fig1.pdf, fig2.pdf). Appendix Exhibits A1-A5 are in a separate supplementary file.', DS] + KT + KW_,
   counted=[t for h_, ps in P_[1:] for t in ps])
print('paper words', paper_wc, 'abstract', wc(ABS)); assert wc(ABS) <= 200, wc(ABS)
# appendix (supplementary file)
A5NOTE = (f"Worked example. HHI is the sum of squared state shares multiplied by {N('param.hhi_scale')}. The pooled HHI first sums all member-code spending by state; the weighted HHI is the sum of the Share x HHI column. "
          f"Illustrative (hypothetical) case: if a class contains {N('toy.n_products')} products with equal spending, each billed entirely in a different state, each product has an HHI of {N('toy.code_hhi')}, so the weighted mean is {N('toy.code_hhi')}, but each state holds {N('toy.state_share')} of pooled spending and the pooled HHI is {N('toy.pooled_hhi')}. "
          f"In the skin-substitute class in 2021, the pooled HHI was {N('ex.pooled_hhi')} and the weighted mean was {N('ex.wmean_hhi')}. The weighted measure is exploratory and post hoc; outside skin substitutes its advantage largely disappears (main text).")
build('long_paper_HealthAffairsScholar_appendix', 'Supplementary Appendix: ' + P_TITLE, [], [], authors=False,
      figs=[('figures/fig5_lookback.png', 'Appendix Exhibit A4. A, Skin-substitute allowed spending, 2019-2024. B, Ratio of 2024 to flag-year spending for non-laboratory codes flagged and not flagged by the prespecified code rule.')],
      tables=[('Appendix Exhibit A1. Non-laboratory codes flagged by the prespecified code rule using data through 2021.', rows(X('A1_flags_2021'))),
              ('Appendix Exhibit A2. Review burden and detection by flag year. Named classes are multi-code classes from the class map; single-code classes are codes that matched no class rule.', rows(X('A2_by_year'))),
              ('Appendix Exhibit A3. All non-laboratory codes flagged by the prespecified code rule in 2024 data.', rows(X('A3_watchlist_all'))),
              ('Appendix Exhibit A5. Worked example: pooled state HHI vs spending-weighted mean member-code HHI, skin-substitute class, 2021 (five largest member codes shown).', rows(X('A5_worked_example')), A5NOTE)])
APPX = [dict(kind='tab', cap='Appendix Exhibit A1. Non-laboratory codes flagged by the prespecified code rule using data through 2021.', rows=rows(X('A1_flags_2021'))),
        dict(kind='tab', land=True, fs=8, cap='Appendix Exhibit A2. Review burden and detection by flag year. Named classes are multi-code classes from the class map; single-code classes are codes that matched no class rule.', rows=rows(X('A2_by_year'))),
        dict(kind='tab', land=True, fs=8, cap='Appendix Exhibit A3. All non-laboratory codes flagged by the prespecified code rule in 2024 data.', rows=rows(X('A3_watchlist_all'))),
        dict(kind='fig', path='figures/fig5_lookback.png', cap='Appendix Exhibit A4. A, Skin-substitute allowed spending, 2019-2024. B, Ratio of 2024 to flag-year spending for non-laboratory codes flagged and not flagged by the prespecified code rule.'),
        dict(kind='tab', cap='Appendix Exhibit A5. Worked example: pooled state HHI vs spending-weighted mean member-code HHI, skin-substitute class, 2021 (five largest member codes shown).', rows=rows(X('A5_worked_example')), note=A5NOTE)]
build_inline('long_paper_HealthAffairsScholar_COMPLETE', P_TITLE, P_, REFS,
   inline=[('(Figure 1)', [dict(kind='fig', path='figures/fig6_skin_code_churn.png', cap=LEG[0], w=5.5)]),
           ('(Table 1; Figure 2)', [dict(kind='tab', land=True, cap=T1CAP, rows=TT), dict(kind='fig', land=True, path='figures/fig8_tradeoff.png', cap=LEG[1])]),
           ('(Table 2;', [dict(kind='tab', land=True, cap=T2CAP, rows=rows(X('table2_watchlist_top')))])],
   appendix=APPX, front_extra=['Reader version with exhibits placed in the text. The journal upload version is long_paper_HealthAffairsScholar_SUBMISSION.docx with figures in writeup/submission_figures/.', DS] + KT + KW_)
os.makedirs(W + 'submission_figures', exist_ok=True)
shutil.copy('figures/fig6_skin_code_churn.pdf', W + 'submission_figures/fig1.pdf'); shutil.copy('figures/fig8_tradeoff.pdf', W + 'submission_figures/fig2.pdf')
# ---------------- SGIM ----------------
S_TITLE = 'Screening Public Medicare Data for Spending Surges: Code Churn and the Review-Burden Tradeoff'
def A(s): return s.replace('≥', '>=').replace('≤', '<=').replace('−', '-').replace('–', '-')
S = [('Background', f"Medicare Part B skin-substitute spending exceeded {N('ext.cms_skin_2024_B')} in 2024, prompting federal warnings and payment reform. We retrospectively evaluated a transparent screen using public data available at each time, focusing on code churn and the tradeoff between screening codes and product classes."),
('Methods', f"We analyzed CMS Medicare Physician & Other Practitioners files (2019-2024). " + A(RULE).replace('Herfindahl-Hirschman Index (HHI)', 'Herfindahl-Hirschman Index (HHI)') + f" Thresholds were chosen with knowledge of the surge, and there is one known outcome, so this is not independent validation. We compared a prespecified code rule, a prespecified class rule, a secondary class growth screen, and an exploratory weighted-HHI rule (added post hoc) for flag years 2020 to 2023, measuring units flagged per year and sensitivity and positive predictive value (PPV) for classes whose spending doubled by 2024."),
('Results', f"Using 2021 data, the code rule flagged {N('lb21.n_flagged')} codes, {N('lb21.n_skin')} of them skin substitutes, but {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes absent in 2021, so the flags captured {N('lb21.share_2024_skin_captured')} of it. Across years, the code rule flagged {N('tr.code.mean.units_flagged')} codes per year (sensitivity {N('tr.code.mean.O1_doubling_class_sens')}, PPV {N('tr.code.mean.O1_doubling_class_ppv')}). The secondary class growth screen raised sensitivity to {N('tr.cgr.mean.O1_doubling_class_sens')} but flagged {N('tr.cgr.mean.units_flagged')} classes per year (PPV {N('tr.cgr.mean.O1_doubling_class_ppv')}), and {NR('cgr','n_flagged_single_code_classes')} of these per year were single-code classes. Only {N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes belonged to {N('cls.n_named')} named classes. The prespecified class rule never flagged skin substitutes because pooled HHI was low. The exploratory weighted-HHI rule flagged {N('tr.cw.min.units_flagged')} classes per year, but excluding skin substitutes it captured {N('tr.cw.mean.share_of_positive_growth_captured_excl_skin')} of later growth (code rule, {N('tr.code.mean.share_of_positive_growth_captured_excl_skin')}). All approaches missed the surge using 2022 data. In 2024 data, the code rule flagged {N('wl.n_watch_nonlab_codes')} non-laboratory codes ({N('wl.watch_nonlab_allowed_2024_M')})."),
('Conclusions', 'Grouping skin-substitute codes into one class addressed code churn within that category at a cost in review burden; generalization to other categories was not demonstrated. The weighted-HHI rule is a post hoc proposal that needs prospective testing. Flags indicate review priority, not improper payment.')]
S = [(h_, A(t)) for h_, t in S]
LO = ['Recognize how code churn and aggregation choices affect screening of Medicare spending for rapid, concentrated growth (Systems-Based Practice).',
      'Weigh sensitivity against review burden when interpreting public-data screens, and distinguish flags from evidence of improper payment (Practice-Based Learning and Improvement).']
sgim_chars = sum(len(t) for _, t in S); assert sgim_chars <= 3000, sgim_chars
assert all(ord(ch) < 128 for _, t in S for ch in t), 'non-ASCII in SGIM'
d = Document(); d.add_paragraph().add_run('SGIM 2027 Scientific Abstract (draft)').bold = True
d.add_paragraph('Title: ' + S_TITLE); d.add_paragraph('Authors: ' + AUTH); [d.add_paragraph(a) for a in AFF]
for h_, t in S: p = d.add_paragraph(); p.add_run(h_ + ': ').bold = True; p.add_run(t)
d.add_paragraph().add_run('Learning Objectives').bold = True; [d.add_paragraph(f'{i}. {x}') for i, x in enumerate(LO, 1)]
d.add_paragraph('Presentation format: No preference. Suggested primary category: Health Care Policy, Advocacy, and Health Services Research; secondary: Healthcare Delivery and Redesign [ALI TO CONFIRM in the SGIM27 ScholarOne list at submission]. Graphic: none.')
d.add_paragraph(f'Character count (Background through Conclusions, including spaces, excluding headings): {sgim_chars} of 3,000. Deadline: December 11, 2026, 11:59 PM ET.')
d.add_paragraph(AI)
d.save(W + 'abstract_SGIM2027.docx')
# ---------------- ARM ----------------
AH = [('Research Objective', f"Medicare Part B spending on skin substitutes grew from about {N('skin.allowed_2019_M')} in 2019 in public files to more than {N('ext.cms_skin_2024_B')} in 2024, prompting federal warnings and a payment overhaul. We retrospectively evaluated a transparent screen combining spending, growth, and concentration, applied only to public data available at each time, and quantified the tradeoff between sensitivity and review burden when screening codes or product classes."),
('Study Design', RULE.replace('In year t, the rule', 'The prespecified rule') + f" Thresholds were chosen with general knowledge of the surge, and there is one known outcome, so this is not an independent validation. We compared the {NAMES} (added post hoc) for flag years 2020 to 2023. Among units with at least {N('param.spend_M')}, we measured units flagged per year, growth captured, and sensitivity and positive predictive value (PPV) for classes whose spending doubled by 2024."),
('Population Studied', 'All HCPCS codes in CMS Medicare Physician & Other Practitioners by Geography and Service files (fee-for-service Part B professional claims, 2019-2024), with provider shares from the 2024 by Provider and Service file. Laboratory codes were analyzed separately.'),
('Principal Findings', f"Using 2021 data, the prespecified code rule flagged {N('lb21.n_flagged')} of {N('lb21.n_eligible')} eligible codes, {N('lb21.n_skin')} of them skin substitutes, but {N('churn.share_2024_skin_in_codes_absent_2021')} of 2024 skin-substitute spending was billed under codes absent in 2021, so these flags captured {N('lb21.share_2024_skin_captured')} of it. Across flag years, the code rule flagged {N('tr.code.mean.units_flagged')} codes per year, with {N('tr.code.mean.O1_doubling_class_sens')} sensitivity and {N('tr.code.mean.O1_doubling_class_ppv')} PPV. The secondary class growth screen raised sensitivity to {N('tr.cgr.mean.O1_doubling_class_sens')} but flagged {NR('cgr','units_flagged')} classes per year ({NR('cgr','n_flagged_single_code_classes')} single-code), with PPV of {N('tr.cgr.mean.O1_doubling_class_ppv')}. Only {N('cls.n_codes_named')} of {N('tot.n_codes_all_years')} codes belonged to named classes. The prespecified class rule never flagged skin substitutes, because pooling lowered HHI. The exploratory weighted-HHI rule captured {N('tr.cw.mean.share_of_positive_growth_captured_excl_skin')} of later growth outside skin substitutes, similar to the code rule. All approaches missed the surge using 2022 data."),
('Conclusions', 'Grouping skin-substitute codes into one class addressed code churn within that category at the cost of a longer review list; generalization to other categories was not demonstrated. The weighted-HHI rule is a post hoc proposal needing prospective testing.'),
('Implications for Policy or Practice', 'CMS and its contractors could run published class-level screens on current claims and should choose aggregation with review capacity in mind. Flags indicate review priority, not improper payment.')]
ah_words = sum(len(t.split()) for _, t in AH); assert ah_words <= 500, ah_words
d = Document(); d.add_paragraph().add_run('AcademyHealth ARM 2027 Abstract (draft)').bold = True
d.add_paragraph('Title: ' + S_TITLE)
d.add_paragraph('Suggested theme: [ALI TO SELECT from the ARM 2027 theme list when published; likely Medicare or payment policy]; Presentation: podium or poster. Authors are entered separately in the submission system; no author names or references appear in the abstract text. [ALI TO CONFIRM against the ARM 2027 call for abstracts once released.]')
for h_, t in AH: p = d.add_paragraph(); p.add_run(h_ + ': ').bold = True; p.add_run(t)
d.add_paragraph(f'Word count (excluding headings and title): {ah_words} of 500. 2027 ARM: June 12-15, 2027, Boston; abstract deadline not yet announced as of October 26, 2026.')
d.add_paragraph(AI)
d.save(W + 'abstract_AcademyHealth_ARM2027.docx')
for n in ['abstract_SGIM2027', 'abstract_AcademyHealth_ARM2027']:
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', W, W + n + '.docx'], capture_output=True)
json.dump({'letter_main_text_words': letter_wc, 'letter_limit': 800, 'paper_main_text_words': paper_wc, 'paper_limit': 4000, 'paper_abstract_words': wc(ABS), 'paper_abstract_limit': 200, 'paper_title_chars': len(P_TITLE), 'sgim_chars': sgim_chars, 'sgim_limit_chars': 3000, 'arm_words': ah_words, 'arm_limit': 500}, open(W + 'wordcounts.json', 'w'), indent=1)
print('sgim chars', sgim_chars, 'arm words', ah_words, 'titles', len(TITLE), len(P_TITLE), len(S_TITLE))
