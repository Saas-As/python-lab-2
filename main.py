from lab2.materials import Wallpaper, Tile, Laminate
from lab2.calculator import MaterialCalculator

w = Wallpaper(1.06, 10, 1500)
t = Tile(30, 30, 120)
l = Laminate(2.13, 900)

# один материал
res = MaterialCalculator.calculate(w, area=20, reserve=0.1)
print(res)                              # Обои: 3 рулон(ов) на 31.80 м², итого 4500.00 ₽
print(res.to_row())                     # кортеж для отчёта

# сразу несколько
summary = MaterialCalculator.calculate_many([w, t, l], area=20)
print(summary)                          # строки + ИТОГО
print(f"Всего позиций: {len(summary)}")