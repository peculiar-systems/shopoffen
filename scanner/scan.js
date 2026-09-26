#!/usr/bin/env node
/* ShopOffen — automated accessibility scan.
 *
 * Runs axe-core (in the report's language where axe ships one) over a shop's core
 * pages in headless Chromium and writes one JSON with every violation, tagged by page. Page discovery is
 * heuristic (category/product/cart links from the home page) and can be
 * overridden with an explicit page list.
 *
 * Usage:
 *   node scan.js https://shop.example.de
 *   node scan.js https://shop.example.de /kategorie /produkt/x /cart
 *   node scan.js --lang de https://shop.example.de     (axe messages in German; default English)
 * Output: out/scan-<host>-<date>.json
 */
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const dns = require("dns").promises;
const net = require("net");

// The scanner runs on a server next to other services and scans URLs strangers
// submit. Every request the browser makes is checked: only http(s) to hosts that
// resolve to public addresses. Anything private, loopback or link-local is aborted.
function isPrivateIp(ip) {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split(".").map(Number);
    return a === 10 || a === 127 || a === 0 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31)
      || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127) || a >= 224;
  }
  const v = ip.toLowerCase();
  if (v.startsWith("::ffff:")) return isPrivateIp(v.slice(7));
  return v === "::1" || v === "::" || v.startsWith("fc") || v.startsWith("fd") || v.startsWith("fe80");
}
const hostVerdict = new Map();
async function hostIsPublic(host) {
  if (hostVerdict.has(host)) return hostVerdict.get(host);
  let ok = false;
  try {
    const h = host.replace(/^\[|\]$/g, "");
    const addrs = net.isIP(h) ? [{ address: h }] : await dns.lookup(h, { all: true });
    ok = addrs.length > 0 && addrs.every(a => !isPrivateIp(a.address));
  } catch { ok = false; }
  hostVerdict.set(host, ok);
  return ok;
}
async function guard(page) {
  await page.setRequestInterception(true);
  page.on("request", async req => {
    let u;
    try { u = new URL(req.url()); } catch { return req.abort(); }
    if (u.protocol === "data:" || u.protocol === "blob:") return req.continue();
    if (!/^https?:$/.test(u.protocol)) return req.abort();
    return (await hostIsPublic(u.hostname)) ? req.continue() : req.abort();
  });
}


/* ---------- checks beyond axe: what used to be the manual self-check ---------- */

// WCAG 1.4.10 Reflow: at 320 CSS px wide nothing may need sideways scrolling.
async function reflowCheck(page) {
  await page.setViewport({ width: 320, height: 800 });
  await new Promise(r => setTimeout(r, 600));
  const res = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const sw = document.documentElement.scrollWidth;
    const off = [];
    if (sw > vw + 2) {
      for (const el of document.querySelectorAll("body *")) {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        if (r.right > vw + 2 && r.width > 0 && cs.position !== "fixed" && cs.visibility !== "hidden") {
          const parentOff = el.parentElement && el.parentElement.getBoundingClientRect().right > vw + 2;
          if (!parentOff) off.push((el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).slice(0, 2).join(".") : "")).slice(0, 90));
          if (off.length >= 4) break;
        }
      }
    }
    return { viewport: vw, scrollWidth: sw, overflow: sw > vw + 2, offenders: off };
  });
  await page.setViewport({ width: 1280, height: 900 });
  return res;
}

