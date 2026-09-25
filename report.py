#!/usr/bin/env python3
"""ShopOffen — report generator.

Turns the axe scan JSON into one branded HTML report: automated findings, the
accessibility-statement check, a self-check list for what no scanner sees, and a
statement template. Free and fully automatic since 2026-09-24 — no manual testing.

Every word a reader sees comes from i18n/<lang>.json (plus the template it names), so a
new language is one JSON file and one template, no code. Finding titles come from axe's own
locale; for languages axe does not ship (cs, fi, ro, hu) the JSON carries `rule_titles`.
Rule references (EN 301 549 / WCAG) are language-neutral and live in i18n/_refs.json. A legal frame can differ by
country inside a language: "de" picks Austria's for .at shops.

Usage:
    python3 report.py scanner/out/scan-<host>-<date>.json [--lang en|de|…] [--country at]
Output: out/Bericht-<host>-<date>.html
"""
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
I18N = HERE / "i18n"

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3, None: 4}

# What already works, in words a shop owner reads: each line stands for a group of axe rules and
# shows only when every rule of the group that applied to the shop passed on every page.
GOOD_GROUPS = {
    "images": ["image-alt", "role-img-alt", "svg-img-alt", "input-image-alt", "area-alt", "object-alt"],
    "contrast": ["color-contrast"],
    "language": ["html-has-lang", "html-lang-valid", "valid-lang"],
    "titles": ["document-title"],
    "links": ["link-name"],
    "buttons": ["button-name"],
    "forms": ["label", "select-name", "form-field-multiple-labels"],
    "zoom": ["meta-viewport"],
    "headings": ["page-has-heading-one", "heading-order", "empty-heading"],
    "structure": ["landmark-one-main", "region", "bypass"],
    "aria": ["aria-allowed-attr", "aria-required-attr", "aria-valid-attr-value", "aria-valid-attr", "aria-roles", "aria-hidden-focus", "aria-hidden-body"],
    "lists": ["list", "listitem"],
    "frames": ["frame-title"],
    "focus_order": ["tabindex"],
    "nesting": ["nested-interactive"],
}

