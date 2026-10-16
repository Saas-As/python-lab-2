"""
Основная программа: расчёт отделочных материалов (Qt-интерфейс).

Использует PySide6 для графического интерфейса.
Бизнес-логика — в пакете lab2 (materials, calculator, report).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lab2.materials import Laminate, Material, Tile, Wallpaper
from lab2.calculator import CalculationResult, MaterialCalculator, Summary
from lab2.reports import DocxReportWriter, XlsxReportWriter


# Описание материалов: какой набор полей показывать при выборе.
# Каждое поле — (ключ, подпись, минимум, максимум, значение_по_умолчанию, шаг)
MATERIAL_FIELDS = {
    "Обои": [
        ("width", "Ширина рулона, м", 0.01, 100.0, 1.06, 0.01),
        ("length", "Длина рулона, м", 0.01, 1000.0, 10.0, 0.1),
        ("price", "Цена за рулон, ₽", 0.01, 1_000_000.0, 1500.0, 10.0),
    ],
    "Плитка": [
        ("width_cm", "Ширина плитки, см", 0.1, 1000.0, 30.0, 0.5),
        ("height_cm", "Высота плитки, см", 0.1, 1000.0, 30.0, 0.5),
        ("price", "Цена за плитку, ₽", 0.01, 1_000_000.0, 120.0, 1.0),
    ],
    "Ламинат": [
        ("pack_area", "Площадь упаковки, м²", 0.01, 1000.0, 2.13, 0.01),
        ("price", "Цена за упаковку, ₽", 0.01, 1_000_000.0, 900.0, 10.0),
    ],
}


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Расчёт отделочных материалов")
        self.resize(780, 720)

        # Сводка по всем добавленным материалам.
        self._summary = Summary()

        # Текущий материал (пересоздаётся при нажатии «Рассчитать»).
        self._last_result: CalculationResult | None = None

        # Спинбоксы параметров материала — заполняются динамически.
        self._param_widgets: dict[str, QDoubleSpinBox] = {}

        self._build_ui()
        self._on_material_changed()  # показать поля для первого материала

    # ================================================================
    #                      ПОСТРОЕНИЕ ИНТЕРФЕЙСА
    # ================================================================

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- Выбор материала ---
        material_box = QGroupBox("Материал")
        material_layout = QVBoxLayout(material_box)
        self.material_combo = QComboBox()
        self.material_combo.addItems(list(MATERIAL_FIELDS.keys()))
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        material_layout.addWidget(self.material_combo)
        root.addWidget(material_box)

        # --- Параметры материала (динамические) ---
        self.params_box = QGroupBox("Параметры материала")
        self.params_form = QFormLayout(self.params_box)
        root.addWidget(self.params_box)

        # --- Площадь и запас ---
        common_box = QGroupBox("Общие параметры")
        common_form = QFormLayout(common_box)

        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0.01, 1_000_000.0)
        self.area_spin.setValue(20.0)
        self.area_spin.setSuffix(" м²")
        self.area_spin.setDecimals(2)
        common_form.addRow("Площадь:", self.area_spin)

        self.reserve_spin = QDoubleSpinBox()
        self.reserve_spin.setRange(0.0, 100.0)
        self.reserve_spin.setValue(10.0)
        self.reserve_spin.setSuffix(" %")
        self.reserve_spin.setDecimals(1)
        common_form.addRow("Запас на подрезку:", self.reserve_spin)

        root.addWidget(common_box)

        # --- Кнопки расчёта ---
        buttons_layout = QHBoxLayout()
        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.clicked.connect(self._on_calculate)
        self.add_btn = QPushButton("Добавить в отчёт")
        self.add_btn.clicked.connect(self._on_add_to_report)
        self.add_btn.setEnabled(False)  # пока нет расчёта — нельзя добавить
        buttons_layout.addWidget(self.calc_btn)
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addStretch()
        root.addLayout(buttons_layout)

        # --- Таблица результатов ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Материал", "Кол-во", "Единица", "Стоимость, ₽", ""]
        )
        # Растягиваем колонки по ширине окна
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table)

        # --- Итог ---
        self.total_label = QLabel("ИТОГО: 0.00 ₽")
        self.total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.total_label)

        # --- Кнопки сохранения ---
        save_layout = QHBoxLayout()
        self.save_docx_btn = QPushButton("Сохранить .docx")
        self.save_docx_btn.clicked.connect(lambda: self._on_save("docx"))
        self.save_xlsx_btn = QPushButton("Сохранить .xlsx")
        self.save_xlsx_btn.clicked.connect(lambda: self._on_save("xlsx"))
        save_layout.addWidget(self.save_docx_btn)
        save_layout.addWidget(self.save_xlsx_btn)
        save_layout.addStretch()
        root.addLayout(save_layout)

        self.status_label = QLabel("Готово")
        root.addWidget(self.status_label)

    # ================================================================
    #                    ДИНАМИЧЕСКИЕ ПОЛЯ МАТЕРИАЛА
    # ================================================================

    def _on_material_changed(self) -> None:
        """Пересобирает поля формы под выбранный материал."""
        # Удаляем все прежние строки формы
        while self.params_form.rowCount() > 0:
            self.params_form.removeRow(0)
        self._param_widgets.clear()

        material_name = self.material_combo.currentText()
        for key, label, min_v, max_v, default, step in MATERIAL_FIELDS[material_name]:
            spin = QDoubleSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(default)
            spin.setSingleStep(step)
            spin.setDecimals(2 if step < 1 else 1)
            self.params_form.addRow(label + ":", spin)
            self._param_widgets[key] = spin

        # Сбросить «рассчитано, но не добавлено», если пользователь меняет материал
        self._last_result = None
        self.add_btn.setEnabled(False)

    def _build_material(self) -> Material:
        """Собирает объект Material из текущих значений формы."""
        name = self.material_combo.currentText()
        values = {key: w.value() for key, w in self._param_widgets.items()}

        if name == "Обои":
            return Wallpaper(width=values["width"], length=values["length"], price=values["price"])
        if name == "Плитка":
            return Tile(width_cm=values["width_cm"], height_cm=values["height_cm"], price=values["price"])
        if name == "Ламинат":
            return Laminate(pack_area=values["pack_area"], price=values["price"])
        raise ValueError(f"Неизвестный материал: {name}")

    # ================================================================
    #                          ДЕЙСТВИЯ
    # ================================================================

    def _on_calculate(self) -> None:
        try:
            material = self._build_material()
            area = self.area_spin.value()
            reserve = self.reserve_spin.value() / 100.0

            result = MaterialCalculator.calculate(material, area, reserve)
        except (TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка ввода", str(exc))
            return

        self._last_result = result
        self.add_btn.setEnabled(True)

        QMessageBox.information(
            self,
            "Результат",
            f"{material.name}\n"
            f"Количество: {result.quantity} {material.unit_name}(ов)\n"
            f"Стоимость: {result.total_cost:.2f} ₽",
        )
        self.status_label.setText(f"Рассчитано: {material.name} — {result.total_cost:.2f} ₽")

    def _on_add_to_report(self) -> None:
        if self._last_result is None:
            return

        self._summary.add(self._last_result)
        self._refresh_table()

        self._last_result = None
        self.add_btn.setEnabled(False)
        self.status_label.setText(f"Добавлено в отчёт. Позиций: {len(self._summary)}")

    def _refresh_table(self) -> None:
        """Перерисовывает таблицу и итог по актуальному Summary."""
        self.table.setRowCount(0)

        for result in self._summary.results:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(result.material.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(result.quantity)))
            self.table.setItem(row, 2, QTableWidgetItem(result.material.unit_name))
            self.table.setItem(row, 3, QTableWidgetItem(f"{result.total_cost:.2f}"))

            # Кнопка «Удалить» в последней колонке
            delete_btn = QPushButton("✕")
            delete_btn.setFixedWidth(32)
            delete_btn.clicked.connect(lambda _, r=result: self._remove_result(r))
            self.table.setCellWidget(row, 4, delete_btn)

        self.total_label.setText(f"ИТОГО: {self._summary.total:.2f} ₽")

    def _remove_result(self, result: CalculationResult) -> None:
        self._summary.results.remove(result)
        # Пересчитать total: Summary.add сам пересчитывает, но при удалении — вручную
        self._summary.total = sum(r.total_cost for r in self._summary.results)
        self._refresh_table()

    # ================================================================
    #                          СОХРАНЕНИЕ
    # ================================================================

    def _on_save(self, fmt: str) -> None:
        if len(self._summary) == 0:
            QMessageBox.warning(self, "Нечего сохранять", "Сначала добавьте хотя бы один материал.")
            return

        # Диалог сохранения файла (нативный или Qt — неважно)
        default_name = f"report.{fmt}"
        if fmt == "docx":
            filter_str = "Документ Word (*.docx)"
        else:
            filter_str = "Таблица Excel (*.xlsx)"

        filepath_str, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", default_name, filter_str
        )
        if not filepath_str:
            return  # пользователь отменил

        filepath = Path(filepath_str)
        output_dir = filepath.parent
        filename = filepath.name

        try:
            if fmt == "docx":
                DocxReportWriter(output_dir).save(self._summary, filename=filename)
            else:
                XlsxReportWriter(output_dir).save(self._summary, filename=filename)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))
            return

        QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{filepath}")
        self.status_label.setText(f"Сохранено: {filepath}")


# ================================================================
#                            ЗАПУСК
# ================================================================

def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())