"""
Модуль материалов для расчёта закупки отделочных материалов.

Содержит абстрактный базовый класс Material и три конкретных наследника:
Wallpaper (обои), Tile (плитка), Laminate (ламинат).

Классы описывают данные материала и его геомеорию (площадь одной единицы).
"""

from abc import ABC, abstractmethod


class Material(ABC):
    """
    Абстрактный базовый класс отделочного материала.

    Определяет общий контракт для всех материалов:
      * managed-атрибуты name и price (с валидацией);
      * абстрактные свойства unit_area и unit_name — каждая конкретная
        реализация сама решает, что считать "одной единицей";
      * dunder-методы для печати, сравнения и сортировки.
    """

    def __init__(self, name: str, price: float):
        self._name = None
        self._price = None
        self.name = name
        self.price = price

    # ------------------------- managed-атрибуты -------------------------

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Название материала должно быть непустой строкой")
        self._name = value.strip()

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float):
        # bool — подкласс int, но цену True/False принимать не хотим
        # ????
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Цена должна быть числом")
        if value <= 0:
            raise ValueError("Цена должна быть больше нуля")
        self._price = float(value)

    # ------------------------- абстрактный контракт -------------------------

    @property
    @abstractmethod
    def unit_area(self) -> float:
        """
        Площадь одной единицы материала в м².

        Для обоев — площадь рулона, для плитки — площадь одной плитки,
        для ламината — площадь упаковки.
        """
        ...

    @property
    @abstractmethod
    def unit_name(self) -> str:
        """Название единицы измерения: 'рулон', 'плитка', 'упаковка'."""
        ...

    # ------------------------- dunder-методы -------------------------

    def __str__(self) -> str:
        """читаемое представление для print()."""
        return (f"{self.name}: {self.unit_area:.2f} м² за {self.unit_name}, "
                f"цена {self.price:.2f} ₽")

    def __repr__(self) -> str:
        """Техническое представление для отладки."""
        return (f"{type(self).__name__}(name={self.name!r}, "
                f"price={self.price!r}, unit_area={self.unit_area!r})")

    def __lt__(self, other):
        """Сравнение через < — нужно для sorted() по цене."""
        if not isinstance(other, Material):
            return NotImplemented
        return self.price < other.price

    # Объект изменяемый (есть сеттеры) — класть его в set/dict-ключ нельзя.
    __hash__ = None


# =====================================================================
#                              ОБОИ
# =====================================================================

class Wallpaper(Material):
    """Обои. Единица закупки — рулон."""

    def __init__(self, width: float, length: float, price: float):
        # выставит name и price через property-сеттеры
        super().__init__("Обои", price)

        self._width = None
        self._length = None
        self.width = width
        self.length = length

    # ---------- managed-атрибуты ----------

    @property
    def width(self) -> float:
        """Ширина рулона, м."""
        return self._width

    @width.setter
    def width(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Ширина должна быть числом")
        if value <= 0:
            raise ValueError("Ширина рулона должна быть больше нуля")
        self._width = float(value)

    @property
    def length(self) -> float:
        """Длина рулона, м."""
        return self._length

    @length.setter
    def length(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Длина должна быть числом")
        if value <= 0:
            raise ValueError("Длина рулона должна быть больше нуля")
        self._length = float(value)

    # ---------- реализация абстрактного контракта ----------

    @property
    def unit_area(self) -> float:
        """Площадь одного рулона, м²."""
        return self.width * self.length

    @property
    def unit_name(self) -> str:
        return "рулон"

    # ---------- dunder-методы ----------

    def __str__(self) -> str:
        return (f"Обои {self.width}×{self.length} м "
                f"(рулон {self.unit_area:.2f} м²) — {self.price:.2f} ₽/рулон")

    def __repr__(self) -> str:
        return (f"Wallpaper(width={self.width!r}, "
                f"length={self.length!r}, price={self.price!r})")


# =====================================================================
#                              ПЛИТКА
# =====================================================================

class Tile(Material):
    """
    Плитка. Единица закупки — одна плитка.

    Размеры задаются в см,
    а внутри переводятся в метры для единообразия расчётов.
    """

    def __init__(self, width_cm: float, height_cm: float, price: float):
        super().__init__("Плитка", price)

        self._width_cm = None
        self._height_cm = None
        self.width_cm = width_cm
        self.height_cm = height_cm

    # ---------- managed-атрибуты ----------

    @property
    def width_cm(self) -> float:
        """Ширина плитки, см."""
        return self._width_cm

    @width_cm.setter
    def width_cm(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Ширина плитки должна быть числом")
        if value <= 0:
            raise ValueError("Ширина плитки должна быть больше нуля")
        self._width_cm = float(value)

    @property
    def height_cm(self) -> float:
        """Высота плитки, см."""
        return self._height_cm

    @height_cm.setter
    def height_cm(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Высота плитки должна быть числом")
        if value <= 0:
            raise ValueError("Высота плитки должна быть больше нуля")
        self._height_cm = float(value)

    # ---------- реализация абстрактного контракта ----------

    @property
    def unit_area(self) -> float:
        """Площадь одной плитки в м²"""
        return (self.width_cm / 100) * (self.height_cm / 100)

    @property
    def unit_name(self) -> str:
        return "плитка"

    # ---------- dunder-методы ----------

    def __str__(self) -> str:
        return (f"Плитка {self.width_cm}×{self.height_cm} см "
                f"({self.unit_area:.4f} м²) — {self.price:.2f} ₽/шт")

    def __repr__(self) -> str:
        return (f"Tile(width_cm={self.width_cm!r}, "
                f"height_cm={self.height_cm!r}, price={self.price!r})")


# =====================================================================
#                             ЛАМИНАТ
# =====================================================================

class Laminate(Material):
    """
    Ламинат. Единица закупки — упаковка.

    Пользователь указывает площадь упаковки в м² и цену за упаковку.
    """

    def __init__(self, pack_area: float, price: float):
        super().__init__("Ламинат", price)

        self._pack_area = None
        self.pack_area = pack_area

    # ---------- managed-атрибуты ----------

    @property
    def pack_area(self) -> float:
        """Площадь одной упаковки, м²."""
        return self._pack_area

    @pack_area.setter
    def pack_area(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Площадь упаковки должна быть числом")
        if value <= 0:
            raise ValueError("Площадь упаковки должна быть больше нуля")
        self._pack_area = float(value)

    # ---------- реализация абстрактного контракта ----------

    @property
    def unit_area(self) -> float:
        """Площадь одной упаковки, м²."""
        return self.pack_area

    @property
    def unit_name(self) -> str:
        return "упаковка"

    # ---------- dunder-методы ----------

    def __str__(self) -> str:
        return (f"Ламинат, упаковка {self.pack_area:.3f} м² — "
                f"{self.price:.2f} ₽/упаковка")

    def __repr__(self) -> str:
        return f"Laminate(pack_area={self.pack_area!r}, price={self.price!r})"