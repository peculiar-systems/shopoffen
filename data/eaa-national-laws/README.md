# EAA national laws — e-commerce

How each EU country transposed the **European Accessibility Act** (Directive (EU) 2019/882) for
**e-commerce services**: the act, the authority that supervises online shops, the penalties,
where the shop has to publish its accessibility information, and the microenterprise exemption.

Every record was checked in the primary source — the national gazette or official legislation
portal — and carries its sources and the date it was verified. Where an act does not say
something (no fine amount, no named authority), the record says so instead of filling the gap
from secondary sources.

<!-- table:start -->
| Country | Act | E-commerce authority | Penalties | Accessibility information |
|---|---|---|---|---|
| Austria | [BaFG (BGBl. I Nr. 76/2023)](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20012316) | Federal Office for Social Affairs and Disability (Sozialministeriumservice) | administrative fine (Verwaltungsübertretung), up to 80 000 EUR | general terms and conditions or a similar document |
| Belgium | [Act of 5 Nov 2023 (CDE art. VIII.58–66)](https://www.ejustice.just.fgov.be/eli/loi/2023/11/05/2023046827/justel) | FPS Economy, SMEs, Self-employed and Energy – Directorate-General Economic Inspection | criminal fine (sanction de niveau 2 / niveau 3), may be settled by administrative fine, up to 25 000 EUR | _not verified_ |
| Cyprus | [L. 57(I)/2024](https://www.cylaw.org/nomoi/enop/non-ind/2024_1_57/full.html) | Deputy Minister of Social Welfare | administrative fine; also a criminal offence, up to 20 000 EUR | general terms or equivalent document |
| Czechia | [Act No. 424/2023 Coll.](https://e-sbirka.gov.cz/sb/2023/424) | Czech Trade Inspection Authority | administrative fine (offence), up to 10 000 000 CZK | general terms or equivalent document (also in audio form on request) |
| Denmark | [Act No. 801 of 7 June 2022](https://www.retsinformation.dk/eli/lta/2022/801) | Danish Safety Technology Authority | criminal fine, no amount in the act | general terms or equivalent document, in writing and orally |
| Finland | [Act 306/2019, ch. 3 a](https://www.finlex.fi/fi/lainsaadanto/2019/306) | Finnish Transport and Communications Agency | periodic penalty only, no amount in the act | stand-alone accessibility statement (saavutettavuusseloste); feedback answered within 2 weeks |
| France | [Law No. 2023-171, art. 16 (Consumer Code L. 412-13)](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000047281777) | Directorate-General for Competition Policy, Consumer Affairs and Fraud Control | contravention (criminal fine, 5th class), up to 7 500 EUR | general terms or equivalent document |
| Germany | [BFSG (BGBl. I 2021 S. 2970)](https://www.gesetze-im-internet.de/bfsg/) | Market Surveillance Authority of the Länder for the Accessibility of Products and Services (MLBF), Magdeburg | administrative fine (Ordnungswidrigkeit), up to 100 000 EUR | general terms and conditions (Allgemeine Geschäftsbedingungen) or in another clearly perceptible manner |
| Greece | [Law 4994/2022](https://eur-lex.europa.eu/legal-content/EL/TXT/PDF/?uri=CELEX:72019L0882GRC_202207302) | _not named in the act_ | administrative sanctions, no amount in the act | general terms or equivalent document |
| Hungary | [Act XVII of 2022 (Aktv.)](https://njt.hu/jogszabaly/2022-17-00-00) | consumer protection authority (Budapest and county government offices) | administrative fine after a warning, up to 500 000 000 HUF | general terms or equivalent document |
| Italy | [Legislative Decree No. 82/2022](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2022-05-27;82) | Agency for Digital Italy | administrative fine, up to 40 000 EUR | general terms or equivalent document |
| Netherlands | [Implementation Act (BW 6:230fa–fd)](https://wetten.overheid.nl/BWBR0049571/) | Netherlands Authority for Consumers and Markets (ACM) | administrative fine and/or periodic penalty payment (last onder dwangsom), up to 900 000 EUR | statute: information per Annex V of Directive (EU) 2019/882 (i.e. general terms and conditions or equivalent document); ACM guidance: an accessibility statement (verklaring) on the website/app, easy to find, itself accessible, in written and oral form |
| Poland | [Act of 26 April 2024 (Dz.U. 2024 poz. 731)](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20240000731) | Minister responsible for computerisation (Minister of Digital Affairs); in addition the President of the Management Board of the State Fund for Rehabilitation of Disabled Persons (PFRON) can inspect and fine | administrative fine (kara pieniężna), up to 89 035.6 PLN | terms of service (regulamin) or other equivalent document |
| Portugal | [Decree-Law No. 82/2022](https://files.dre.pt/1s/2022/12/23400/0010900132.pdf) | National Communications Authority | administrative offence (coima), no amount in the act | general terms or equivalent document, in writing and orally |
| Romania | [Law No. 232/2022](https://legislatie.just.ro/Public/DetaliiDocument/257778) | Romanian Digitalisation Authority | contravention fine, up to 15 000 RON | general terms or equivalent document, in writing and orally |
| Spain | [Law 11/2023](https://www.boe.es/buscar/act.php?id=BOE-A-2023-11022) | Surveillance authorities designated by each autonomous community (and Ceuta/Melilla); where none is designated, the Technical Support and Coordination Unit (UTAC) of the Directorate-General for the Rights of Persons with Disabilities | administrative fine, up to 1 000 000 EUR | general terms or equivalent document |
| Sweden | [Act 2023:254](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/lag-2023254-om-vissa-produkters-och-tjansters_sfs-2023-254/) | Swedish Post and Telecom Authority | administrative sanction fee, up to 10 000 000 SEK | general terms or equivalent document |
<!-- table:end -->

Data: [`eaa-national-laws.json`](eaa-national-laws.json) (full records, see
[SCHEMA.md](SCHEMA.md)) and [`eaa-national-laws.csv`](eaa-national-laws.csv) (one row per country).
After editing the JSON, run `python3 build.py` to refresh the CSV and the table above.

## Things worth knowing

- **Fines are ceilings, not practice.** The act took effect on 28 June 2025; published
  enforcement so far is mostly warnings, information requests and court cases brought by
  disability organisations, not administrative fines.
- **Most acts ask for the accessibility information in the general terms or an equivalent
  document** (Annex V of the directive). Finland's act requires a stand-alone accessibility
  statement; in the Netherlands the act refers to Annex V, and the regulator ACM describes it as a
  statement on the website or app.
- **Microenterprises** (fewer than 10 staff and at most €2 million turnover or balance sheet)
  providing services are exempt in every country listed here — in Belgium only until 28 June 2030.
- **Least verified: Belgium.** The official portals blocked automated access; the text was read
  from a copy of the Moniteur belge, and where the information has to be published is left open.
- **Penalty amounts can move.** Poland's cap is tied to the national average wage and changes
  every year; Hungary's depends on company size and turnover.

## Coverage

Currently 17 countries: the languages of [ShopOffen](https://shopoffen.peculiar.systems/) (this
repository), whose reports name each country's law, plus Austria, Belgium and Cyprus. Corrections and new countries are welcome — please open an issue or a pull request
with a link to the primary source for every statement.

## Not legal advice

These are informational summaries of the published texts as of the `verified` date. Laws change;
check the linked source before relying on a record.

## Licence

This data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — attribution:
"EAA national laws by Peculiar Systems". `build.py`: MIT. See the repository's [`LICENSE`](../../LICENSE).
