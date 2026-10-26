const pptxgen = require('pptxgenjs');
const p = new pptxgen(); p.defineLayout({ name: 'P', width: 48, height: 36 }); p.layout = 'P';
const s = p.addSlide(); const F = 'Arial', NAVY = '1F3A5F', RED = 'B2182B', BLUE = '2166AC', GREY = '262626', TINT = 'EEF3F8';
const ROOT = process.env.ROOT || '/workspace/research/medicare';
const FIG = ROOT + '/figures/';
const MR = require(ROOT + '/tables/master_results.json');
const N = id => { if (!(id in MR)) throw new Error('missing ' + id); return MR[id].display; };
const R = (a, c) => N(`tr.${a}.min.${c}`) + ' to ' + N(`tr.${a}.max.${c}`);
const M = 1.0, G = 1.0, W = (48 - 2 * M - 2 * G) / 3, X = [M, M + W + G, M + 2 * (W + G)];
const TOP = 10.4, BOT = 35.0, BODY = 34;
// header
s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 48, h: 5.6, fill: { color: NAVY }, line: { color: NAVY } });
s.addText('Screening Public Medicare Data for Spending Surges: Code Churn and the Review-Burden Tradeoff', { x: M, y: 0.35, w: 48 - 2 * M, h: 3.5, fontFace: F, fontSize: 84, bold: true, color: 'FFFFFF', valign: 'middle', margin: 0 });
s.addText('Ali Mirza, B.S.¹; [ALI TO CONFIRM: coauthor]²    ¹University of Connecticut School of Medicine, Farmington, CT   ²[ALI TO CONFIRM: affiliation]', { x: M, y: 4.0, w: 48 - 2 * M, h: 1.2, fontFace: F, fontSize: 40, color: 'DCE6F0', valign: 'middle', margin: 0 });
// stat band (all numbers from tables/master_results.json)
const stats = [[N('churn.share_2024_skin_in_codes_absent_2021'), 'of 2024 skin-substitute spending was billed under codes that did not exist in 2021'],
  [`${N('tr.code.mean.O1_doubling_class_sens')} vs ${N('tr.cgr.mean.O1_doubling_class_sens')}`, 'sensitivity for later doubling: prespecified code rule vs secondary class growth screen (2020-2023 mean)'],
  [`${N('tr.code.mean.units_flagged')} vs ${N('tr.cgr.mean.units_flagged')}`, 'units flagged per year (review burden): prespecified code rule vs secondary class growth screen']];
stats.forEach((st, i) => { const x = X[i], y = 6.3, h = 3.2;
  s.addShape(p.ShapeType.rect, { x, y, w: W, h, fill: { color: TINT }, line: { color: TINT } });
  s.addShape(p.ShapeType.rect, { x, y, w: 0.25, h, fill: { color: RED }, line: { color: RED } });
  s.addText(st[0], { x: x + 0.7, y: y + 0.25, w: W - 1.0, h: 1.45, fontFace: F, fontSize: 72, bold: true, color: RED, valign: 'middle', margin: 0 });
  s.addText(st[1], { x: x + 0.7, y: y + 1.75, w: W - 1.0, h: 1.25, fontFace: F, fontSize: 34, color: GREY, valign: 'top', margin: 0 }); });
// flow helpers: estimate text height, then justify blocks within column so all share TOP and BOT
const lines = (t, size, w) => t.split('\n').reduce((a, para) => a + Math.max(1, Math.ceil(para.length * size * 0.5 / 72 / w)), 0);
const th = (t, size, w) => lines(t, size, w) * size * 1.08 / 72 + 0.1;
const GAP = 0.9;
function column(x, blocks) {
  let hs = blocks.map(b => b.h(W)); const total = hs.reduce((a, b) => a + b, 0);
  let spare = BOT - TOP - total - GAP * (blocks.length - 1);
  const flex = blocks.findIndex(b => b.flex); let gap = GAP;
  if (flex >= 0) { hs[flex] += spare; } else { gap = GAP + spare / (blocks.length - 1); }
  console.log('col', x.toFixed(1), 'spare', spare.toFixed(2), 'gap', gap.toFixed(2));
  let y = TOP; blocks.forEach((b, i) => { b.draw(x, y, hs[i]); y += hs[i] + gap; });
}
const head = t => ({ h: () => 1.45, draw: (x, y) => {
  s.addText(t, { x, y, w: W, h: 1.1, fontFace: F, fontSize: 48, bold: true, color: NAVY, margin: 0, valign: 'bottom' });
  s.addShape(p.ShapeType.line, { x, y: y + 1.25, w: W, h: 0, line: { color: NAVY, width: 3 } }); } });
const para = (t, size = BODY, color = GREY) => ({ h: w => th(t, size, w), draw: (x, y, h) =>
  s.addText(t, { x, y, w: W, h, fontFace: F, fontSize: size, color, valign: 'top', margin: 0 }) });
const sect = (title, t, size) => { const a = head(title), b = para(t, size); return { h: w => 1.9 + b.h(w), draw: (x, y, h) => { a.draw(x, y); b.draw(x, y + 1.9, h - 1.9); } }; };
const img = (path, ar, cap) => { const c = para(cap, 28, '555555'); return { flex: true, h: w => w / ar + 0.3 + c.h(w), draw: (x, y, h) => {
  const ih = Math.min(h - 0.3 - c.h(W), W / ar), iw = ih * ar; s.addImage({ path, x: x + (W - iw) / 2, y, w: iw, h: ih }); c.draw(x, y + ih + 0.3, c.h(W)); } }; };
