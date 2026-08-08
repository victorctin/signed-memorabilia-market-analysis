
# Victor Pavel, 18/07/2026
# Project: Collects every product listed for current players whose surname startwith A, B or C, and saves the raw data from icons.com.

import csv
import os
import re
import time
import unicodedata

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.icons.com"
PLAYER_INDEX_URL = BASE_URL + "/players/current-stars/a-k.html"
OUTPUT_FILE = os.path.join("data", "raw_products.csv")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
REQUEST_DELAY_SECONDS = 0.8  # be polite to the website
WANTED_LETTERS = ("A", "B", "C")
MAX_PAGES_PER_PLAYER = 20  # safety limit so we can never loop forever

# Name parts like "De" in "Kevin De Bruyne" belong to the surname,
# so his surname starts with D, not B.
SURNAME_PREFIXES = ("de", "van", "von", "di", "da", "del", "la", "le")

# Attribute rows that can describe the size of a product,
# checked in this order (most specific first).
SIZE_ATTRIBUTES = [
    "Size",
    "Shirt size",
    "Photo size",
    "Ball size",
    "Boot size",
    "Presentation size",
]

CSV_COLUMNS = [
    "Player",
    "Title",
    "Price",
    "Currency",
    "Availability",
    "Size",
    "Dispatch Time",
    "Product Type",
    "Signed By",
    "Presentation",
    "SKU",
    "Product URL",
]


def get_soup(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    time.sleep(REQUEST_DELAY_SECONDS)
    return BeautifulSoup(response.text, "html.parser")


def get_surname(full_name): # return the surname of a player, e.g "Kevin De Bruyne" to "De Bruyne".
    words = full_name.split()
    if len(words) == 1:
        return words[0]
    surname = words[-1]
    # keep prefixes such as "De" together with the surname
    if len(words) >= 3 and words[-2].lower() in SURNAME_PREFIXES:
        surname = words[-2] + " " + surname
    return surname


def strip_accents(text): # return the text with accents removed, e.g. "Álvarez" to "Alvarez"
    plain = unicodedata.normalize("NFKD", text)
    return "".join(char for char in plain if not unicodedata.combining(char))


def first_letter(text):
    return strip_accents(text)[:1].upper()


def get_players_a_to_c():
    soup = get_soup(PLAYER_INDEX_URL)
    players = []
    for item in soup.select("li.item.product.product-item"):
        link = item.select_one("div.text-center a")
        if link is None:
            continue
        name = link.get_text(strip=True)
        url = link["href"]
        surname = get_surname(name)
        if first_letter(surname) in WANTED_LETTERS:
            players.append((name, url))
    # sort by surname (accents removed) so the output file reads nicely
    players.sort(key=lambda player: strip_accents(get_surname(player[0])))
    return players


def get_product_urls(player_page_url):
    product_urls = []
    total_products = None

    for page_number in range(1, MAX_PAGES_PER_PLAYER + 1):
        if page_number == 1:
            page_url = player_page_url
        else:
            page_url = player_page_url + "?p=" + str(page_number)
        soup = get_soup(page_url)

        # the page reports how many products the player has in total
        progress = soup.select_one("#progressData")
        if progress is not None and progress.get("data-products-total"):
            total_products = int(progress["data-products-total"])

        found_new_product = False
        grid = soup.select_one("div.products-grid")
        if grid is None:
            break
        # a product card is a div on older pages and a form on newer ones,
        # select by class only
        for card in grid.select(".catalog-item"):
            link = card.find("a", href=True)
            if link is None:
                continue
            url = link["href"]
            if url not in product_urls:
                product_urls.append(url)
                found_new_product = True

        if not found_new_product:
            break
        if total_products is not None and len(product_urls) >= total_products:
            break

    return product_urls


def get_dispatch_time(presentation):
    if "framed" in presentation.lower() and "unframed" not in presentation.lower():
        return "1-5 working days"
    return "2 working days"


def scrape_product(product_url):
    soup = get_soup(product_url)

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    price_tag = soup.find("meta", attrs={"itemprop": "price"})
    price = price_tag["content"] if price_tag else ""
    currency_tag = soup.find("meta", attrs={"itemprop": "priceCurrency"})
    currency = currency_tag["content"] if currency_tag else ""

    availability_tag = soup.select_one('p[title="Availability"] span')
    availability = availability_tag.get_text(strip=True) if availability_tag else ""

    attributes = {}
    for row in soup.select("#product-attributes tr"):
        header = row.find("th")
        value = row.find("td")
        if header and value:
            attributes[header.get_text(strip=True)] = value.get_text(strip=True)

    size = ""
    for attribute_name in SIZE_ATTRIBUTES:
        if attribute_name in attributes:
            size = attributes[attribute_name]
            break

    presentation = attributes.get("Presentation type", "")

    return {
        "Title": title,
        "Price": price,
        "Currency": currency,
        "Availability": availability,
        "Size": size,
        "Dispatch Time": get_dispatch_time(presentation),
        "Product Type": attributes.get("Product type(s)", ""),
        "Signed By": attributes.get("Signed by", ""),
        "Presentation": presentation,
        "SKU": attributes.get("SKU", ""),
        "Product URL": product_url,
    }


def main():
    print("Loading player index:", PLAYER_INDEX_URL)
    players = get_players_a_to_c()
    print("Found %d players with surnames A-C" % len(players))

    rows = []
    product_cache = {}  # some products appear under more than one player

    for player_number, (player_name, player_url) in enumerate(players, start=1):
        print("[%d/%d] %s" % (player_number, len(players), player_name))
        try:
            product_urls = get_product_urls(player_url)
        except requests.RequestException as error:
            print("  could not load player page, skipping:", error)
            continue

        for product_url in product_urls:
            if product_url not in product_cache:
                try:
                    product_cache[product_url] = scrape_product(product_url)
                except requests.RequestException as error:
                    print("  could not load product, skipping:", product_url, error)
                    continue
            row = dict(product_cache[product_url])
            row["Player"] = player_name
            rows.append(row)
        print("  %d products" % len(product_urls))

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("Saved %d rows to %s" % (len(rows), OUTPUT_FILE))


if __name__ == "__main__":
    main()
