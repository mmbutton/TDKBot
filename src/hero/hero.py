def csv_int(str):
    str = str.strip()
    return int(str) if str else 0

def csv_float(str):
    str = str.strip()
    return float(str) if str else 0

# King Throne Quality efficiency formula which is Military Paragon % + Maiden Bond % + Military Paragon % * Maiden Bond % + 15% Bronze
def _calculate_growth(n, m):
    return int((n + m + n * m + 1.15) * 100)

class Hero(object):
    def __init__(self, row):
        self.hero_name = row['Hero Name']
        self.military_quality = csv_int(row['Military Quality'])
        self.fortune_quality = csv_int(row['Fortune Quality'])
        self.provisions_quality = csv_int(row['Provisions Quality'])
        self.inspiration_quality = csv_int(row['Inspiration Quality'])
        self.max_power = csv_int(row['Max Power'])
        self.max_kp = csv_int(row['Max KP'])
        self.max_military = csv_int(row['Max Military'])
        self.max_fortune = csv_int(row['Max Fortune'])
        self.max_provisions = csv_int(row['Max Provisions'])
        self.max_inspiration = csv_int(row['Max Inspiration'])
        self.military_paragon = csv_float(row['Military Growth'])
        self.fortune_paragon = csv_float(row['Fortune Growth'])
        self.provisions_paragon = csv_float(row['Provisions Growth'])
        self.inspiration_paragon = csv_float(row['Inspiration Growth'])
        self.difficulty = csv_float(row['Difficulty'])
        self.maiden_bond_percent = csv_float(row['Maiden Bond %'])
        self.maiden_military_bond = csv_int(row['Military Flat Bond'])
        self.maiden_fortune_bond = csv_int(row['Fortune Flat Bond'])
        self.maiden_provisions_bond = csv_int(row['Provisions Flat Bond'])
        self.maiden_inspiration_bond = csv_int(row['Inspiration Flat Bond'])
        self.diamond_bonus = csv_int(row['Diamond Bonus'])

    @property
    def military_growth(self):
        return _calculate_growth(self.military_paragon, self.maiden_bond_percent)

    @property
    def fortune_growth(self):
        return _calculate_growth(self.fortune_paragon, self.maiden_bond_percent)

    @property
    def provisions_growth(self):
        return _calculate_growth(self.provisions_paragon, self.maiden_bond_percent)

    @property
    def inspiration_growth(self):
        return _calculate_growth(self.inspiration_paragon, self.maiden_bond_percent)
