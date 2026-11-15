import sys
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import database
from groups_view import GroupsSplitWidget
from personal_view import PersonalExpensesWidget
from theme import apply_stylesheet, get_safe_icon, theme_manager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finanse App — Menedżer Budżetu")
        self.setWindowIcon(get_safe_icon("fa5s.wallet", "#3b82f6"))
        self.resize(1140, 740)

        root_widget = QWidget()
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Lewy panel boczny ---
        sidebar_container = QWidget()
        sidebar_container.setObjectName("Sidebar")
        sidebar_container.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 18, 0, 18)
        sidebar_layout.setSpacing(12)

        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(18, 4, 18, 8)
        logo_row.setSpacing(10)

        logo_icon = QLabel()
        logo_icon.setPixmap(get_safe_icon("fa5s.wallet", "#3b82f6").pixmap(22, 22))
        app_title = QLabel("Finanse App")
        app_title.setObjectName("AppLogo")

        logo_row.addWidget(logo_icon)
        logo_row.addWidget(app_title)
        logo_row.addStretch()
        sidebar_layout.addLayout(logo_row)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(16, 16))
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        item_personal = QListWidgetItem(
            get_safe_icon("fa5s.chart-pie", "#cbd5e1"), "  Wydatki i Przychody"
        )
        item_groups = QListWidgetItem(
            get_safe_icon("fa5s.users", "#cbd5e1"), "  Rozliczenia grupowe"
        )

        self.nav_list.addItem(item_personal)
        self.nav_list.addItem(item_groups)

        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        # --- Przełącznik motywu na dole panelu bocznego ---
        theme_box = QHBoxLayout()
        theme_box.setContentsMargins(14, 0, 14, 0)

        self.theme_toggle_btn = QPushButton("  Tryb ciemny")
        self.theme_toggle_btn.setObjectName("ThemeToggleBtn")
        self.theme_toggle_btn.setIcon(get_safe_icon("fa5s.moon", "#fbbf24"))
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.clicked.connect(theme_manager.toggle_theme)

        theme_box.addWidget(self.theme_toggle_btn)
        sidebar_layout.addLayout(theme_box)

        root_layout.addWidget(sidebar_container)

        # --- Prawa strona: stos widoków ---
        self.pages = QStackedWidget()
        self.personal_page = PersonalExpensesWidget()
        self.groups_page = GroupsSplitWidget()

        self.pages.addWidget(self.personal_page)
        self.pages.addWidget(self.groups_page)

        root_layout.addWidget(self.pages, stretch=1)

        self.nav_list.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        theme_manager.theme_changed.connect(self.update_theme_button)
        self.setCentralWidget(root_widget)

    def update_theme_button(self, mode: str) -> None:
        if mode == "dark":
            self.theme_toggle_btn.setText("  Tryb jasny")
            self.theme_toggle_btn.setIcon(get_safe_icon("fa5s.sun", "#fbbf24"))
        else:
            self.theme_toggle_btn.setText("  Tryb ciemny")
            self.theme_toggle_btn.setIcon(get_safe_icon("fa5s.moon", "#fbbf24"))


if __name__ == "__main__":
    database.init_db()
    app = QApplication(sys.argv)
    apply_stylesheet(app, "light")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())