CSS = """
:root{--bg:oklch(0.991 0.006 95);--bg-2:oklch(0.975 0.008 95);--surface:#fff;--ink:oklch(0.21 0.012 270);--ink-soft:oklch(0.43 0.012 270);
--ink-faint:oklch(0.5 0.012 270);--line:oklch(0.9 0.008 95);--line-strong:oklch(0.83 0.01 95);--blue:oklch(0.55 0.15 258);--blue-strong:oklch(0.46 0.14 258);
--lime:oklch(0.86 0.21 124);--lime-strong:oklch(0.77 0.2 124);--magenta:#B4145F;--magenta-deep:#9B1152;--blue-tint:oklch(0.95 0.03 258);--radius:16px;--maxw:860px}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"Geist",system-ui,sans-serif;font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100dvh;display:flex;flex-direction:column}
a{color:var(--blue-strong);text-decoration:underline;text-underline-offset:3px}
:focus-visible{outline:2.5px solid var(--blue);outline-offset:3px;border-radius:5px}
.skip{position:absolute;left:-9999px;top:8px;background:var(--ink);color:#fff;padding:8px 14px;border-radius:8px;z-index:99}.skip:focus{left:12px}
.wrap{width:100%;max-width:var(--maxw);margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:"Bricolage Grotesque",system-ui,sans-serif;letter-spacing:-0.02em;line-height:1.1}
.nav{border-bottom:1px solid var(--line);background:oklch(0.991 0.006 95 / 0.9)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:64px}
.brand{font-family:"Bricolage Grotesque", system-ui, sans-serif;font-weight:800;font-size:20px;color:var(--ink);text-decoration:none}.brand .dot{color:var(--blue)}
.btn{background:var(--lime);color:var(--ink);font-weight:600;font-size:14.5px;padding:9px 16px;border-radius:11px;text-decoration:none}
.hero{padding:44px 0 8px}
.tag{display:inline-flex;align-items:center;gap:8px;font-family:"Geist Mono", ui-monospace, monospace;font-size:12.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-soft)}
.dot-s{width:8px;height:8px;border-radius:50%;background:var(--blue)}
.hero h1{font-size:clamp(32px,6vw,48px);font-weight:800;margin:12px 0 10px;overflow-wrap:anywhere}
.meta{color:var(--ink-soft);font-size:14px}
.summary{display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:space-between;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px 26px;margin:26px 0 6px}
.big{display:flex;align-items:center;gap:16px}.big span{font-family:"Bricolage Grotesque", system-ui, sans-serif;font-size:60px;font-weight:800;line-height:1}
.big p{font-weight:600}.big small{font-weight:400;color:var(--ink-soft);font-size:13.5px}
ul.sum{list-style:none;display:grid;gap:6px}ul.sum li{display:flex;align-items:center;justify-content:space-between;gap:18px;min-width:170px}
.score{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:24px 26px;margin:26px 0 6px}
.score-top{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px}.score-top b{font-family:"Bricolage Grotesque", system-ui, sans-serif;font-size:clamp(24px,4vw,32px);font-weight:800;letter-spacing:-.02em}
.level{font-family:"Geist Mono", ui-monospace, monospace;font-size:12px;text-transform:uppercase;letter-spacing:.06em;padding:4px 10px;border-radius:99px;background:var(--lime);color:var(--ink)}
.score.grow .level{background:var(--line)}
.bar{height:10px;border-radius:99px;background:var(--bg-2);border:1px solid var(--line);overflow:hidden;margin:14px 0}.bar i{display:block;height:100%;background:var(--lime-strong);border-radius:99px}
.score p{color:var(--ink-soft)}
.share{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:16px;font-size:14px}.share span{color:var(--ink-soft);margin-right:4px}
.share a,.share button{border:1px solid var(--line-strong);border-radius:10px;padding:6px 12px;text-decoration:none;color:var(--ink);font-weight:500;font:inherit;background:var(--surface);cursor:pointer}
.share a.primary{background:var(--lime);border-color:var(--lime);font-weight:600}
.fwd{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px 24px}.fwd p{color:var(--ink-soft);max-width:62ch}.fwd .share{margin-top:14px}
ul.good{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
ul.good li{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 14px 12px 40px;position:relative;font-weight:500}
ul.good li::before{content:"✓";position:absolute;left:12px;top:12px;width:18px;height:18px;border-radius:50%;background:var(--lime);color:var(--ink);font-size:11px;font-weight:700;display:grid;place-items:center;line-height:1}
.sumrow{margin-bottom:6px}.sumrow .lead{margin-bottom:8px}.sumrow ul.sum{display:flex;flex-wrap:wrap;gap:8px}.sumrow ul.sum li{min-width:0}
section{margin-top:40px}
h2{font-size:26px;font-weight:800;margin-bottom:14px}
.lead{color:var(--ink-soft);margin-bottom:14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:18px 22px;margin:12px 0;page-break-inside:avoid}
.card-head{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin-bottom:6px}
.card h3{font-size:17.5px;font-weight:700}
.pill{font-family:"Geist Mono", ui-monospace, monospace;font-size:11.5px;font-weight:500;letter-spacing:.03em;text-transform:uppercase;border-radius:99px;padding:3px 10px;white-space:nowrap}
/* studio palette only: magenta = act on it, blue = worth a look, lime = fine, line grey = neutral */
.pill.critical{background:var(--magenta-deep);color:#fff}.pill.serious,.pill.issue{background:var(--magenta);color:#fff}
.pill.moderate{background:var(--blue-strong);color:#fff}.pill.look{background:var(--blue-tint);color:var(--blue-strong)}
.pill.minor,.pill.na,.pill.self{background:var(--line);color:var(--ink-soft)}.pill.ok{background:var(--lime);color:var(--ink)}
.where{font-size:13px;color:var(--ink-soft)}.ref{font-family:"Geist Mono", ui-monospace, monospace;color:var(--blue-strong)}
ul.nodes{margin:10px 0 0 18px;font-size:13px;color:var(--ink-soft);overflow-wrap:anywhere}ul.nodes li{margin:4px 0}
code,.html{font-family:"Geist Mono",ui-monospace,monospace;font-size:12px}.html{display:block;color:var(--ink-faint)}
.more{font-size:13px;color:var(--ink-soft)}
table.sr{border-collapse:collapse;margin-top:6px;font-size:14.5px}table.sr th{text-align:left;font-weight:500;color:var(--ink-soft);padding:4px 16px 4px 0;vertical-align:top}table.sr td{font-weight:600;padding:4px 0}
.note{background:var(--bg-2);border:1px solid var(--line);border-radius:var(--radius);padding:16px 20px;font-size:14px;color:var(--ink-soft)}
details{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 20px}
summary{cursor:pointer;font-weight:600;color:var(--blue-strong)}
pre.tpl{white-space:pre-wrap;font-family:"Geist Mono", ui-monospace, monospace;font-size:12.5px;line-height:1.55;margin-top:14px;color:var(--ink)}
footer{border-top:1px solid var(--line);margin-top:56px;padding:24px 0;font-family:"Geist Mono", ui-monospace, monospace;font-size:12px;color:var(--ink-soft)}
.foot-inner{display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between}
@media print{.nav,.btn,.skip{display:none}body{background:#fff}}
"""


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wcag_ref(tags):
    """axe tags like 'wcag111' → 'WCAG 1.1.1'; rules outside WCAG are axe best practices."""
    for tag in tags:
        d = tag[4:]
        if tag.startswith("wcag") and d.isdigit() and len(d) >= 3:
            return f"WCAG {d[0]}.{d[1]}.{d[2:]}"
    return "Best Practice"