// Keyboard: Tab through the page, check that each stop visibly changes (WCAG 2.4.7) and that
// focus does not get stuck (2.1.2). Nothing is clicked or submitted.
async function keyboardCheck(page) {
  await page.evaluate(() => {
    const sel = 'a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"]), summary';
    const style = el => { const f = (x, pe) => { const c = getComputedStyle(x, pe); return [c.outlineStyle, c.outlineWidth, c.outlineColor, c.boxShadow, c.borderColor, c.backgroundColor, c.color, c.textDecorationLine, c.opacity, c.transform].join("|"); }; return [f(el), f(el, "::before"), f(el, "::after"), el.parentElement ? f(el.parentElement) : "", el.firstElementChild ? f(el.firstElementChild) : ""].join("#"); };
    window.__so = [];
    document.querySelectorAll(sel).forEach((el, i) => { el.dataset.soIdx = i; window.__so[i] = style(el); });
    if (document.activeElement) document.activeElement.blur();
    window.scrollTo(0, 0);
  });
  const focusable = await page.evaluate(() => window.__so.length);
  const stops = [];
  const LIMIT = Math.min(60, Math.max(focusable, 1) + 5);
  for (let i = 0; i < LIMIT; i++) {
    await page.keyboard.press("Tab");
    await new Promise(r => setTimeout(r, 60));
    const info = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return { body: true };
      const f = (x, pe) => { const c = getComputedStyle(x, pe); return [c.outlineStyle, c.outlineWidth, c.outlineColor, c.boxShadow, c.borderColor, c.backgroundColor, c.color, c.textDecorationLine, c.opacity, c.transform].join("|"); };
      const now = [f(el), f(el, "::before"), f(el, "::after"), el.parentElement ? f(el.parentElement) : "", el.firstElementChild ? f(el.firstElementChild) : ""].join("#");
      const idx = el.dataset ? el.dataset.soIdx : undefined;
      const before = idx !== undefined ? window.__so[idx] : null;
      const visible = before === null ? null : now !== before;
      el.scrollIntoView({ block: "center", inline: "nearest", behavior: "instant" });   // smooth scrolling would still be travelling
      const r = el.getBoundingClientRect();
      const label = (el.getAttribute("aria-label") || el.innerText || el.value || el.getAttribute("title") || el.tagName).trim().replace(/\s+/g, " ").slice(0, 60);
      // on screen and actually the thing at its own centre (not clipped away, not under a banner)
      const inView = r.width > 1 && r.height > 1 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
      const hit = inView ? document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2)), Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2))) : null;
      // elementFromPoint also "hits" opacity:0 menus — ask Chrome whether it is really visible
      const painted = typeof el.checkVisibility === "function" ? el.checkVisibility({ opacityProperty: true, visibilityProperty: true }) : true;
      const shown = painted && !!hit && (hit === el || el.contains(hit) || hit.contains(el));
      return { idx, tag: el.tagName.toLowerCase(), label, visible, shown };
    });
    stops.push(info);
  }
  const real = stops.filter(s => !s.body);
  const distinct = new Set(real.map(s => s.idx ?? s.label)).size;
  const noFocus = real.filter(s => s.shown && s.visible === false);
  const hidden = real.filter(s => !s.shown);
  // stuck: the last 15 stops cycle through three elements or fewer while the page has many more
  const tail = real.slice(-15).map(s => s.idx ?? s.label);
  const trapped = focusable > 10 && real.length >= 15 && new Set(tail).size <= 3;
  const uniq = arr => [...new Map(arr.map(s => [s.idx ?? s.label, s])).values()];
  return { focusable, reached: distinct, stops: real.length,
    hiddenStops: uniq(hidden).length, hiddenExamples: uniq(hidden).slice(0, 5).map(s => `${s.tag}: ${s.label}`),
    invisible: uniq(noFocus).length, invisibleExamples: uniq(noFocus).slice(0, 5).map(s => `${s.tag}: ${s.label}`), trapped, trapAt: trapped ? [...new Set(tail)].slice(0, 3).map(k => (real.find(s => (s.idx ?? s.label) === k) || {}).label) : [] };
}

const BUY_RE = /(add to (cart|bag|basket)|buy|warenkorb|kaufen|in den korb|panier|acheter|carrello|acquista|cesta|comprar|winkelwagen|bestellen|koszyk|kup|carrinho|cesto|encomendar|do košíku|do kosiku|koupit|varukorg|kundvagn|köp|læg i kurv|tilføj til kurv|køb|ostoskoriin|lisää koriin|\bosta\b|în coș|în coş|in cos|cumpără|cumpara|kosárba|megveszem|megrendelem|στο καλάθι|αγορ)/i;

