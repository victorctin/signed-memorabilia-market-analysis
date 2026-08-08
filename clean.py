"""Clean the raw scraped data.

Reads data/raw_products.csv, fixes types, removes duplicates and adds
helper columns, then saves the result to data/clean_products.csv.

Run:  python clean.py  (after scrape.py)
"""

import os
import unicodedata

import pandas as pd

RAW_FILE = os.path.join("data", "raw_products.csv")
CLEAN_FILE = os.path.join("data", "clean_products.csv")

TEXT_COLUMNS = [
    "Player",
    "Title",
    "Availability",
    "Size",
    "Dispatch Time",
    "Product Type",
    "Signed By",
    "Presentation",
    "SKU",
]


def strip_accents(text):
    """Return the text with accents removed, e.g. "Álvarez" -> "Alvarez"."""
    plain = unicodedata.normalize("NFKD", str(text))
    return "".join(char for char in plain if not unicodedata.combining(char))


def signed_by_player_only(row):
    """True when the product is signed by the page's player and nobody else."""
    player = strip_accents(row["Player"]).lower()
    signed_by = strip_accents(row["Signed By"]).lower()
    return signed_by == player


def main():
    data = pd.read_csv(RAW_FILE)
    print("Raw rows:", len(data))

    # tidy up the text columns
    for column in TEXT_COLUMNS:
        data[column] = data[column].fillna("").astype(str).str.strip()

    # price as a number we can calculate with
    data["Price (GBP)"] = pd.to_numeric(data["Price"], errors="coerce")
    missing_price = data["Price (GBP)"].isna().sum()
    if missing_price:
        print("Rows without a usable price:", missing_price)

    # one row per player + product (the same product should not
    # appear twice for the same player)
    before = len(data)
    data = data.drop_duplicates(subset=["Player", "Product URL"])
    if len(data) < before:
        print("Removed duplicate rows:", before - len(data))

    # helper columns for the analysis
    data["Signed By Player Only"] = data.apply(signed_by_player_only, axis=1)
    data["In Stock"] = data["Availability"].str.lower() == "in stock"

    data.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
    print("Clean rows:", len(data))
    print("Players:", data["Player"].nunique())
    print("Saved to", CLEAN_FILE)


if __name__ == "__main__":
    main()
