"""Analyse the cleaned data and create the charts.

Answers the question: which current player's (surnames A-C) signature
is worth the most on icons.com?

Reads data/clean_products.csv and saves charts to the charts folder.

Run:  python analyse.py  (after clean.py)
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

CLEAN_FILE = os.path.join("data", "clean_products.csv")
CHARTS_FOLDER = "charts"

BAR_COLOR = "#2f6fde"
TEXT_COLOR = "#333333"
MUTED_COLOR = "#767676"


def style_bar_chart(axes):
    """Give a horizontal bar chart a clean, quiet look."""
    for side in ["top", "right", "left"]:
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color("#cccccc")
    axes.tick_params(colors=TEXT_COLOR, length=0)
    axes.xaxis.grid(True, color="#e5e5e5", linewidth=0.8)
    axes.set_axisbelow(True)


def save_bar_chart(values, title, x_label, file_name, extra_labels=None):
    """Save one sorted horizontal bar chart with value labels."""
    values = values.sort_values()
    figure, axes = plt.subplots(figsize=(9, 5.5), dpi=150)
    bars = axes.barh(values.index, values, color=BAR_COLOR, height=0.62)
    style_bar_chart(axes)
    axes.set_title(title, loc="left", fontsize=12, color=TEXT_COLOR, pad=14)
    axes.set_xlabel(x_label, color=MUTED_COLOR, fontsize=9)

    # value label at the end of each bar
    for position, bar in enumerate(bars):
        label = "£%s" % format(round(bar.get_width()), ",")
        if extra_labels is not None:
            label += "  (%s)" % extra_labels[values.index[position]]
        axes.text(
            bar.get_width() + values.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=8,
            color=MUTED_COLOR,
        )
    axes.set_xlim(0, values.max() * 1.18)

    figure.tight_layout()
    path = os.path.join(CHARTS_FOLDER, file_name)
    figure.savefig(path)
    plt.close(figure)
    print("Saved chart:", path)


def main():
    data = pd.read_csv(CLEAN_FILE)
    os.makedirs(CHARTS_FOLDER, exist_ok=True)

    # a product only tells us about a player's signature value when it is
    # signed by that player alone and has a price
    signed = data[data["Signed By Player Only"] & data["Price (GBP)"].notna()]
    print("Products signed by a single A-C player:", len(signed))

    # ---- price statistics per player -------------------------------------
    stats = signed.groupby("Player")["Price (GBP)"].agg(
        products="count", median_price="median", mean_price="mean", max_price="max"
    )
    stats = stats.round(2).sort_values("median_price", ascending=False)
    print("\nPrice of signed products per player (GBP):")
    print(stats.to_string())

    top_player = stats.index[0]
    print("\nHighest typical (median) signed-product price:", top_player)

    # ---- chart 1: typical signed-product price ---------------------------
    save_bar_chart(
        stats["median_price"].head(10),
        "Typical price of a signed product, top 10 players (surnames A-C)",
        "Median price of products signed by the player alone (GBP) - (n products)",
        "1_median_price_per_player.png",
        extra_labels=stats["products"].astype(str) + " products",
    )

    # ---- chart 2: each player's most expensive item ----------------------
    save_bar_chart(
        stats["max_price"].sort_values(ascending=False).head(10),
        "Most expensive single signed item per player, top 10 (surnames A-C)",
        "Price of the player's most expensive signed item (GBP)",
        "2_most_expensive_items.png",
    )

    # ---- chart 3: signed shirts only (like-for-like comparison) ----------
    shirts = signed[signed["Product Type"] == "Signed shirts"]
    shirt_stats = shirts.groupby("Player")["Price (GBP)"].agg(["count", "median"])
    shirt_stats = shirt_stats[shirt_stats["count"] >= 3]  # need a few shirts to compare
    shirt_medians = shirt_stats["median"].sort_values(ascending=False)
    save_bar_chart(
        shirt_medians.head(10),
        "Signed shirts only: typical price per player (3+ shirts listed)",
        "Median signed-shirt price (GBP) - (n shirts)",
        "3_median_shirt_price_per_player.png",
        extra_labels=shirt_stats["count"].astype(str) + " shirts",
    )

    print("\nSigned shirts, highest median price:", shirt_medians.index[0])


if __name__ == "__main__":
    main()
