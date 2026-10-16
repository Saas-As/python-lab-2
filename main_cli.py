"""
Консольная версия приложения для запуска в Docker.

Не зависит от PySide6 — использует только lab2.materials, lab2.calculator
и lab2.report. Запускается командой: python main_cli.py
"""

from __future__ import annotations

from lab2.materials import Laminate, Tile, Wallpaper
from lab2.calculator import MaterialCalculator
from lab2.reports import save_all


# Меню: ключ → (название, функция-фабрика материала)
MENU = {
    "1": ("Обои", lambda: Wallpaper(1.06, 10, 1500)),
    "2": ("Плитка", lambda: Tile(30, 30, 120)),
    "3": ("Ламинат", lambda: Laminate(2.13, 900)),
}


def read_float(prompt: str, default: float) -> float:
    """Читает число с клавиатуры, при пустом вводе берёт default."""
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        print(f"  ⚠ Не число, беру значение по умолчанию: {default}")
        return default


def main() -> None:
    print("=" * 55)
    print("  Расчёт отделочных материалов (консольная версия)")
    print("=" * 55)

    area = read_float("Площадь, м²", 20.0)
    reserve_percent = read_float("Запас на подрезку, %", 10.0)
    reserve = reserve_percent / 100.0

    # Считаем сразу все три материала — этого достаточно для демонстрации
    materials = [factory() for _, factory in MENU.values()]
    summary = MaterialCalculator.calculate_many(materials, area=area, reserve=reserve)

    print()
    print(summary)
    print()

    # Сохраняем отчёты в /app/reports (этот путь смонтируем с хостом)
    paths = save_all(summary, output_dir="reports")
    for p in paths:
        print(f"  ✓ Сохранено: {p}")


if __name__ == "__main__":
    main()