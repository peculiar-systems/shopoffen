#!/usr/bin/env python3
"""Build the README table and the CSV from eaa-national-laws.json (this folder).

The JSON is the source of truth (one record per country, see SCHEMA.md). Run after editing it:
    python3 build.py
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "eaa-national-laws.json"
CSV = HERE / "eaa-national-laws.csv"
README = HERE / "README.md"
START, END = "<!-- table:start -->", "<!-- table:end -->"


def money(p):
    if p.get("max_amount") is None:
        return "no amount in the act"
    return f"up to {p['max_amount']:,} {p['currency']}".replace(",", " ")


def main():
    records = sorted(json.loads(DATA.read_text(encoding="utf-8")), key=lambda r: r["country_name"])
    rows = []
    for r in records:
        a, p, auth = r["act"], r["penalties"], r.get("authority_ecommerce") or {}
        rows.append({
            "country": r["country"], "country_name": r["country_name"],
            "act": a["title_original"], "act_short": a["short"], "act_en": a["title_en"], "act_url": a["url"] or "",
            "authority": auth.get("name_original", ""), "authority_en": auth.get("name_en", ""),
            "penalty_type": p["type"], "penalty_max": "" if p.get("max_amount") is None else p["max_amount"],
            "currency": p["currency"], "penalty_summary": p["summary_en"],
            "information_where": r["accessibility_information"]["where"] or "",
            "microenterprise_exemption": r["microenterprise_exemption"]["basis"] if r["microenterprise_exemption"]["exists"] else "",
            "verified": r["verified"],
        })
    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    lines = ["| Country | Act | E-commerce authority | Penalties | Accessibility information |", "|---|---|---|---|---|"]
    for r in records:
        a, p, auth = r["act"], r["penalties"], r.get("authority_ecommerce")
        act = f"[{a['short']}]({a['url']})" if a["url"] else a["short"]
        who = auth["name_en"] if auth else "_not named in the act_"
        where = r["accessibility_information"]["where"] or "_not verified_"
        lines.append(f"| {r['country_name']} | {act} | {who} | {p['type']}, {money(p)} | {where} |")
    table = "\n".join(lines)
    text = README.read_text(encoding="utf-8")
    i, j = text.index(START) + len(START), text.index(END)
    README.write_text(text[:i] + "\n" + table + "\n" + text[j:], encoding="utf-8")
    print(f"{len(records)} countries → {CSV.name}, README table")


if __name__ == "__main__":
    main()