const headimg = (t, path, ar, cap) => { const a = head(t), b = img(path, ar, cap); return { flex: true, h: w => 1.9 + b.h(w), draw: (x, y, h) => { a.draw(x, y); b.draw(x, y + 1.9, h - 1.9); } }; };
const box = (title, t) => { const pad = 0.5, iw = W - 2 * pad; const hh = () => 0.9 + th(t, BODY, iw) + 2 * pad;
  return { h: hh, draw: (x, y, h) => { s.addShape(p.ShapeType.rect, { x, y, w: W, h, fill: { color: TINT }, line: { color: BLUE, width: 2.5 } });
    s.addText(title, { x: x + pad, y: y + pad, w: iw, h: 0.8, fontFace: F, fontSize: 36, bold: true, color: BLUE, margin: 0, valign: 'top' });
    s.addText(t, { x: x + pad, y: y + pad + 0.9, w: iw, h: h - 2 * pad - 0.9, fontFace: F, fontSize: BODY, color: GREY, margin: 0, valign: 'top' }); } }; };
column(X[0], [
  sect('Background', `Medicare Part B spending on skin substitutes grew from ${N('skin.allowed_2019_M')} in 2019 (public files; CMS reports ${N('ext.cms_skin_2019_M')}) to more than ${N('ext.cms_skin_2024_B')} in 2024, prompting a federal Inspector General warning and a 2026 payment overhaul. We retrospectively evaluated a transparent screen using only public data available at each time, focusing on code churn and the tradeoff between screening codes and product classes.`),
  sect('Methods', `Data were the CMS Medicare Physician & Other Practitioners files by Geography and Service (2019-2024) and by Provider and Service (2024). Spending is the allowed amount from national rows. Product classes grouped all skin substitutes, ${N('cls.n_named_drug')} drug classes, and ${N('cls.n_named_service')} service families; only ${N('cls.n_codes_named')} of ${N('tot.n_codes_all_years')} codes fell in named classes, and the rest were single-code classes. Laboratory codes were analyzed separately. For flag years 2020-2023 we counted units flagged and measured sensitivity and PPV for classes whose spending doubled by 2024.`),
  box('Prespecified code rule (year t)', `Flag a unit with at least ${N('param.spend_M')} in allowed spending, at least ${N('param.growth')} growth from the prior year (or no prior-year spending), and a state HHI of at least ${N('param.hhi')} or no more than ${N('param.providers')} rendering providers. Prespecified class rule: the same rule on classes (pooled HHI). Secondary class growth screen: classes, without concentration. Exploratory weighted-HHI rule (post hoc): spending-weighted HHI of member codes.`),
  sect('Limitations', 'Thresholds were chosen with knowledge of the surge, and there is one known outcome, so this is not independent validation. The data exclude Medicare Advantage, facility, and supplier claims; small cells are suppressed; files are released about two years late. Sources: data.cms.gov; HHS OIG OEI-BL-24-00420; CMS CY2026 PFS final rule.'),
]);
column(X[1], [
  headimg('Code Churn', FIG + 'fig6_skin_code_churn.png', 1800 / 1440, 'Figure 1. Skin-substitute allowed spending by the year each product code was first billed.'),
  para(`Using 2021 data, the prespecified code rule flagged ${N('lb21.n_flagged')} of ${N('lb21.n_eligible')} eligible codes, ${N('lb21.n_skin')} of them skin substitutes. Because most later spending moved to new codes, these flags captured only ${N('lb21.share_2024_skin_captured')} of 2024 skin-substitute spending. Pooling products into one class diluted state concentration (HHI ${N('skin.pooled_hhi_min_2020_2024')} to ${N('skin.pooled_hhi_max_2020_2024')}), so the prespecified class rule never flagged skin substitutes.`),
  box('What was and was not shown', `Demonstrated: grouping skin-substitute codes into one class addressed churn within that category. Not demonstrated: generalization to other categories; ${R('cgr', 'n_flagged_single_code_classes')} of each year's growth-screen flags were single-code classes.`),
]);
column(X[2], [
  headimg('Review Burden vs Detection', FIG + 'fig8_tradeoff_poster.png', 1400 / 1720, 'Figure 2. Each point is one approach in one flag year (2020-2023). Triangles are exploratory.'),
  sect('Results and Conclusions', `The secondary class growth screen flagged ${R('cgr', 'units_flagged')} classes per year (PPV ${N('tr.cgr.mean.O1_doubling_class_ppv')} vs ${N('tr.code.mean.O1_doubling_class_ppv')} for the code rule). The exploratory weighted-HHI rule flagged ${N('tr.cw.min.units_flagged')} classes per year, but outside skin substitutes it captured ${N('tr.cw.mean.share_of_positive_growth_captured_excl_skin')} of later growth (code rule, ${N('tr.code.mean.share_of_positive_growth_captured_excl_skin')}); a post hoc proposal. In 2024 data the code rule flagged ${N('wl.n_watch_nonlab_codes')} non-laboratory codes (${N('wl.watch_nonlab_allowed_2024_M')}). Flags are review priorities, not evidence of improper payment.`),
]);
p.writeFile({ fileName: 'poster_SGIM2027_48x36.pptx' }).then(() => console.log('written'));
