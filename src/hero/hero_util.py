import csv
from hero.hero import Hero
from pathlib import Path

def get_all_heros_from_csv():
    heros = []
    # CSV Import
    with open(Path(__file__).parent / '../../resources/hero_attr_stats.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            heros.append(Hero(row))
    return heros