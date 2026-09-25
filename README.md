# ShopOffen

A free, automated accessibility check for online shops under the European Accessibility Act
(Directive (EU) 2019/882). This is the scanner and report generator behind
**[shopoffen.peculiar.systems](https://shopoffen.peculiar.systems/)** — use the hosted version,
or run it yourself.

It opens a shop's home, category, product and cart pages in headless Chromium, runs
[axe-core](https://github.com/dequelabs/axe-core) against WCAG 2.1 AA / EN 301 549, and adds a few
checks axe does not do:

- **Reflow** — does the page work at 320 px without horizontal scrolling?
- **Keyboard** — a Tab walk through the home page: is focus visible, are there hidden stops or traps?
- **Screen reader** — does the product page expose a heading, a price and a named buy button?
- **Accessibility information** — is it linked from the home page, and does it offer a way to report barriers?

The report is written for the shop owner, not the developer: what already works first, then
what to fix, each finding with the page, the element and how to fix it — plus a template for
the accessibility information the EAA asks for (Annex V).

## Languages and national law

Reports come in the shop's own language. Each names the country's own transposition act,
supervisory authority and penalties, checked in the national gazettes:

`en` `de` (+ `at`) `fr` (+ `be`) `it` `es` `nl` (+ `be`) `pl` `pt` `cs` `sv` `da` `fi` `ro` `hu` `el` (+ `cy`)

The legal data is also published as a dataset with sources — act, authority, penalties, where to
publish the accessibility information, microenterprise exemption — for 17 countries in
[`data/eaa-national-laws/`](data/eaa-national-laws/) (JSON and CSV).

## Run it

Needs Node.js 18+ and Python 3.9+ (standard library only).

```sh
cd scanner && npm install && cd ..
node scanner/scan.js --lang de https://shop.example.de        # → scanner/out/scan-<host>-<date>.json
python3 report.py scanner/out/scan-shop.example.de-2026-09-25.json --lang de   # → out/Bericht-<host>-<date>.html
```

- `--lang` picks the report language (default `de` for `report.py`, `en` for the scanner).
- `--country at|be|cy` picks another country's law inside a language; by default it follows the shop's top-level domain.
- Page discovery is heuristic. Pass paths explicitly if it picks the wrong pages:
  `node scanner/scan.js https://shop.example /collections/all /products/x /cart`

The scanner only follows public addresses: every request the browser makes is checked, and
anything that resolves to a private, loopback or link-local address is aborted.

## What it is not

An automated check finds only part of what a manual audit would. A clean report is a good
first pass, **not a certificate of conformity and not legal advice**. The report says so, and
it recommends against accessibility overlays (see the
[European Disability Forum's statement](https://www.edf-feph.org/publications/joint-statement-on-accessibility-overlays/)).

## Adding a language

A language is data, not code: `i18n/<lang>.json` (same keys as `en.json`, with a `legal` block
per country) and `templates/statement-<lang>.md`. For languages axe-core has no locale for,
add `rule_titles` to the JSON so finding titles are translated too. Please cite the primary
source for every legal statement.

## Licence

Code (`scanner/`, `report.py`, `build.py`): MIT. Report texts, templates and data (`i18n/`,
`templates/`, `data/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` and `LICENSE-CONTENT`.

Made by [Peculiar Systems](https://peculiar.systems), an independent software studio.
