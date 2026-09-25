# Record schema

One JSON object per country in `data/eaa-national-laws.json`. English values unless a field
ends in `_original` (the official-language wording). `null` means the act does not say, or it
could not be verified — `notes` explains which.

| Field | Meaning |
|---|---|
| `country`, `country_name` | ISO 3166-1 alpha-2 code and English name |
| `act.short` | Short name used in the README table |
| `act.title_original`, `act.title_en` | Title of the transposition act, and a faithful translation |
| `act.citation`, `act.url` | Gazette reference and link to the (consolidated, where available) official text |
| `act.applies_from` | Date the requirements apply to services |
| `secondary_acts[]` | Decrees, regulations or guidelines that matter for services |
| `authority_ecommerce` | Market-surveillance authority for e-commerce services: names, URL, legal basis. `null` if the act names none |
| `penalties.type` | Kind of sanction: administrative fine, criminal fine, contravention, periodic penalty only… |
| `penalties.summary_en` | What the act says for e-commerce service providers, in one or two sentences |
| `penalties.max_amount`, `penalties.currency` | Highest amount the act sets for service providers; `null` if it sets none |
| `penalties.basis` | Article(s) |
| `accessibility_information.where` | Where the provider must publish the Annex V information |
| `accessibility_information.basis` | Article(s) / annex |
| `microenterprise_exemption.exists`, `.basis` | Whether the service exemption for microenterprises is in the national act, and where |
| `transition` | Transitional periods for services |
| `notes` | Caveats, unverified points, noteworthy details |
| `sources[]` | Primary sources used |
| `verified` | Date the record was last checked |