// Screen reader: what the accessibility tree offers on the product page — heading, price, buy button.
async function screenReaderCheck(page) {
  const tree = await page.accessibility.snapshot({ interestingOnly: true });
  const nodes = [];
  (function walk(n) { if (!n) return; nodes.push(n); (n.children || []).forEach(walk); })(tree);
  if (nodes.length < 5) return { unavailable: true };   // bot wall or empty shell — say so, don't report "missing"
  const h1 = nodes.find(n => n.role === "heading" && n.level === 1);
  const buy = nodes.find(n => n.role === "button" && BUY_RE.test(n.name || ""));
  const priceRe = /(\d[\d.,\s]*\s?(€|eur|zł|pln|kr|sek|dkk|kč|czk|lei|ron|ft|huf|chf|£|\$))|((€|£|\$|kr\.?)\s?\d)/i;
  const price = nodes.find(n => (n.role === "StaticText" || n.role === "text" || n.role === "generic") && priceRe.test(n.name || ""));
  const unnamedButtons = nodes.filter(n => n.role === "button" && !(n.name || "").trim()).length;
  return { h1: h1 ? h1.name : null, buy: buy ? buy.name : null, price: price ? price.name.slice(0, 60) : null, unnamedButtons };
}

// Listen: the home page read out loud, top to bottom, the way a screen reader walks it. The full
// tree, not interestingOnly — Chrome drops unnamed images from the "interesting" one, and those are
// exactly what a blind shopper hears as a bare "image". Links, buttons and headings are read once,
// their inner text is not repeated.
async function listenCheck(page, toBuy) {
  const tree = await page.accessibility.snapshot({ interestingOnly: false });
  const SPOKEN = { image: "image", img: "image", link: "link", button: "button", heading: "heading",
    textbox: "edit", searchbox: "edit", combobox: "combo", checkbox: "checkbox", StaticText: "text" };
  const seq = [];
  (function walk(n) {
    if (!n || seq.length >= 5000) return;
    const kind = SPOKEN[n.role];
    const name = (n.name || "").replace(/\s+/g, " ").trim();
    if (kind && !(kind === "text" && !name)) {
      seq.push({ k: kind, n: name.slice(0, 70), ...(kind === "heading" && n.level ? { l: n.level } : {}) });
      if (kind !== "text") return;   // a named control is read once
    }
    (n.children || []).forEach(walk);
  })(tree);
  if (seq.length < 5) return { unavailable: true };
  // on the product page: how much the shopper sits through before the buy button
  const buyAt = toBuy ? seq.findIndex(s => s.k === "button" && BUY_RE.test(s.n)) : -1;
  const heard = buyAt >= 0 ? seq.slice(0, buyAt + 1) : seq;
  const unnamed = {};
  heard.forEach(s => { if (s.k !== "text" && s.k !== "heading" && !s.n) unnamed[s.k] = (unnamed[s.k] || 0) + 1; });
  // the stretch with the most bare words, when it lies past the start — that is what the shopper should hear
  const bare = s => s.k !== "text" && s.k !== "heading" && !s.n;
  let worst = null, most = 1;
  for (let i = 24; i + 12 <= heard.length; i++) {
    const c = heard.slice(i, i + 12).filter(bare).length;
    if (c > most) { most = c; worst = i; }
  }
  return { read: heard.length, unnamed, first: seq.slice(0, 24), ...(worst !== null ? { worst: heard.slice(worst, worst + 12), worstAt: worst + 1 } : {}),
    ...(buyAt >= 0 ? { buy: seq[buyAt].n } : {}) };
}

// Feedback channel: does the accessibility statement give a way to report barriers?
async function feedbackCheck(browser, href) {
  const page = await browser.newPage();
  await guard(page);
  try {
    await page.goto(href, { waitUntil: "networkidle2", timeout: 45000 });
    return await page.evaluate(() => {
      const mail = document.querySelector('a[href^="mailto:"]');
      const form = document.querySelector("form textarea, form input[type=email]");
      const tel = document.querySelector('a[href^="tel:"]');
      const text = document.body ? document.body.innerText : "";
      const emailInText = /[\w.+-]+@[\w-]+\.[\w.]+/.test(text);
      return { checked: true, email: !!mail || emailInText, form: !!form, phone: !!tel };
    });
  } catch (e) { return { checked: false, error: e.message.slice(0, 120) }; }
  finally { await page.close(); }
}

