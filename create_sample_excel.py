"""
create_sample_excel.py
-----------------------
Run this once to generate data/products.xlsx with sample MS Fragrances inventory.
Safe to re-run — overwrites the existing file.
"""

import os
import pandas as pd

data = [
    # product_name, aliases, size, price_inr, stock, description
    ("Oud Al Shams", "oud, oud al shams, royal oud", "3ml",  350,  True,  "A rich and smoky Oud with warm amber base notes. Long-lasting and majestic."),
    ("Oud Al Shams", "oud, oud al shams, royal oud", "6ml",  620,  True,  "A rich and smoky Oud with warm amber base notes. Long-lasting and majestic."),
    ("Oud Al Shams", "oud, oud al shams, royal oud", "12ml", 1100, False, "A rich and smoky Oud with warm amber base notes. Long-lasting and majestic."),
    ("Rose Attar",   "rose, gulab, gulab attar",       "3ml",  280,  True,  "Pure distilled rose petals. Soft, fresh, and feminine with a dewy floral heart."),
    ("Rose Attar",   "rose, gulab, gulab attar",       "6ml",  500,  True,  "Pure distilled rose petals. Soft, fresh, and feminine with a dewy floral heart."),
    ("Rose Attar",   "rose, gulab, gulab attar",       "12ml", 900,  True,  "Pure distilled rose petals. Soft, fresh, and feminine with a dewy floral heart."),
    ("Musk Tahara",  "musk, white musk, musk tahara",  "3ml",  300,  True,  "Clean white musk with a hint of sandalwood. Ideal for everyday wear."),
    ("Musk Tahara",  "musk, white musk, musk tahara",  "6ml",  550,  True,  "Clean white musk with a hint of sandalwood. Ideal for everyday wear."),
    ("Musk Tahara",  "musk, white musk, musk tahara",  "12ml", 980,  False, "Clean white musk with a hint of sandalwood. Ideal for everyday wear."),
    ("Kesar Chandan","kesar, saffron, sandalwood, chandan", "6ml", 480, True, "Warm saffron meets creamy sandalwood. A classic unisex attar for special occasions."),
    ("Kesar Chandan","kesar, saffron, sandalwood, chandan", "12ml",850, True, "Warm saffron meets creamy sandalwood. A classic unisex attar for special occasions."),
    ("Jasmine Night", "jasmine, mogra, chameli",        "3ml",  260,  True,  "Intoxicating jasmine absolute for evening wear. Floral and exotic."),
    ("Jasmine Night", "jasmine, mogra, chameli",        "6ml",  460,  True,  "Intoxicating jasmine absolute for evening wear. Floral and exotic."),
    ("Jasmine Night", "jasmine, mogra, chameli",        "12ml", 820,  False, "Intoxicating jasmine absolute for evening wear. Floral and exotic."),
    ("Black Oud",    "black oud, dark oud, kala oud",   "6ml",  750,  True,  "Dark, resinous Oud blended with leather and spice. Bold and commanding."),
    ("Black Oud",    "black oud, dark oud, kala oud",   "12ml",1350,  True,  "Dark, resinous Oud blended with leather and spice. Bold and commanding."),
    ("Amber Bliss",  "amber, ambar, amber bliss",       "6ml",  420,  True,  "Sweet amber resin with vanilla undertones. Warm and enveloping."),
    ("Amber Bliss",  "amber, ambar, amber bliss",       "12ml", 760,  True,  "Sweet amber resin with vanilla undertones. Warm and enveloping."),
    ("Lavender Cool","lavender, lavendar",               "6ml",  390,  True,  "Fresh French lavender — calming, aromatic, and perfect for the office."),
    ("Lavender Cool","lavender, lavendar",               "12ml", 700,  False, "Fresh French lavender — calming, aromatic, and perfect for the office."),
]

columns = ["product_name", "aliases", "size", "price_inr", "in_stock", "description"]

df = pd.DataFrame(data, columns=columns)

os.makedirs("data", exist_ok=True)
df.to_excel("data/products.xlsx", index=False, engine="openpyxl")

print(f"✅  Created data/products.xlsx with {len(df)} rows.")
print(df.to_string(index=False))
