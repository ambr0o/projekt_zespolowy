import calendar
from datetime import date, timedelta
from PySide6.QtCore import QDate, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database
from theme import apply_card_shadow, get_safe_icon, theme_manager

MONTHS_NOMINATIVE = [
    "",
    "Styczeń",
    "Luty",
    "Marzec",
    "Kwiecień",
    "Maj",
    "Czerwiec",
    "Lipiec",
    "Sierpień",
    "Wrzesień",
    "Październik",
    "Listopad",
    "Grudzień",
]

MONTHS_GENITIVE = [
    "",
    "stycznia",
    "lutego",
    "marca",
    "kwietnia",
    "maja",
    "czerwca",
    "lipca",
    "sierpnia",
    "września",
    "października",
    "listopada",
    "grudnia",
]

WEEKDAYS_PL = [
    "poniedziałek",
    "wtorek",
    "środa",
    "czwartek",
    "piątek",
    "sobota",
    "niedziela",
]

PRESET_CATEGORY_COLORS = [
    "#ef4444",  # Czerwony
    "#f97316",  # Pomarańczowy
    "#f59e0b",  # Bursztynowy
    "#eab308",  # Żółty
    "#84cc16",  # Limonkowy
    "#10b981",  # Szmaragdowy
    "#14b8a6",  # Morski
    "#06b6d4",  # Cyjan
    "#3b82f6",  # Niebieski
    "#6366f1",  # Indygo
    "#8b5cf6",  # Fioletowy
    "#ec4899",  # Różowy
]

PRESET_CATEGORY_ICONS = [
    "fa5s.utensils",
    "fa5s.coffee",
    "fa5s.shopping-bag",
    "fa5s.shopping-cart",
    "fa5s.home",
    "fa5s.bolt",
    "fa5s.car",
    "fa5s.bus",
    "fa5s.gas-pump",
    "fa5s.plane",
    "fa5s.film",
    "fa5s.gamepad",
    "fa5s.music",
    "fa5s.heartbeat",
    "fa5s.pills",
    "fa5s.dumbbell",
    "fa5s.paw",
    "fa5s.book",
    "fa5s.graduation-cap",
    "fa5s.laptop",
    "fa5s.gift",
    "fa5s.briefcase",
    "fa5s.piggy-bank",
    "fa5s.coins",
    "fa5s.wrench",
    "fa5s.tshirt",
    "fa5s.baby",
    "fa5s.tag",
]


def format_date_pl(iso_date_str: str) -> str:
    """Zamienia datę z bazy 'RRRR-MM-DD' na czytelny format 'DD-MM-RRRR'."""
    parts = iso_date_str.split("-")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return iso_date_str


def format_pln(amount_grosze: int, show_plus: bool = False) -> str:
    """Formatuje kwotę z groszy do postaci np. '1 250.00 zł' lub '+450.00 zł'."""
    sign = ""
    if amount_grosze < 0:
        sign = "-"
    elif show_plus and amount_grosze > 0:
        sign = "+"

    abs_pln = abs(amount_grosze) / 100
    formatted = f"{abs_pln:,.2f} zł".replace(",", " ")
    return f"{sign}{formatted}"


class BalanceSummaryBar(QWidget):
    """Pasek trzech kart bilansu dla wybranego okresu: Przychody, Wydatki i Saldo."""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.income_card, self.income_value_lbl, self.income_badge = self._build_card(
            title="Przychody w okresie",
            icon_name="fa5s.arrow-down",
            badge_bg="#10b98124",
            icon_color="#10b981",
            state="income",
        )

        self.expense_card, self.expense_value_lbl, self.expense_badge = self._build_card(
            title="Wydatki w okresie",
            icon_name="fa5s.arrow-up",
            badge_bg="#ef444424",
            icon_color="#ef4444",
            state="expense",
        )

        self.balance_card, self.balance_value_lbl, self.balance_badge = self._build_card(
            title="Saldo okresu (bilans)",
            icon_name="fa5s.wallet",
            badge_bg="#3b82f624",
            icon_color="#3b82f6",
            state="neutral",
        )

        layout.addWidget(self.income_card, stretch=1)
        layout.addWidget(self.expense_card, stretch=1)
        layout.addWidget(self.balance_card, stretch=1)

    def _build_card(
        self,
        title: str,
        icon_name: str,
        badge_bg: str,
        icon_color: str,
        state: str,
    ) -> tuple[QFrame, QLabel, QLabel]:
        card = QFrame()
        card.setObjectName("MetricCard")
        apply_card_shadow(card)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 11, 16, 11)
        card_layout.setSpacing(12)

        badge = QLabel()
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {badge_bg}; border-radius: 18px; border: none;"
        )
        badge.setPixmap(get_safe_icon(icon_name, icon_color).pixmap(16, 16))
        card_layout.addWidget(badge)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("MetricTitle")

        value_lbl = QLabel("0.00 zł")
        value_lbl.setObjectName("MetricValue")
        value_lbl.setProperty("state", state)

        text_col.addWidget(title_lbl)
        text_col.addWidget(value_lbl)
        card_layout.addLayout(text_col, stretch=1)

        return card, value_lbl, badge

    def update_totals(self, income_grosze: int, expense_grosze: int) -> None:
        balance_grosze = income_grosze - expense_grosze

        self.income_value_lbl.setText(format_pln(income_grosze))
        self.expense_value_lbl.setText(format_pln(expense_grosze))
        self.balance_value_lbl.setText(format_pln(balance_grosze, show_plus=True))

        if balance_grosze > 0:
            balance_state = "income"
            badge_bg = "#10b98124"
            icon_color = "#10b981"
        elif balance_grosze < 0:
            balance_state = "expense"
            badge_bg = "#ef444424"
            icon_color = "#ef4444"
        else:
            balance_state = "neutral"
            badge_bg = "#3b82f624"
            icon_color = "#3b82f6"

        self.balance_badge.setStyleSheet(
            f"background-color: {badge_bg}; border-radius: 18px; border: none;"
        )
        self.balance_badge.setPixmap(
            get_safe_icon("fa5s.wallet", icon_color).pixmap(16, 16)
        )

        self.balance_value_lbl.setProperty("state", balance_state)
        self.balance_value_lbl.style().unpolish(self.balance_value_lbl)
        self.balance_value_lbl.style().polish(self.balance_value_lbl)