// Formal duty the authority starts with: is there a findable accessibility statement?
async function statementLinks(page) {
  return page.$$eval("a[href]", as => as
    // en, de, fr, it, es, nl, pl, pt, sv, da, cs, fi, ro, hu, el. A footer-style link: the word in a short link text
    // or in the link's own path — not a long card or teaser that merely mentions accessibility.
    .filter(a => {
      const re = /barrierefrei|zugänglichkeit|accessib|accesib|toegankelijk|dostępno|dostepno|acessibilidade|tillgänglig|tilgængelig|tilgaengelig|přístupnost|pristupnost|saavutettav|esteettöm|akadálymentes|akadalymentes|προσβασιμ|prosvasim/i;
      const text = (a.textContent || "").trim();
      let path = "";
      try { const u = new URL(a.href); path = u.protocol === "mailto:" ? u.href : u.pathname + u.hash; } catch {}
      return (text.length <= 60 && re.test(text)) || re.test(decodeURIComponent(path));
    })
    .slice(0, 5).map(a => ({ text: (a.textContent || "").trim().slice(0, 120), href: a.href })));
}

// axe ships Portuguese as pt_PT / pt_BR; languages it lacks (cs, fi, ro, hu) fall back to English
const AXE_LOCALE = { pt: "pt_PT" };

const AXE_PATH = require.resolve("axe-core/axe.min.js");

const PAGE_HINTS = [
  { key: "category", re: /(kategori|category|collections?|shop|produkte|sortiment|categor|colec|tuoteryhma|termekek|katigori|κατηγορ)/i },
  { key: "product", re: /(produkt|product|artikel|\/p\/|\/dp\/|produto|artigo|produs|zbozi|tuote|termek|proion|προϊόν)/i },
  { key: "cart", re: /(warenkorb|cart|basket|carrinho|cesto|kosik|varukorg|kundvagn|kurv|ostoskori|cos-de-cumparaturi|cosul|kosar|kalathi|καλάθι)/i },
  { key: "checkout", re: /(kasse|checkout|bestellen|finalizar|pagamento|pokladna|objednavka|kassa|tilaus|finalizare|penztar|megrendeles|tameio|oloklirosi|ταμείο)/i },
];

async function discover(page, base) {
  const links = await page.$$eval("a[href]", as => as.map(a => a.href));
  // Match hints against the path only — a host like "myshop.de" would otherwise make every
  // link look like a category — and skip links back to the page itself (#anchors).
  const home = new URL(base);
  const pathOf = h => { const u = new URL(h); return u.pathname + u.search; };
  const sameHost = links.filter(h => {
    try { const u = new URL(h); return u.host === home.host && u.pathname + u.search !== home.pathname + home.search; }
    catch { return false; }
  });
  const found = {};
  for (const { key, re } of PAGE_HINTS) {
    const hit = sameHost.find(h => re.test(pathOf(h)));
    if (hit) found[key] = hit.split("#")[0];
  }
  // a product link is often only on the category page — one level deeper
  if (found.category && !found.product) {
    try {
      await page.goto(found.category, { waitUntil: "networkidle2", timeout: 45000 });
      const deeper = await page.$$eval("a[href]", as => as.map(a => a.href));
      const hit = deeper.filter(h => { try { return new URL(h).host === home.host; } catch { return false; } })
        .find(h => PAGE_HINTS[1].re.test(pathOf(h)));
      if (hit) found.product = hit.split("#")[0];
    } catch {}
  }
  return found;
}