def fill(text, **kw):
    """Replace only the named {placeholders} — templates keep their own {BRACES}."""
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text


# "Copy link" is the one script a report carries. The worker's report CSP allows exactly this
# text by hash (SHOP_REPORT_JS in _worker.js) — change one, recompute the other. The buttons are
# rendered hidden and only shown by this script, so without it nothing dead is on the page.
COPY_JS = ("document.querySelectorAll('[data-copy]').forEach(function(b){b.hidden=false;"
           "b.addEventListener('click',function(){navigator.clipboard.writeText(b.dataset.copy)"
           ".then(function(){b.textContent=b.dataset.done})})})")


def attr(s):
    return esc(s).replace('"', "&quot;")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    args = [a for i, a in enumerate(sys.argv[1:], 1)
            if not a.startswith("--") and sys.argv[i - 1] not in ("--lang", "--country")]
    lang = arg("--lang", "de")
    L = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    refs = json.loads((I18N / "_refs.json").read_text(encoding="utf-8"))
    t = L["t"]

    scan = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    host = scan["base"].split("//")[-1].strip("/")
    # inside a language the country can differ: .at shops get Austria's law in German, .be Belgium's in French/Dutch
    tld = host.split("/")[0].rsplit(".", 1)[-1]
    country = arg("--country") or (tld if tld in L["legal"] else "default")
    legal = L["legal"].get(country, L["legal"]["default"])

    findings = [(p["label"], p["url"], v) for p in scan["pages"] for v in p["violations"]]
    findings.sort(key=lambda f: IMPACT_ORDER.get(f[2]["impact"], 4))
    counts = {}
    for _, _, v in findings:
        counts[v["impact"] or "minor"] = counts.get(v["impact"] or "minor", 0) + 1
    formal = scan.get("formal") or {}
    statement = formal.get("statement") or []
    failed = [p for p in scan["pages"] if p.get("error")]
    home = next((p for p in scan["pages"] if p["label"] == "home"), scan["pages"][0])
    share_url = arg("--share-url")
    product = next((p for p in scan["pages"] if p["label"] == "product"), None)

    # ---- score: axe rules that applied (passed or failed anywhere) + the robot checks ----
    ok_pages = [p for p in scan["pages"] if not p.get("error")]
    failed_rules = {v["id"] for p in ok_pages for v in p["violations"]}
    passed_rules = {r for p in ok_pages for r in p.get("passes", [])} - failed_rules
    rf = [p for p in scan["pages"] if isinstance(p.get("reflow"), dict) and "overflow" in p["reflow"]]
    kb = home.get("keyboard") if isinstance(home.get("keyboard"), dict) and "focusable" in home.get("keyboard", {}) else None
    sr = product.get("screenReader") if product else None
    sr_ok = isinstance(sr, dict) and "h1" in sr and not sr.get("unavailable")
    fb = formal.get("feedback")
    robot = {  # True passed · False failed · None not scored
        "reflow": (not any(p["reflow"]["overflow"] for p in rf)) if rf else None,
        "keyboard": (not kb.get("trapped") and not kb.get("hiddenStops")) if kb else None,
        "statement": bool(statement),
        "feedback": (bool(fb.get("email") or fb.get("form") or fb.get("phone")) if fb and fb.get("checked") else None),
        "screen_reader": (all(sr.get(k) for k in ("h1", "price", "buy")) and not sr.get("unnamedButtons")) if sr_ok else None,
    }
    scored = [v for v in robot.values() if v is not None]
    total_checks = len(passed_rules | failed_rules) + len(scored)
    passed_checks = len(passed_rules) + sum(scored)
    ratio = passed_checks / total_checks if total_checks else 0
    level = "excellent" if ratio >= 0.95 else "strong" if ratio >= 0.85 else "good" if ratio >= 0.7 else "grow"
    good = [k for k, rules in GOOD_GROUPS.items() if (set(rules) & passed_rules) and not (set(rules) & failed_rules)]
    good += [k for k, v in robot.items() if v]

    def pill(kind, text):
        return f"<span class='pill {kind}'>{esc(text)}</span>"

    def card(kind, label, title, inner):
        return f"<article class='card'><div class='card-head'>{pill(kind, label)}<h3>{esc(title)}</h3></div>{inner}</article>"

    def items(xs):
        return "<ul class='nodes'>" + "".join(f"<li><code>{esc(x)}</code></li>" for x in xs) + "</ul>" if xs else ""

    # ---- hero: the score first, then what is good, then what to fix ----
    summary_rows = "".join(
        f"<li>{pill(i, str(counts[i]) + ' × ' + L['impact'][i])}</li>" for i in ("critical", "serious", "moderate", "minor") if counts.get(i))
    score_line = fill(t["score"], p=passed_checks, n=total_checks)
    share = forward = script = ""
    if share_url:
        from urllib.parse import quote
        law_short = legal.get("law_short", legal["law"])
        vals = dict(host=host, p=passed_checks, n=total_checks, law=law_short, url=share_url)
        copy_btn = (f'<button type="button" hidden data-copy="{attr(share_url)}" data-done="{attr(t["share_copied"])}">'
                    f'{esc(t["share_copy"])}</button>')
        if level in ("excellent", "strong"):
            # a result worth showing off: the public post, plus the link people actually paste
            share = (f"<div class='share'><span>{esc(t['share_h'])}</span>"
                     f"<a href='https://www.linkedin.com/sharing/share-offsite/?url={quote(share_url)}' target='_blank' rel='noopener'>LinkedIn</a>"
                     f"{copy_btn}</div>")
        else:
            # nobody posts a weak score; they forward it to whoever will fix it
            share = f"<div class='share'><a class='primary' href='#forward'>{esc(t['fwd_cta'])}</a></div>"
        mail = f"mailto:?subject={quote(fill(t['fwd_subject'], **vals))}&amp;body={quote(fill(t['fwd_body'], **vals))}"
        wa = f"https://wa.me/?text={quote(fill(t['fwd_wa_text'], **vals))}"
        forward = (f"<section id='forward'><h2>{esc(t['fwd_h'])}</h2><div class='fwd'><p>{esc(t['fwd_intro'])}</p>"
                   f"<div class='share'><a href='{mail}'>{esc(t['share_mail'])}</a>"
                   f"<a href='{wa}' target='_blank' rel='noopener'>WhatsApp</a>{copy_btn}</div></div></section>")
        script = f"<script>{COPY_JS}</script>"
    body = f"""
<header class="hero">
  <span class="tag"><span class="dot-s"></span>{esc(t["h1"])}</span>
  <h1>{esc(host)}</h1>
  <p class="meta">{fill(t["meta"], host=esc(host), date=date.today().strftime(L["date_fmt"]), law=esc(legal["law"]), authority=esc(legal["authority"]))}</p>
  <div class="score {level}">
    <div class="score-top"><span class="level">{esc(t["level_" + level])}</span><b>{esc(score_line)}</b></div>
    <div class="bar" role="img" aria-label="{esc(score_line)}"><i style="width:{round(ratio * 100)}%"></i></div>
    <p>{esc(t["lead_" + level])}</p>
    {share}
  </div>
</header>"""
    if failed:
        body += f"<p class='note'>{fill(esc(t['unreachable']), urls=', '.join(esc(p['url']) for p in failed))}</p>"
    if good:
        body += f"<section><h2>{esc(t['h_good'])}</h2><ul class='good'>" + "".join(f"<li>{esc(L['good'][k])}</li>" for k in good if k in L["good"]) + "</ul></section>"

    # ---- axe findings ----
    body += (f"<section><h2>{esc(t['h_fix'])}</h2>"
             f"<div class='sumrow'><p class='lead'>{fill(esc(t['fix_intro']), n=len(findings))}</p><ul class='sum'>{summary_rows}</ul></div>") if findings else ""
    for label, url, v in findings:
        expl = L["rules"].get(v["id"], v["description"])
        ref = refs.get(v["id"]) or wcag_ref(v["tags"])
        imp = v["impact"] or "minor"
        nodes = "".join(f"<li><code>{esc(n['target'])}</code><span class='html'>{esc(n['html'])}</span></li>" for n in v["nodes"][:6])
        more = f"<p class='more'>{fill(esc(t['more']), n=v['nodeCount'] - 6)}</p>" if v["nodeCount"] > 6 else ""
        body += card(imp, L["impact"].get(imp, "—"), L.get("rule_titles", {}).get(v["id"], v["help"]),
                     f"<p class='where'><span class='ref'>{esc(ref)}</span> · {esc(t['page'])}: {esc(label)} · ×{v['nodeCount']}</p>"
                     f"<p>{esc(expl)}</p><ul class='nodes'>{nodes}</ul>{more}")
    body += "</section>" if findings else ""

    # ---- robot checks: reflow, keyboard, screen reader ----
    body += f"<section><h2>{esc(t['h_auto2'])}</h2><p class='lead'>{esc(t['auto2_intro'])}</p>"
    rf = [p for p in scan["pages"] if isinstance(p.get("reflow"), dict) and "overflow" in p["reflow"]]
    bad = [p for p in rf if p["reflow"]["overflow"]]
    if not rf:
        body += card("na", t["na"], t["reflow_t"], "")
    elif bad:
        offs = list(dict.fromkeys(o for p in bad for o in p["reflow"]["offenders"]))[:6]
        body += card("issue", t["issue"], t["reflow_t"], f"<p>{fill(esc(t['reflow_bad']), pages=esc(', '.join(p['label'] for p in bad)))}</p>{items(offs)}")
    else:
        body += card("ok", t["pass"], t["reflow_t"], f"<p>{esc(t['reflow_ok'])}</p>")

    kb = home.get("keyboard") if isinstance(home.get("keyboard"), dict) else None
    if not kb or "focusable" not in kb:
        body += card("na", t["na"], t["kb_t"], "")
    else:
        inner = f"<p>{fill(esc(t['kb_reach']), reached=kb['reached'], focusable=kb['focusable'], stops=kb.get('stops', kb['reached']))}</p>"
        kind, label = "ok", t["pass"]
        if kb.get("trapped"):
            inner += f"<p>{fill(esc(t['kb_trap']), items=esc(' · '.join(x or '?' for x in kb['trapAt'])))}</p>"
            kind, label = "issue", t["issue"]
        if kb.get("hiddenStops"):
            inner += f"<p>{fill(esc(t['kb_hidden']), n=kb['hiddenStops'])}</p>{items(kb['hiddenExamples'])}"
            kind, label = "issue", t["issue"]
        if kb.get("invisible"):
            inner += f"<p>{fill(esc(t['kb_invisible']), n=kb['invisible'])}</p>{items(kb['invisibleExamples'])}"
            if kind == "ok":
                kind, label = "look", t["look"]
        if kind == "ok":
            inner += f"<p>{esc(t['kb_ok'])}</p>"
        body += card(kind, label, t["kb_t"], inner)

    sr = product.get("screenReader") if product else None
    if not product:
        body += card("na", t["na"], t["sr_t"], f"<p>{esc(t['sr_none'])}</p>")
    elif not isinstance(sr, dict) or sr.get("unavailable") or "h1" not in sr:
        body += card("na", t["na"], t["sr_t"], f"<p>{esc(t['sr_unavailable'])}</p>")
    else:
        missing = [k for k in ("h1", "price", "buy") if not sr.get(k)]
        rows = "".join(f"<tr><th>{esc(t['sr_' + k])}</th><td>{esc(sr.get(k) or t['sr_missing'])}</td></tr>" for k in ("h1", "price", "buy"))
        extra = f"<p>{fill(esc(t['sr_unnamed']), n=sr['unnamedButtons'])}</p>" if sr.get("unnamedButtons") else ""
        kind = "issue" if (missing or sr.get("unnamedButtons")) else "ok"
        body += card(kind, t["issue"] if kind == "issue" else t["pass"], t["sr_t"], f"<table class='sr'>{rows}</table>{extra}")
    body += "</section>"

    # ---- formal duties ----
    body += f"<section><h2>{esc(t['h_formal'])}</h2>"
    if statement:
        links = "".join(f"<li><a href='{esc(l['href'])}'>{esc(l['text'] or l['href'])}</a></li>" for l in statement)
        body += card("ok", t["found"], t["statement_link"], f"<p>{esc(t['statement_found'])}</p><ul class='nodes'>{links}</ul>")
    else:
        body += card("issue", t["not_found"], t["statement_link"], f"<p>{esc(t['statement_missing'])}</p>")
    fb = formal.get("feedback")
    if fb and fb.get("checked"):
        how = [t[k] for k, on in (("fb_email", fb.get("email")), ("fb_form", fb.get("form")), ("fb_phone", fb.get("phone"))) if on]
        body += (card("ok", t["found"], t["fb_t"], f"<p>{fill(esc(t['fb_ok']), how=esc(', '.join(how)))}</p>") if how
                 else card("issue", t["not_found"], t["fb_t"], f"<p>{esc(t['fb_bad'])}</p>"))
    else:
        body += card("na", t["na"], t["fb_t"], f"<p>{esc(t['fb_unchecked'])}</p>")
    body += "</section>"
    body += forward

    # ---- what is left for a person ----
    body += f"<section><h2>{esc(t['h_self'])}</h2><p class='lead'>{esc(t['self_intro'])}</p>"
    for title, how in L["self_checks"]:
        body += card("self", t["self_pill"], title, f"<p>{esc(how)}</p>")
    body += "</section>"

    template = (HERE / L["template"]).read_text(encoding="utf-8").split("\n---\n", 1)[-1].strip()
    body += (f"<section><h2>{esc(t['h_template'])}</h2><p class='lead'>{esc(t['template_intro'])}</p>"
             f"<details><summary>{esc(t['template_show'])}</summary><pre class='tpl'>{esc(template)}</pre></details></section>")
    body += f"<section><h2>{esc(t['h_frame'])}</h2><p class='note'>{fill(esc(t['frame']), authority=esc(legal['authority']), law=esc(legal['law']), fine=esc(legal['fine']))}</p></section>"

    home_url = "https://shopoffen.peculiar.systems/" + ("" if lang == "en" else lang)
    html = f"""<!DOCTYPE html><html lang="{L['html_lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{fill(esc(t['doc_title']), host=esc(host))}</title>
<meta property="og:title" content="{esc(fill(t['share_text'], host=host, p=passed_checks, n=total_checks))}"><meta property="og:description" content="{esc(t['og_desc'])}">
<meta property="og:image" content="https://peculiar.systems/og.png"><meta name="twitter:card" content="summary_large_image"><meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">{esc(t.get('skip', 'Skip to content'))}</a>
<nav class="nav"><div class="wrap nav-inner"><a class="brand" href="{home_url}">ShopOffen<span class="dot">.</span></a><a class="btn" href="{home_url}#get">{esc(t.get('again', 'New check'))} →</a></div></nav>
<!--email_off--><main id="main" class="wrap">{body}</main><!--/email_off-->
<footer><div class="wrap foot-inner"><span>© Peculiar Systems</span><span>{esc(t['footer'])}</span></div></footer>
{script}</body></html>"""

    OUT.mkdir(exist_ok=True)
    out = OUT / f"Bericht-{host.replace('/', '_')}-{date.today().isoformat()}.html"
    out.write_text(html, encoding="utf-8")
    print(f"{out}  ({len(findings)} findings, {lang}/{country})")


if __name__ == "__main__":
    main()
