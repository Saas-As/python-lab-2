"""
Модуль расчёта количества и стоимости отделочных материалов.

Работает с любыми объектами, реализующими контракт Material из materials.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

from .materials import Material


# =====================================================================
#                      РЕЗУЛЬТАТ РАСЧЁТА ПО ОДНОМУ МАТЕРИАЛУ
# =====================================================================

@dataclass
class CalculationResult:
    """
    Результат расчёта по одному материалу.
    """

    material: Material
    area: float
    reserve: float # запас
    quantity: int
    total_cost: float

    @property
    def total_area_needed(self) -> float:
        """Сколько м² материала реально закупается (с запасом)."""
        return self.quantity * self.material.unit_area

    def to_row(self) -> tuple:
        """
        Возвращает строку-кортеж для вставки в отчёт (docx/xlsx).
        """
        return (
            self.material.name,
            f"{self.material.unit_area:.3f}",
            self.material.unit_name,
            f"{self.area:.2f}",
            f"{self.reserve * 100:.1f}%",
            self.quantity,
            f"{self.material.price:.2f}",
            f"{self.total_cost:.2f}",
        )

    def __str__(self) -> str:
        return (f"{self.material.name}: {self.quantity} {self.material.unit_name}(ов) "
                f"на {self.total_area_needed:.2f} м², итого {self.total_cost:.2f} ₽")


# =====================================================================
#                       СВОДКА ПО НЕСКОЛЬКИМ МАТЕРИАЛАМ
# =====================================================================

@dataclass
class Summary:
    """
    Сводка по списку рассчитанных материалов.
    """

    results: list[CalculationResult] = field(default_factory=list)
    total: float = field(init=False, default=0.0)

    def __post_init__(self):
        self.total = sum(r.total_cost for r in self.results)

    def add(self, result: CalculationResult) -> None:
        """Добавить результат и пересчитать итог."""
        self.results.append(result)
        self.total = sum(r.total_cost for r in self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __str__(self) -> str:
        lines = [str(r) for r in self.results]
        lines.append(f"ИТОГО: {self.total:.2f} ₽")
        return "\n".join(lines)


# =====================================================================
#                          КАЛЬКУЛЯТОР
# =====================================================================

class MaterialCalculator:
    """
    Универсальный калькулятор отделочных материалов.
    """

    # Запас по умолчанию — 10%.
    DEFAULT_RESERVE = 0.10

    # Максимально допустимый запас — 100%
    MAX_RESERVE = 1.0

    @staticmethod
    def _validate_inputs(area: float, reserve: float) -> None:
        """
        Проверка входных параметров.
        """
        if isinstance(area, bool) or not isinstance(area, (int, float)):
            raise TypeError("Площадь должна быть числом")
        if area <= 0:
            raise ValueError("Площадь должна быть больше нуля")

        if isinstance(reserve, bool) or not isinstance(reserve, (int, float)):
            raise TypeError("Запас должен быть числом")
        if reserve < 0:
            raise ValueError("Запас не может быть отрицательным")
        if reserve > MaterialCalculator.MAX_RESERVE:
            raise ValueError(
                f"Запас не может превышать {MaterialCalculator.MAX_RESERVE * 100:.0f}%"
            )

    @classmethod
    def calculate(
        cls,
        material: Material,
        area: float,
        reserve: float | None = None,
    ) -> CalculationResult:
        """
        Рассчитать количество и стоимость для одного материала.
        """
        if not isinstance(material, Material):
            raise TypeError(
                f"Ожидался Material, получено {type(material).__name__}"
            )

        if reserve is None:
            reserve = cls.DEFAULT_RESERVE

        cls._validate_inputs(area, reserve)

        # math.ceil — округление вверх: нельзя купить 2.3 рулона, берём 3.
        # Небольшая поправка 1e-9 нужна из-за ошибок округления float:
        # например, 0.1 + 0.2 != 0.3, и ceil(3.0000000000000004) даст 4.
        quantity = math.ceil(area * (1 + reserve) / material.unit_area - 1e-9)

        total_cost = quantity * material.price

        return CalculationResult(
            material=material,
            area=float(area),
            reserve=float(reserve),
            quantity=quantity,
            total_cost=round(total_cost, 2),
        )

    @classmethod
    def calculate_many(
        cls,
        materials: Iterable[Material],
        area: float,
        reserve: float | None = None,
    ) -> Summary:
        """
        Рассчитать сразу несколько материалов на одну и ту же площадь.
        """
        summary = Summary()
        for material in materials:
            summary.add(cls.calculate(material, area, reserve))
        return summary