async function scanPage(browser, url, label, axeSource, locale) {
  const page = await browser.newPage();
  await guard(page);
  await page.setViewport({ width: 1280, height: 900 });
  await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36 ShopOffen-Scan/1.0");
  const result = { label, url, error: null, violations: [] };
  try {
    await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
    await page.evaluate(axeSource);
    const axeResult = await page.evaluate(async (loc) => {
      if (loc) window.axe.configure({ locale: loc });
      return await window.axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"] },
        resultTypes: ["violations"],   // node details for violations only; passes still come back, just thin
      });
    }, locale);
    result.violations = axeResult.violations.map(v => ({
      id: v.id, impact: v.impact, help: v.help, description: v.description,
      helpUrl: v.helpUrl, tags: v.tags,
      nodes: v.nodes.slice(0, 12).map(n => ({ target: n.target.join(" "), html: (n.html || "").slice(0, 240), summary: n.failureSummary })),
      nodeCount: v.nodes.length,
    }));
    // rules this page passed — the report leads with what already works
    result.passes = axeResult.passes.map(p => p.id);
    result.title = await page.title();
    result.reflow = await reflowCheck(page).catch(e => ({ error: e.message.slice(0, 120) }));
    if (label === "home") {
      await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 }).catch(() => {});
      result.listen = await listenCheck(page).catch(e => ({ error: e.message.slice(0, 120) }));
      result.keyboard = await keyboardCheck(page).catch(e => ({ error: e.message.slice(0, 120) }));
    }
    if (label === "product") {
      result.screenReader = await screenReaderCheck(page).catch(e => ({ error: e.message.slice(0, 120) }));
      result.listen = await listenCheck(page, true).catch(e => ({ error: e.message.slice(0, 120) }));
    }
  } catch (e) {
    result.error = e.message;
  }
  await page.close();
  return result;
}

(async () => {
  const argv = process.argv.slice(2);
  const li = argv.indexOf("--lang");
  const lang = li >= 0 ? argv.splice(li, 2)[1] : "en";
  const [base, ...explicit] = argv;
  if (!base) { console.error("usage: node scan.js [--lang xx] <shop-url> [paths...]"); process.exit(1); }
  const axeSource = fs.readFileSync(AXE_PATH, "utf8");
  let locale = null;   // English is axe's own language
  if (lang !== "en") {
    try { locale = JSON.parse(fs.readFileSync(require.resolve(`axe-core/locales/${AXE_LOCALE[lang] || lang}.json`), "utf8")); } catch {}
  }

  let baseUrl;
  try { baseUrl = new URL(base); } catch { console.error("not a URL:", base); process.exit(2); }
  if (!/^https?:$/.test(baseUrl.protocol) || !(await hostIsPublic(baseUrl.hostname))) {
    console.error("refused: not a public http(s) address:", base); process.exit(2);
  }
  const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox", `--lang=${lang}`] });
  const page = await browser.newPage();
  await guard(page);
  await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36 ShopOffen-Scan/1.0");
  await page.goto(base, { waitUntil: "networkidle2", timeout: 60000 });

  let targets = { home: base };
  if (explicit.length) {
    explicit.forEach((p, i) => { targets[`page${i + 1}`] = new URL(p, base).href; });
  } else {
    Object.assign(targets, await discover(page, base));
  }
  await page.goto(base, { waitUntil: "networkidle2", timeout: 60000 }).catch(() => {});
  const found = await statementLinks(page).catch(() => []);
  // a mailto "report a barrier" link is a feedback channel, not the statement itself
  const formal = { statement: found.filter(l => /^https?:/.test(l.href)), reportMail: found.some(l => l.href.startsWith("mailto:")) };
  await page.close();

  console.error("scanning:", Object.entries(targets).map(([k, v]) => `${k}=${v}`).join("  "));
  const results = [];
  for (const [label, url] of Object.entries(targets)) {
    results.push(await scanPage(browser, url, label, axeSource, locale));
    console.error(`  ${label}: ${results.at(-1).error ? "ERROR " + results.at(-1).error : results.at(-1).violations.length + " violation types"}`);
  }
  if (formal.statement.length) formal.feedback = await feedbackCheck(browser, formal.statement[0].href);
  if (formal.reportMail) formal.feedback = { ...(formal.feedback || {}), checked: true, email: true };
  await browser.close();

  const host = (new URL(base).host + new URL(base).pathname.replace(/\/$/, "").replace(/\//g, "_")).replace(/[^a-z0-9._-]/gi, "");
  const outDir = path.join(__dirname, "out");
  fs.mkdirSync(outDir, { recursive: true });
  const out = path.join(outDir, `scan-${host}-${new Date().toISOString().slice(0, 10)}.json`);
  fs.writeFileSync(out, JSON.stringify({ base, scannedAt: new Date().toISOString(), formal, pages: results }, null, 1));
  console.log(out);
})();
