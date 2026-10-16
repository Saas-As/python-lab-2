"""
Тесты для пакета lab2: materials, calculator, report.

Запуск:
    pytest -v
или только этот файл:
    pytest tests/test_materials.py -v
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from lab2.materials import Laminate, Material, Tile, Wallpaper
from lab2.calculator import (
    CalculationResult,
    MaterialCalculator,
    Summary,
)
from lab2.reports import DocxReportWriter, XlsxReportWriter, save_all


# =====================================================================
#                          ФИКСТУРЫ
# =====================================================================

@pytest.fixture
def wallpaper() -> Wallpaper:
    """Обои 1.06 × 10 м по 1500 ₽ — площадь рулона 10.6 м²."""
    return Wallpaper(width=1.06, length=10, price=1500)


@pytest.fixture
def tile() -> Tile:
    """Плитка 30 × 30 см по 120 ₽ — площадь 0.09 м²."""
    return Tile(width_cm=30, height_cm=30, price=120)


@pytest.fixture
def laminate() -> Laminate:
    """Ламинат, упаковка 2.13 м² по 900 ₽."""
    return Laminate(pack_area=2.13, price=900)


# =====================================================================
#                        ТЕСТЫ: MATERIALS
# =====================================================================

class TestWallpaper:
    """Валидация, свойства и dunder-методы обоев."""

    def test_creation(self, wallpaper: Wallpaper):
        assert wallpaper.width == 1.06
        assert wallpaper.length == 10
        assert wallpaper.price == 1500
        assert wallpaper.name == "Обои"

    def test_unit_area(self, wallpaper: Wallpaper):
        assert wallpaper.unit_area == pytest.approx(10.6)

    def test_unit_name(self, wallpaper: Wallpaper):
        assert wallpaper.unit_name == "рулон"

    @pytest.mark.parametrize("bad_width", [0, -1, -0.5])
    def test_negative_width_raises(self, bad_width: float):
        with pytest.raises(ValueError):
            Wallpaper(width=bad_width, length=10, price=1500)

    def test_zero_price_raises(self):
        with pytest.raises(ValueError):
            Wallpaper(width=1.06, length=10, price=0)

    def test_bool_price_raises(self):
        # True — подкласс int, но ценой быть не должен
        with pytest.raises(TypeError):
            Wallpaper(width=1.06, length=10, price=True)

    def test_str_contains_key_info(self, wallpaper: Wallpaper):
        s = str(wallpaper)
        assert "Обои" in s
        assert "1.06" in s
        assert "10" in s
        assert "1500" in s

    def test_repr_is_eval_friendly(self, wallpaper: Wallpaper):
        r = repr(wallpaper)
        assert r.startswith("Wallpaper(")
        assert "width=1.06" in r
        assert "price=1500" in r

    def test_different_types_not_equal(self):
        w = Wallpaper(1.06, 10, 1500)
        t = Tile(30, 30, 1500)   # та же цена, но другой тип
        assert w != t

    def test_lt_by_price(self):
        cheap = Wallpaper(1.06, 10, 1000)
        expensive = Wallpaper(1.06, 10, 2000)
        assert cheap < expensive
        assert not expensive < cheap

    def test_immutable_hash(self, wallpaper: Wallpaper):
        # __hash__ = None — объект нельзя положить в set
        with pytest.raises(TypeError):
            {wallpaper}


class TestTile:
    """Плитка: перевод см → м."""

    def test_unit_area_in_square_meters(self, tile: Tile):
        # 30 см × 30 см = 0.09 м²
        assert tile.unit_area == pytest.approx(0.09)

    def test_unit_name(self, tile: Tile):
        assert tile.unit_name == "плитка"

    def test_negative_dimension_raises(self):
        with pytest.raises(ValueError):
            Tile(width_cm=-30, height_cm=30, price=120)

class TestLaminate:
    """Ламинат: простая обёртка над pack_area."""

    def test_unit_area(self, laminate: Laminate):
        assert laminate.unit_area == pytest.approx(2.13)

    def test_unit_name(self, laminate: Laminate):
        assert laminate.unit_name == "упаковка"

    def test_zero_pack_area_raises(self):
        with pytest.raises(ValueError):
            Laminate(pack_area=0, price=900)


class TestMaterialABC:
    """Абстрактный базовый класс нельзя инстанцировать напрямую."""

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            Material(name="X", price=100)  # type: ignore[abstract]


# =====================================================================
#                       ТЕСТЫ: CALCULATOR
# =====================================================================

class TestCalculate:
    """Расчёт количества и стоимости для одного материала."""

    def test_wallpaper_calculation(self, wallpaper: Wallpaper):
        # 20 м² + 10% = 22 м²; 22 / 10.6 = 2.075 → ceil = 3 рулона
        result = MaterialCalculator.calculate(wallpaper, area=20, reserve=0.1)
        assert isinstance(result, CalculationResult)
        assert result.quantity == 3
        assert result.total_cost == pytest.approx(4500.0)
        assert result.area == 20
        assert result.reserve == 0.1

    def test_tile_calculation(self, tile: Tile):
        # 22 м² / 0.09 = 244.44 → 245 плиток
        result = MaterialCalculator.calculate(tile, area=20, reserve=0.1)
        assert result.quantity == 245
        assert result.total_cost == pytest.approx(29400.0)

    def test_laminate_calculation(self, laminate: Laminate):
        # 22 / 2.13 = 10.33 → 11 упаковок
        result = MaterialCalculator.calculate(laminate, area=20, reserve=0.1)
        assert result.quantity == 11
        assert result.total_cost == pytest.approx(9900.0)

    def test_default_reserve(self, wallpaper: Wallpaper):
        # reserve=None → берётся DEFAULT_RESERVE (0.1)
        r_default = MaterialCalculator.calculate(wallpaper, area=20)
        r_explicit = MaterialCalculator.calculate(wallpaper, area=20, reserve=0.1)
        assert r_default.quantity == r_explicit.quantity

    def test_zero_reserve(self, wallpaper: Wallpaper):
        # 20 / 10.6 = 1.887 → 2 рулона
        result = MaterialCalculator.calculate(wallpaper, area=20, reserve=0)
        assert result.quantity == 2

    def test_float_precision_at_integer_boundary(self):
        # Ровно 3 рулона * 10.6 = 31.8 м²; с запасом 0 должно быть 3, а не 4
        w = Wallpaper(1.0, 10.0, 100)
        result = MaterialCalculator.calculate(w, area=30.0, reserve=0)
        # 30 / 10 = 3.0, и мы ожидаем именно 3, а не 4 из-за float-погрешности
        assert result.quantity == 3

    @pytest.mark.parametrize("bad_area", [0, -5, -0.1])
    def test_bad_area_raises(self, wallpaper: Wallpaper, bad_area: float):
        with pytest.raises(ValueError):
            MaterialCalculator.calculate(wallpaper, area=bad_area)

    def test_area_wrong_type_raises(self, wallpaper: Wallpaper):
        with pytest.raises(TypeError):
            MaterialCalculator.calculate(wallpaper, area="20")  # type: ignore[arg-type]

    def test_reserve_over_100_percent_raises(self, wallpaper: Wallpaper):
        with pytest.raises(ValueError):
            MaterialCalculator.calculate(wallpaper, area=20, reserve=2.0)

    def test_negative_reserve_raises(self, wallpaper: Wallpaper):
        with pytest.raises(ValueError):
            MaterialCalculator.calculate(wallpaper, area=20, reserve=-0.1)

    def test_wrong_material_type_raises(self):
        with pytest.raises(TypeError):
            MaterialCalculator.calculate("not a material", area=20)  # type: ignore[arg-type]


class TestCalculateMany:
    """Агрегация нескольких материалов в одну сводку."""

    def test_summary_total(self, wallpaper: Wallpaper, tile: Tile, laminate: Laminate):
        summary = MaterialCalculator.calculate_many(
            [wallpaper, tile, laminate], area=20, reserve=0.1
        )
        assert len(summary) == 3
        # 4500 + 29400 + 9900 = 43800
        assert summary.total == pytest.approx(43800.0)

    def test_empty_list(self):
        summary = MaterialCalculator.calculate_many([], area=20)
        assert len(summary) == 0
        assert summary.total == 0.0

    def test_iteration(self, wallpaper: Wallpaper, tile: Tile):
        summary = MaterialCalculator.calculate_many([wallpaper, tile], area=20)
        names = [r.material.name for r in summary]
        assert names == ["Обои", "Плитка"]


class TestCalculationResult:
    """Дополнительные свойства объекта результата."""

    def test_total_area_needed(self, wallpaper: Wallpaper):
        result = MaterialCalculator.calculate(wallpaper, area=20, reserve=0.1)
        # 3 рулона × 10.6 м² = 31.8 м²
        assert result.total_area_needed == pytest.approx(31.8)

    def test_to_row_has_eight_fields(self, wallpaper: Wallpaper):
        result = MaterialCalculator.calculate(wallpaper, area=20)
        row = result.to_row()
        assert len(row) == 8
        assert row[0] == "Обои"
        assert row[5] == result.quantity


# =====================================================================
#                       ТЕСТЫ: REPORT
# =====================================================================

class TestReportWriters:
    """Проверяем, что файлы создаются и имеют ненулевой размер."""

    @pytest.fixture
    def summary(self, wallpaper: Wallpaper, tile: Tile) -> Summary:
        return MaterialCalculator.calculate_many([wallpaper, tile], area=20)

    def test_docx_writer_creates_file(self, summary: Summary, tmp_path: Path):
        # tmp_path — встроенная фикстура pytest: временная папка, чистится автоматически
        path = DocxReportWriter(tmp_path).save(summary, filename="test.docx")
        assert path.exists()
        assert path.stat().st_size > 0
        assert path.suffix == ".docx"

    def test_xlsx_writer_creates_file(self, summary: Summary, tmp_path: Path):
        path = XlsxReportWriter(tmp_path).save(summary, filename="test.xlsx")
        assert path.exists()
        assert path.stat().st_size > 0
        assert path.suffix == ".xlsx"

    def test_auto_filename(self, summary: Summary, tmp_path: Path):
        # Без filename — имя генерируется с timestamp
        path = DocxReportWriter(tmp_path).save(summary)
        assert path.exists()
        assert path.name.startswith("report_")
        assert path.name.endswith(".docx")

    def test_save_all_both(self, summary: Summary, tmp_path: Path):
        paths = save_all(summary, output_dir=tmp_path, docx=True, xlsx=True)
        assert len(paths) == 2
        assert all(p.exists() for p in paths)

    def test_save_all_only_xlsx(self, summary: Summary, tmp_path: Path):
        paths = save_all(summary, output_dir=tmp_path, docx=False, xlsx=True)
        assert len(paths) == 1
        assert paths[0].suffix == ".xlsx"

    def test_writer_rejects_non_summary(self, tmp_path: Path):
        with pytest.raises(TypeError):
            DocxReportWriter(tmp_path).save("not a summary")  # type: ignore[arg-type]

    def test_output_dir_creates_automatically(self, summary: Summary, tmp_path: Path):
        # Папка, которой ещё нет
        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()
        DocxReportWriter(nested).save(summary, filename="test.docx")
        assert nested.exists()