class DonutChartWidget(QWidget):
    """Nowoczesny wykres pierścieniowy dopasowujący kolory napisów do aktualnego motywu."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(220)
        self.slices: list[tuple[str, int, str]] = []
        self.center_subtitle: str = "Suma wydatków"
        theme_manager.theme_changed.connect(lambda _mode: self.update())

    def set_data(self, slices: list[tuple[str, int, str]], subtitle: str) -> None:
        self.slices = slices
        self.center_subtitle = subtitle
        self.update()

    def paintEvent(self, event) -> None:
        colors = theme_manager.get_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        ring_thickness = 28
        diameter = min(width, height) - 30
        if diameter < 100:
            diameter = 100

        rect = QRectF(
            (width - diameter) / 2,
            (height - diameter) / 2,
            diameter,
            diameter,
        )

        total_grosze = sum(item[1] for item in self.slices)

        if total_grosze <= 0:
            pen = QPen(QColor(colors["DONUT_EMPTY"]), ring_thickness)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, 0, 360 * 16)
        else:
            start_angle = 90 * 16
            total_span_budget = 360 * 16

            for idx, (_name, amount_grosze, color_hex) in enumerate(self.slices):
                if idx == len(self.slices) - 1:
                    span_angle = total_span_budget
                else:
                    span_angle = int(round((amount_grosze / total_grosze) * 360 * 16))
                    total_span_budget -= span_angle

                pen = QPen(QColor(color_hex), ring_thickness)
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(pen)
                painter.drawArc(rect, start_angle, -span_angle)
                start_angle -= span_angle

        subtitle_font = QFont("Segoe UI", 10)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(colors["TEXT_MUTED"]))
        subtitle_rect = QRectF(rect.left(), rect.center().y() - 26, rect.width(), 20)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, self.center_subtitle)

        amount_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(amount_font)
        painter.setPen(QColor(colors["TEXT_PRIMARY"]))
        amount_rect = QRectF(rect.left(), rect.center().y() - 4, rect.width(), 30)
        painter.drawText(
            amount_rect, Qt.AlignmentFlag.AlignCenter, format_pln(total_grosze)
        )


class CategoryCardButton(QFrame):
    """Klikalna karta kategorii z czystym zapisem procentowym i kwotą."""

    clicked = Signal(int, str, str, str)

    def __init__(
        self,
        category_id: int,
        name: str,
        color_hex: str,
        icon_name: str,
        amount_grosze: int,
        entries_count: int,
        percentage: float,
    ):
        super().__init__()
        self.category_id = category_id
        self.category_name = name
        self.color_hex = color_hex
        self.icon_name = icon_name

        colors = theme_manager.get_colors()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("CategoryCard")
        apply_card_shadow(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        icon_badge = QLabel()
        icon_badge.setFixedSize(40, 40)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 20px; border: none;"
        )
        icon_badge.setPixmap(get_safe_icon(icon_name, "#ffffff").pixmap(18, 18))
        layout.addWidget(icon_badge)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setObjectName("CardTitle")
        count_lbl = QLabel(f"Liczba wpisów: {entries_count}")
        count_lbl.setObjectName("MutedText")
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(count_lbl)
        layout.addLayout(info_layout, stretch=1)

        pct_lbl = QLabel(f"{percentage:.0f}%")
        pct_lbl.setObjectName("CategoryPercent")
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct_lbl.setMinimumWidth(42)
        layout.addWidget(pct_lbl)

        amount_lbl = QLabel(format_pln(amount_grosze))
        amount_lbl.setObjectName("CardAmount")
        amount_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        amount_lbl.setMinimumWidth(95)
        layout.addWidget(amount_lbl)

        chevron_lbl = QLabel()
        chevron_lbl.setPixmap(
            get_safe_icon("fa5s.chevron-right", colors["TEXT_MUTED"]).pixmap(13, 13)
        )
        layout.addWidget(chevron_lbl)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self.category_id, self.category_name, self.color_hex, self.icon_name
            )
        super().mousePressEvent(event)


class CategoryManagerDialog(QDialog):
    """Okno tworzenia własnych kategorii (z wyborem koloru i ikony) oraz przeglądania listy."""

    def __init__(self, initial_type: str = "expense", parent=None):
        super().__init__(parent)
        self.current_type = initial_type
        self.selected_color = PRESET_CATEGORY_COLORS[0]
        self.selected_icon = PRESET_CATEGORY_ICONS[0]
        self.last_created_category_id: int | None = None

        self.setWindowTitle("Zarządzanie kategoriami")
        self.setMinimumSize(780, 540)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 20, 22, 20)
        root_layout.setSpacing(14)

        top_row = QHBoxLayout()
        title_lbl = QLabel("Kategorie wydatków i przychodów")
        title_lbl.setObjectName("PageTitle")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        switcher_frame = QFrame()
        switcher_frame.setObjectName("SegmentedContainer")
        switcher_layout = QHBoxLayout(switcher_frame)
        switcher_layout.setContentsMargins(4, 4, 4, 4)
        switcher_layout.setSpacing(4)

        self.expense_btn = QPushButton("Wydatki")
        self.income_btn = QPushButton("Przychody")
        self.expense_btn.setObjectName("SegmentBtn")
        self.income_btn.setObjectName("SegmentBtn")
        self.expense_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.income_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.expense_btn.clicked.connect(lambda: self.switch_type("expense"))
        self.income_btn.clicked.connect(lambda: self.switch_type("income"))

        switcher_layout.addWidget(self.expense_btn)
        switcher_layout.addWidget(self.income_btn)
        top_row.addWidget(switcher_frame)

        root_layout.addLayout(top_row)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        list_card = QFrame()
        list_card.setObjectName("Card")
        apply_card_shadow(list_card)
        list_card_layout = QVBoxLayout(list_card)
        list_card_layout.setContentsMargins(16, 16, 16, 16)
        list_card_layout.setSpacing(10)

        list_header = QLabel("Istniejące kategorie")
        list_header.setObjectName("SectionTitle")
        list_card_layout.addWidget(list_header)

        self.cats_scroll = QScrollArea()
        self.cats_scroll.setWidgetResizable(True)
        self.cats_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cats_scroll.setStyleSheet("background: transparent;")

        self.cats_list_container = QWidget()
        self.cats_list_container.setStyleSheet("background: transparent;")
        self.cats_list_layout = QVBoxLayout(self.cats_list_container)
        self.cats_list_layout.setContentsMargins(0, 0, 4, 0)
        self.cats_list_layout.setSpacing(8)
        self.cats_list_layout.addStretch()

        self.cats_scroll.setWidget(self.cats_list_container)
        list_card_layout.addWidget(self.cats_scroll, stretch=1)

        columns.addWidget(list_card, stretch=1)

        creator_card = QFrame()
        creator_card.setObjectName("Card")
        apply_card_shadow(creator_card)
        creator_layout = QVBoxLayout(creator_card)
        creator_layout.setContentsMargins(18, 16, 18, 16)
        creator_layout.setSpacing(12)

        creator_title = QLabel("Utwórz nową kategorię")
        creator_title.setObjectName("SectionTitle")
        creator_layout.addWidget(creator_title)

        preview_box = QFrame()
        preview_box.setObjectName("PreviewBox")
        preview_layout = QHBoxLayout(preview_box)
        preview_layout.setContentsMargins(14, 10, 14, 10)
        preview_layout.setSpacing(12)

        self.preview_badge = QLabel()
        self.preview_badge.setFixedSize(42, 42)
        self.preview_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        preview_text_col = QVBoxLayout()
        preview_text_col.setSpacing(1)
        preview_hint = QLabel("Podgląd nowej kategorii")
        preview_hint.setObjectName("MutedText")
        self.preview_name_lbl = QLabel("Nowa kategoria")
        self.preview_name_lbl.setObjectName("CardTitle")
        preview_text_col.addWidget(preview_hint)
        preview_text_col.addWidget(self.preview_name_lbl)

        preview_layout.addWidget(self.preview_badge)
        preview_layout.addLayout(preview_text_col, stretch=1)
        creator_layout.addWidget(preview_box)

        creator_layout.addWidget(QLabel("Nazwa kategorii:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("np. Zwierzęta, Paliwo, Kawa, Subskrypcje...")
        self.name_input.textChanged.connect(self.update_preview)
        creator_layout.addWidget(self.name_input)

        color_header_row = QHBoxLayout()
        color_header_row.addWidget(QLabel("Kolor:"))
        color_header_row.addStretch()
        self.custom_color_btn = QPushButton("Własny kolor...")
        self.custom_color_btn.setObjectName("MiniIconBtn")
        self.custom_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.custom_color_btn.clicked.connect(self.pick_custom_color)
        color_header_row.addWidget(self.custom_color_btn)
        creator_layout.addLayout(color_header_row)

        color_grid = QHBoxLayout()
        color_grid.setSpacing(6)
        self.color_buttons: dict[str, QPushButton] = {}
        for hex_code in PRESET_CATEGORY_COLORS:
            c_btn = QPushButton()
            c_btn.setFixedSize(26, 26)
            c_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            c_btn.clicked.connect(lambda _c, col=hex_code: self.select_color(col))
            self.color_buttons[hex_code] = c_btn
            color_grid.addWidget(c_btn)
        color_grid.addStretch()
        creator_layout.addLayout(color_grid)

        creator_layout.addWidget(QLabel("Ikona:"))
        icon_grid = QGridLayout()
        icon_grid.setSpacing(6)
        self.icon_group = QButtonGroup(self)
        self.icon_buttons: dict[str, QPushButton] = {}

        cols_count = 7
        for idx, icon_name in enumerate(PRESET_CATEGORY_ICONS):
            i_btn = QPushButton()
            i_btn.setObjectName("IconChoiceBtn")
            i_btn.setCheckable(True)
            i_btn.setFixedSize(38, 38)
            i_btn.setIconSize(QSize(16, 16))
            i_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if icon_name == self.selected_icon:
                i_btn.setChecked(True)
            i_btn.clicked.connect(lambda _c, ic=icon_name: self.select_icon(ic))
            self.icon_group.addButton(i_btn)
            self.icon_buttons[icon_name] = i_btn
            icon_grid.addWidget(i_btn, idx // cols_count, idx % cols_count)

        creator_layout.addLayout(icon_grid)
        creator_layout.addStretch()

        self.save_cat_btn = QPushButton("Dodaj kategorię")
        self.save_cat_btn.setObjectName("PrimaryBtn")
        self.save_cat_btn.setIcon(get_safe_icon("fa5s.plus", "#ffffff"))
        self.save_cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_cat_btn.clicked.connect(self.handle_create_category)
        creator_layout.addWidget(self.save_cat_btn)

        columns.addWidget(creator_card, stretch=1)
        root_layout.addLayout(columns, stretch=1)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)
        root_layout.addLayout(bottom_row)

        self.refresh_type_tabs()
        self.refresh_color_buttons()
        self.refresh_icon_buttons()
        self.update_preview()
        self.refresh_categories_list()

    def switch_type(self, entry_type: str) -> None:
        self.current_type = entry_type
        self.refresh_type_tabs()
        self.refresh_categories_list()

    def refresh_type_tabs(self) -> None:
        is_expense = self.current_type == "expense"
        self.expense_btn.setProperty("active", "expense" if is_expense else "")
        self.income_btn.setProperty("active", "income" if not is_expense else "")
        for btn in (self.expense_btn, self.income_btn):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def select_color(self, hex_code: str) -> None:
        self.selected_color = hex_code
        self.refresh_color_buttons()
        self.update_preview()

    def pick_custom_color(self) -> None:
        chosen = QColorDialog.getColor(
            QColor(self.selected_color), self, "Wybierz kolor kategorii"
        )
        if chosen.isValid():
            self.selected_color = chosen.name()
            self.refresh_color_buttons()
            self.update_preview()

    def refresh_color_buttons(self) -> None:
        border_col = theme_manager.get_colors()["TEXT_PRIMARY"]
        for hex_code, btn in self.color_buttons.items():
            if hex_code.lower() == self.selected_color.lower():
                btn.setStyleSheet(
                    f"background-color: {hex_code}; border-radius: 13px; "
                    f"border: 3px solid {border_col};"
                )
            else:
                btn.setStyleSheet(
                    f"background-color: {hex_code}; border-radius: 13px; border: none;"
                )

    def select_icon(self, icon_name: str) -> None:
        self.selected_icon = icon_name
        self.refresh_icon_buttons()
        self.update_preview()

    def refresh_icon_buttons(self) -> None:
        neutral_col = theme_manager.get_colors()["ICON_NEUTRAL"]
        for icon_name, btn in self.icon_buttons.items():
            is_selected = icon_name == self.selected_icon
            btn.setChecked(is_selected)
            icon_color = "#ffffff" if is_selected else neutral_col
            btn.setIcon(get_safe_icon(icon_name, icon_color))

    def update_preview(self) -> None:
        typed = self.name_input.text().strip()
        self.preview_name_lbl.setText(typed if typed else "Nowa kategoria")
        self.preview_badge.setStyleSheet(
            f"background-color: {self.selected_color}; border-radius: 21px; border: none;"
        )
        self.preview_badge.setPixmap(
            get_safe_icon(self.selected_icon, "#ffffff").pixmap(19, 19)
        )

    def refresh_categories_list(self) -> None:
        while self.cats_list_layout.count() > 1:
            item = self.cats_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        categories = database.get_categories_with_counts(self.current_type)
        danger_color = theme_manager.get_colors()["DANGER_TEXT"]

        for idx, (cat_id, cat_name, color_hex, icon_name, tx_count) in enumerate(
            categories
        ):
            row_frame = QFrame()
            row_frame.setObjectName("CategoryManageRow")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(10, 7, 10, 7)
            row_layout.setSpacing(10)

            badge = QLabel()
            badge.setFixedSize(30, 30)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background-color: {color_hex}; border-radius: 15px; border: none;"
            )
            badge.setPixmap(get_safe_icon(icon_name, "#ffffff").pixmap(14, 14))
            row_layout.addWidget(badge)

            name_lbl = QLabel(cat_name)
            name_lbl.setObjectName("CardTitle")
            row_layout.addWidget(name_lbl, stretch=1)

            count_lbl = QLabel(f"{tx_count} wpisów")
            count_lbl.setObjectName("MutedText")
            row_layout.addWidget(count_lbl)

            if tx_count == 0:
                del_btn = QPushButton()
                del_btn.setObjectName("DangerBtn")
                del_btn.setFixedSize(28, 28)
                del_btn.setToolTip("Usuń pustą kategorię")
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setIcon(get_safe_icon("fa5s.trash-alt", danger_color))
                del_btn.clicked.connect(
                    lambda _c, cid=cat_id, cname=cat_name: self.handle_delete_category(
                        cid, cname
                    )
                )
                row_layout.addWidget(del_btn)

            self.cats_list_layout.insertWidget(idx, row_frame)

    def handle_create_category(self) -> None:
        try:
            new_id = database.add_category(
                name=self.name_input.text(),
                entry_type=self.current_type,
                color_hex=self.selected_color,
                icon_name=self.selected_icon,
            )
        except ValueError as err:
            QMessageBox.warning(self, "Błąd", str(err))
            return

        self.last_created_category_id = new_id
        self.name_input.clear()
        self.refresh_categories_list()

    def handle_delete_category(self, category_id: int, category_name: str) -> None:
        reply = QMessageBox.question(
            self,
            "Usuwanie kategorii",
            f"Czy na pewno usunąć pustą kategorię '{category_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            database.delete_category(category_id)
        except ValueError as err:
            QMessageBox.warning(self, "Nie można usunąć", str(err))
            return

        self.refresh_categories_list()


class AddTransactionDialog(QDialog):
    """Okno dialogowe do dodawania lub edycji wydatku/przychodu z rozwijanym kalendarzem."""

    def __init__(
        self,
        entry_type: str,
        default_date: date | None = None,
        parent=None,
        edit_data: tuple[int, str, int, int, str, str] | None = None,
    ):
        super().__init__(parent)
        self.entry_type = entry_type
        self.transaction_id: int | None = edit_data[0] if edit_data is not None else None
        is_edit = self.transaction_id is not None

        if is_edit:
            title_text = "Edytuj wydatek" if entry_type == "expense" else "Edytuj przychód"
        else:
            title_text = "Nowy wydatek" if entry_type == "expense" else "Nowy przychód"

        self.setWindowTitle(title_text)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 22)

        header = QLabel(title_text)
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("np. 49.90")

        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)
        self.category_combo = QComboBox()
        self.category_combo.setIconSize(QSize(16, 16))
        self.reload_categories(
            select_category_id=edit_data[3] if edit_data is not None else None
        )

        new_cat_btn = QPushButton()
        new_cat_btn.setObjectName("MiniIconBtn")
        new_cat_btn.setFixedSize(34, 34)
        new_cat_btn.setToolTip("Utwórz nową kategorię")
        new_cat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_cat_btn.setIcon(get_safe_icon("fa5s.plus"))
        new_cat_btn.clicked.connect(self.open_quick_category_manager)

        cat_row.addWidget(self.category_combo, stretch=1)
        cat_row.addWidget(new_cat_btn)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("np. Zakupy spożywcze / Wypłata")

        target_date = default_date or date.today()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate(target_date.year, target_date.month, target_date.day))
        self.date_input.setDisplayFormat("dd-MM-yyyy")

        # Wypełnienie pól w trybie edycji
        if edit_data is not None:
            _t_id, existing_title, amount_grosze, _cat_id, iso_date, _t_type = edit_data
            self.amount_input.setText(f"{amount_grosze / 100:.2f}")
            self.title_input.setText(existing_title)
            parsed_qdate = QDate.fromString(iso_date, "yyyy-MM-dd")
            if parsed_qdate.isValid():
                self.date_input.setDate(parsed_qdate)

        form.addRow("Kwota (zł):", self.amount_input)
        form.addRow("Kategoria:", cat_row)
        form.addRow("Opis:", self.title_input)
        form.addRow("Data:", self.date_input)
        layout.addLayout(form)

        buttons_row = QHBoxLayout()
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Zapisz zmiany" if is_edit else "Zapisz")
        save_btn.setIcon(get_safe_icon("fa5s.check", "#ffffff"))
        save_btn.setObjectName(
            "ExpenseActionBtn" if entry_type == "expense" else "IncomeActionBtn"
        )
        save_btn.clicked.connect(self.handle_save)

        buttons_row.addStretch()
        buttons_row.addWidget(cancel_btn)
        buttons_row.addWidget(save_btn)
        layout.addLayout(buttons_row)

    def reload_categories(self, select_category_id: int | None = None) -> None:
        current_id = (
            select_category_id
            if select_category_id is not None
            else self.category_combo.currentData()
        )
        self.category_combo.clear()
        for cat_id, cat_name, color_hex, icon_name in database.get_categories(
            self.entry_type
        ):
            self.category_combo.addItem(
                get_safe_icon(icon_name, color_hex), cat_name, cat_id
            )
        if current_id is not None:
            idx = self.category_combo.findData(current_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

    def open_quick_category_manager(self) -> None:
        mgr = CategoryManagerDialog(initial_type=self.entry_type, parent=self)
        mgr.exec()
        self.reload_categories(select_category_id=mgr.last_created_category_id)

    def handle_save(self) -> None:
        try:
            if self.transaction_id is not None:
                database.update_personal_transaction(
                    transaction_id=self.transaction_id,
                    title=self.title_input.text(),
                    amount_str=self.amount_input.text(),
                    category_id=self.category_combo.currentData(),
                    date_str=self.date_input.date().toString("yyyy-MM-dd"),
                )
            else:
                database.add_personal_transaction(
                    title=self.title_input.text(),
                    amount_str=self.amount_input.text(),
                    category_id=self.category_combo.currentData(),
                    date_str=self.date_input.date().toString("yyyy-MM-dd"),
                    entry_type=self.entry_type,
                )
        except ValueError as err:
            QMessageBox.warning(self, "Błąd danych", str(err))
            return
        self.accept()


class PersonalExpensesWidget(QWidget):
    """Widok 1: Wydatki / Przychody z bilansem okresu i filtrowaniem po czasie."""

    def __init__(self):
        super().__init__()
        self.current_type = "expense"
        self.current_period_mode = "month"
        self.anchor_date: date = date.today()

        self.selected_category_id: int | None = None
        self.selected_category_name: str = ""
        self.selected_category_color: str = "#3b82f6"
        self.selected_category_icon: str = "fa5s.tag"

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 18, 24, 18)
        root_layout.setSpacing(12)

        # --- Górny pasek ---
        top_bar = QHBoxLayout()

        type_switcher_frame = QFrame()
        type_switcher_frame.setObjectName("SegmentedContainer")
        type_switcher_layout = QHBoxLayout(type_switcher_frame)
        type_switcher_layout.setContentsMargins(4, 4, 4, 4)
        type_switcher_layout.setSpacing(4)

        self.expense_tab_btn = QPushButton("Wydatki")
        self.income_tab_btn = QPushButton("Przychody")
        self.expense_tab_btn.setObjectName("SegmentBtn")
        self.income_tab_btn.setObjectName("SegmentBtn")
        self.expense_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.income_tab_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.expense_tab_btn.clicked.connect(lambda: self.switch_entry_type("expense"))
        self.income_tab_btn.clicked.connect(lambda: self.switch_entry_type("income"))

        type_switcher_layout.addWidget(self.expense_tab_btn)
        type_switcher_layout.addWidget(self.income_tab_btn)

        top_bar.addWidget(type_switcher_frame)
        top_bar.addStretch()

        self.manage_cats_btn = QPushButton("Kategorie")
        self.manage_cats_btn.setIcon(get_safe_icon("fa5s.tags"))
        self.manage_cats_btn.setToolTip("Twórz i zarządzaj własnymi kategoriami")
        self.manage_cats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_cats_btn.clicked.connect(self.open_categories_manager)
        top_bar.addWidget(self.manage_cats_btn)

        self.add_entry_btn = QPushButton("Dodaj wydatek")
        self.add_entry_btn.setIcon(get_safe_icon("fa5s.plus", "#ffffff"))
        self.add_entry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_entry_btn.clicked.connect(self.open_add_dialog)
        top_bar.addWidget(self.add_entry_btn)

        root_layout.addLayout(top_bar)

        # --- Pasek okresu ---
        period_frame = QFrame()
        period_frame.setObjectName("PeriodBar")
        apply_card_shadow(period_frame)

        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(8, 6, 10, 6)
        period_layout.setSpacing(6)

        self.period_group = QButtonGroup(self)
        period_modes = [
            ("Dzień", "day"),
            ("Tydzień", "week"),
            ("Miesiąc", "month"),
            ("Rok", "year"),
        ]
        for label, mode_key in period_modes:
            btn = QPushButton(label)
            btn.setObjectName("PeriodBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if mode_key == "month":
                btn.setChecked(True)
            btn.clicked.connect(lambda _checked, m=mode_key: self.switch_period_mode(m))
            self.period_group.addButton(btn)
            period_layout.addWidget(btn)

        period_layout.addStretch()

        self.prev_period_btn = QPushButton()
        self.prev_period_btn.setObjectName("PeriodNavBtn")
        self.prev_period_btn.setIcon(get_safe_icon("fa5s.chevron-left"))
        self.prev_period_btn.setToolTip("Poprzedni okres")
        self.prev_period_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_period_btn.clicked.connect(lambda: self.step_period(-1))

        self.period_range_label = QLabel("Listopad 2026")
        self.period_range_label.setObjectName("PeriodRangeLabel")
        self.period_range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.period_range_label.setMinimumWidth(230)

        self.next_period_btn = QPushButton()
        self.next_period_btn.setObjectName("PeriodNavBtn")
        self.next_period_btn.setIcon(get_safe_icon("fa5s.chevron-right"))
        self.next_period_btn.setToolTip("Następny okres")
        self.next_period_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_period_btn.clicked.connect(lambda: self.step_period(1))

        self.today_btn = QPushButton("Dziś")
        self.today_btn.setObjectName("PeriodNavBtn")
        self.today_btn.setToolTip("Wróć do dzisiejszej daty")
        self.today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.today_btn.clicked.connect(self.reset_to_today)

        period_layout.addWidget(self.prev_period_btn)
        period_layout.addWidget(self.period_range_label)
        period_layout.addWidget(self.next_period_btn)
        period_layout.addSpacing(4)
        period_layout.addWidget(self.today_btn)

        root_layout.addWidget(period_frame)

        # --- Pasek bilansu okresu ---
        self.balance_bar = BalanceSummaryBar()
        root_layout.addWidget(self.balance_bar)

        # --- Stos ekranów ---
        self.content_stack = QStackedWidget()
        root_layout.addWidget(self.content_stack, stretch=1)

        # === EKRAN 0 ===
        overview_page = QWidget()
        overview_layout = QVBoxLayout(overview_page)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.setSpacing(12)

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        apply_card_shadow(chart_card)
        chart_card_layout = QVBoxLayout(chart_card)
        chart_card_layout.setContentsMargins(10, 8, 10, 8)

        self.donut_chart = DonutChartWidget()
        chart_card_layout.addWidget(self.donut_chart)
        overview_layout.addWidget(chart_card)

        section_lbl = QLabel("Kategorie (kliknij kategorię, aby zobaczyć listę wpisów)")
        section_lbl.setObjectName("SectionTitle")
        overview_layout.addWidget(section_lbl)

        self.categories_scroll = QScrollArea()
        self.categories_scroll.setWidgetResizable(True)
        self.categories_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.categories_scroll.setStyleSheet("background: transparent;")

        self.categories_container = QWidget()
        self.categories_container.setStyleSheet("background: transparent;")
        self.categories_list_layout = QVBoxLayout(self.categories_container)
        self.categories_list_layout.setContentsMargins(2, 2, 6, 6)
        self.categories_list_layout.setSpacing(10)
        self.categories_list_layout.addStretch()

        self.categories_scroll.setWidget(self.categories_container)
        overview_layout.addWidget(self.categories_scroll, stretch=1)

        self.content_stack.addWidget(overview_page)

        # === EKRAN 1 ===
        details_page = QWidget()
        details_layout = QVBoxLayout(details_page)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)

        details_header_card = QFrame()
        details_header_card.setObjectName("Card")
        apply_card_shadow(details_header_card)
        details_header_layout = QHBoxLayout(details_header_card)
        details_header_layout.setContentsMargins(14, 12, 18, 12)

        self.back_btn = QPushButton("Wróć do wykresu")
        self.back_btn.setIcon(get_safe_icon("fa5s.arrow-left"))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.show_overview)

        self.detail_icon_badge = QLabel()
        self.detail_icon_badge.setFixedSize(34, 34)
        self.detail_icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.detail_title_label = QLabel("Kategoria")
        self.detail_title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.detail_sum_label = QLabel("0.00 zł")
        self.detail_sum_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        details_header_layout.addWidget(self.back_btn)
        details_header_layout.addSpacing(12)
        details_header_layout.addWidget(self.detail_icon_badge)
        details_header_layout.addWidget(self.detail_title_label)
        details_header_layout.addStretch()
        details_header_layout.addWidget(self.detail_sum_label)

        details_layout.addWidget(details_header_card)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(["ID", "Data", "Opis", "Kwota"])
        self.detail_table.setColumnHidden(0, True)
        self.detail_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.detail_table.cellDoubleClicked.connect(self.handle_edit_detail_entry)
        details_layout.addWidget(self.detail_table, stretch=1)

        detail_bottom_row = QHBoxLayout()

        self.edit_entry_btn = QPushButton("Edytuj zaznaczony wpis")
        self.edit_entry_btn.setIcon(get_safe_icon("fa5s.edit"))
        self.edit_entry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_entry_btn.clicked.connect(lambda: self.handle_edit_detail_entry())

        self.delete_entry_btn = QPushButton("Usuń zaznaczony wpis")
        self.delete_entry_btn.setObjectName("DangerBtn")
        self.delete_entry_btn.setIcon(get_safe_icon("fa5s.trash-alt", "#dc2626"))
        self.delete_entry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_entry_btn.clicked.connect(self.handle_delete_detail_entry)

        edit_hint_lbl = QLabel("Kliknij dwukrotnie dowolny wiersz, aby go edytować")
        edit_hint_lbl.setObjectName("MutedText")

        detail_bottom_row.addWidget(self.edit_entry_btn)
        detail_bottom_row.addWidget(self.delete_entry_btn)
        detail_bottom_row.addStretch()
        detail_bottom_row.addWidget(edit_hint_lbl)
        details_layout.addLayout(detail_bottom_row)

        self.content_stack.addWidget(details_page)

        theme_manager.theme_changed.connect(self.on_theme_changed)
        self.update_top_styles()
        self.refresh_current_view()

    def get_active_period(self) -> tuple[str, str, str]:
        d = self.anchor_date
        today = date.today()

        if self.current_period_mode == "day":
            weekday = WEEKDAYS_PL[d.weekday()]
            label = f"{d.day:02d}-{d.month:02d}-{d.year} ({weekday})"
            if d == today:
                label += " • Dziś"
            iso = d.isoformat()
            return iso, iso, label

        if self.current_period_mode == "week":
            start = d - timedelta(days=d.weekday())
            end = start + timedelta(days=6)
            week_num = start.isocalendar().week
            label = (
                f"{start.day:02d}-{start.month:02d}-{start.year} – "
                f"{end.day:02d}-{end.month:02d}-{end.year} (Tydz. {week_num})"
            )
            return start.isoformat(), end.isoformat(), label

        if self.current_period_mode == "month":
            last_day = calendar.monthrange(d.year, d.month)[1]
            start = date(d.year, d.month, 1)
            end = date(d.year, d.month, last_day)
            label = f"{MONTHS_NOMINATIVE[d.month]} {d.year}"
            return start.isoformat(), end.isoformat(), label

        start = date(d.year, 1, 1)
        end = date(d.year, 12, 31)
        label = f"Rok {d.year}"
        return start.isoformat(), end.isoformat(), label

    def switch_period_mode(self, mode: str) -> None:
        self.current_period_mode = mode
        self.refresh_current_view()

    def step_period(self, delta: int) -> None:
        d = self.anchor_date

        if self.current_period_mode == "day":
            self.anchor_date = d + timedelta(days=delta)
        elif self.current_period_mode == "week":
            self.anchor_date = d + timedelta(days=7 * delta)
        elif self.current_period_mode == "month":
            total_months = (d.year * 12 + (d.month - 1)) + delta
            new_year = total_months // 12
            new_month = (total_months % 12) + 1
            max_day = calendar.monthrange(new_year, new_month)[1]
            self.anchor_date = date(new_year, new_month, min(d.day, max_day))
        elif self.current_period_mode == "year":
            new_year = d.year + delta
            max_day = calendar.monthrange(new_year, d.month)[1]
            self.anchor_date = date(new_year, d.month, min(d.day, max_day))

        self.refresh_current_view()

    def reset_to_today(self) -> None:
        self.anchor_date = date.today()
        self.refresh_current_view()

    def refresh_current_view(self) -> None:
        start_iso, end_iso, period_label = self.get_active_period()
        self.period_range_label.setText(period_label)

        income_grosze, expense_grosze = database.get_period_totals(start_iso, end_iso)
        self.balance_bar.update_totals(income_grosze, expense_grosze)

        if self.content_stack.currentIndex() == 1 and self.selected_category_id is not None:
            self.open_category_details(
                self.selected_category_id,
                self.selected_category_name,
                self.selected_category_color,
                self.selected_category_icon,
            )
        else:
            self.refresh_overview()

    def on_theme_changed(self, _mode: str) -> None:
        self.manage_cats_btn.setIcon(get_safe_icon("fa5s.tags"))
        self.back_btn.setIcon(get_safe_icon("fa5s.arrow-left"))
        self.edit_entry_btn.setIcon(get_safe_icon("fa5s.edit"))
        self.prev_period_btn.setIcon(get_safe_icon("fa5s.chevron-left"))
        self.next_period_btn.setIcon(get_safe_icon("fa5s.chevron-right"))
        danger_color = theme_manager.get_colors()["DANGER_TEXT"]
        self.delete_entry_btn.setIcon(get_safe_icon("fa5s.trash-alt", danger_color))
        self.refresh_current_view()

    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def update_top_styles(self) -> None:
        is_expense = self.current_type == "expense"

        self.expense_tab_btn.setProperty("active", "expense" if is_expense else "")
        self.income_tab_btn.setProperty("active", "income" if not is_expense else "")
        self._repolish(self.expense_tab_btn)
        self._repolish(self.income_tab_btn)

        self.add_entry_btn.setText(
            "Dodaj wydatek" if is_expense else "Dodaj przychód"
        )
        self.add_entry_btn.setObjectName(
            "ExpenseActionBtn" if is_expense else "IncomeActionBtn"
        )
        self._repolish(self.add_entry_btn)

    def switch_entry_type(self, entry_type: str) -> None:
        self.current_type = entry_type
        self.update_top_styles()
        self.show_overview()

    def open_categories_manager(self) -> None:
        dialog = CategoryManagerDialog(initial_type=self.current_type, parent=self)
        dialog.exec()
        self.refresh_current_view()

    def open_add_dialog(self) -> None:
        start_iso, end_iso, _ = self.get_active_period()
        today_iso = date.today().isoformat()
        suggested_date = (
            date.today() if start_iso <= today_iso <= end_iso else self.anchor_date
        )

        dialog = AddTransactionDialog(self.current_type, suggested_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_current_view()

    def show_overview(self) -> None:
        self.selected_category_id = None
        self.content_stack.setCurrentIndex(0)
        self.refresh_current_view()

    def refresh_overview(self) -> None:
        start_iso, end_iso, period_label = self.get_active_period()
        self.period_range_label.setText(period_label)

        summary = database.get_category_summary(
            entry_type=self.current_type,
            start_date=start_iso,
            end_date=end_iso,
        )
        total_grosze = sum(row[4] for row in summary)

        subtitle = (
            "Suma wydatków" if self.current_type == "expense" else "Suma przychodów"
        )
        chart_slices = [(row[1], row[4], row[2]) for row in summary]
        self.donut_chart.set_data(chart_slices, subtitle)

        while self.categories_list_layout.count() > 1:
            item = self.categories_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not summary:
            empty_card = QFrame()
            empty_card.setObjectName("Card")
            empty_layout = QVBoxLayout(empty_card)
            empty_label = QLabel(
                f"Brak wpisów dla okresu: {period_label}.\n"
                "Użyj strzałek < > powyżej, aby przejść do innego okresu, lub kliknij 'Dodaj'."
            )
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setObjectName("MutedText")
            empty_label.setStyleSheet("padding: 24px; font-size: 13px;")
            empty_layout.addWidget(empty_label)
            self.categories_list_layout.insertWidget(0, empty_card)
            return

        for idx, (cat_id, cat_name, color_hex, icon_name, cat_grosze, count) in enumerate(
            summary
        ):
            percentage = (cat_grosze / total_grosze * 100) if total_grosze > 0 else 0.0
            card = CategoryCardButton(
                category_id=cat_id,
                name=cat_name,
                color_hex=color_hex,
                icon_name=icon_name,
                amount_grosze=cat_grosze,
                entries_count=count,
                percentage=percentage,
            )
            card.clicked.connect(self.open_category_details)
            self.categories_list_layout.insertWidget(idx, card)

    def open_category_details(
        self, category_id: int, category_name: str, color_hex: str, icon_name: str
    ) -> None:
        self.selected_category_id = category_id
        self.selected_category_name = category_name
        self.selected_category_color = color_hex
        self.selected_category_icon = icon_name

        start_iso, end_iso, period_label = self.get_active_period()
        self.period_range_label.setText(period_label)

        entries = database.get_transactions_by_category(
            category_id=category_id,
            entry_type=self.current_type,
            start_date=start_iso,
            end_date=end_iso,
        )

        self.detail_icon_badge.setStyleSheet(
            f"background-color: {color_hex}; border-radius: 17px;"
        )
        self.detail_icon_badge.setPixmap(get_safe_icon(icon_name, "#ffffff").pixmap(16, 16))
        self.detail_title_label.setText(f"{category_name}  •  {period_label}")

        cat_total = sum(row[3] for row in entries)
        self.detail_sum_label.setText(format_pln(cat_total))

        self.detail_table.setRowCount(len(entries))
        for row_idx, (t_id, date_str, title, amount_grosze) in enumerate(entries):
            self.detail_table.setItem(row_idx, 0, QTableWidgetItem(str(t_id)))
            self.detail_table.setItem(row_idx, 1, QTableWidgetItem(format_date_pl(date_str)))
            self.detail_table.setItem(row_idx, 2, QTableWidgetItem(title))
            self.detail_table.setItem(row_idx, 3, QTableWidgetItem(format_pln(amount_grosze)))

        self.content_stack.setCurrentIndex(1)

    def handle_edit_detail_entry(
        self, row: int | None = None, _column: int | None = None
    ) -> None:
        if row is None:
            selected_rows = self.detail_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.information(self, "Informacja", "Zaznacz wpis do edycji.")
                return
            row_index = selected_rows[0].row()
        else:
            row_index = row

        id_item = self.detail_table.item(row_index, 0)
        if id_item is None:
            return

        transaction_id = int(id_item.text())
        tx_data = database.get_personal_transaction_by_id(transaction_id)
        if tx_data is None:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono wybranego wpisu w bazie.")
            self.refresh_current_view()
            return

        dialog = AddTransactionDialog(
            entry_type=self.current_type,
            parent=self,
            edit_data=tx_data,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_current_view()

    def handle_delete_detail_entry(self) -> None:
        selected_rows = self.detail_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Informacja", "Zaznacz wpis do usunięcia.")
            return

        row_index = selected_rows[0].row()
        transaction_id = int(self.detail_table.item(row_index, 0).text())
        database.delete_personal_transaction(transaction_id)
        self.refresh_current_view()