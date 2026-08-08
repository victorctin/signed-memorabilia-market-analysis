# Icons.com Signed Memorabilia — Data Analyst Assessment

Which current footballer's signature (surnames A–C) is worth the most on
[icons.com](https://www.icons.com/)?

The pipeline scrapes every product listed for current players with surnames
A–C, cleans the data, and answers the question with charts.
Findings are in [REPORT.md](REPORT.md).

## Project structure

```
scrape.py            step 1 - collect the raw data from icons.com
clean.py             step 2 - clean the raw data
analyse.py           step 3 - statistics + charts
data/raw_products.csv     raw scraped data (one row per player + product)
data/clean_products.csv   cleaned data used for the analysis
charts/              the three output charts (PNG)
REPORT.md            findings report
```

## How to run

```
pip install -r requirements.txt
python scrape.py     # ~15-20 minutes (polite 0.8s delay between requests)
python clean.py
python analyse.py
```

## What the scraper collects

For every product listed on an A–C player's page:
**Title, Price, Availability, Size, Dispatch Time, Product Type, Signed By,
Presentation** — plus Player, Currency, SKU and Product URL for traceability.

## Decisions worth knowing

- **Player list**: taken from the "Current Stars A–K" index. Surname = last
  word of the name ("Casemiro" counts as C); name parts like "De" stay with
  the surname, so Kevin De Bruyne is D and excluded; accents are ignored
  ("Álvarez" is A). 32 players qualify.
- **Dispatch Time**: icons.com no longer shows a dispatch time per product.
  It is derived from the site's own delivery policy: framed items
  "take between one and five working days", everything else is dispatched
  "within two working days".
- **Size**: the site uses several size fields (Shirt/Photo/Ball/Presentation
  size). The most specific one available is used.
- **Duplicate products**: items signed by two players (e.g. dual-framed
  shirts) are listed under both players. They stay in the raw data, but the
  analysis only compares products signed by one player alone, so a
  two-signature price never counts as one player's signature value.
