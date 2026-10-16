from lab2.materials import Wallpaper, Tile, Laminate
from lab2.calculator import MaterialCalculator
from lab2.reports import save_all

w = Wallpaper(1.06, 10, 1500)
t = Tile(30, 30, 120)
l = Laminate(2.13, 900)

summary = MaterialCalculator.calculate_many([w, t, l], area=20, reserve=0.1)

paths = save_all(summary, output_dir="reports", docx=True, xlsx=True)
for p in paths:
    print("Сохранено:", p)