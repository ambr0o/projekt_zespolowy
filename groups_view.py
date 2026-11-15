from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database
from theme import apply_card_shadow, get_safe_icon, theme_manager


class GroupsSplitWidget(QWidget):
    """Widok 2: Tworzenie grup i rozliczenia w stylu Splitwise."""

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        header = QLabel("Rozliczenia grupowe")
        header.setObjectName("PageTitle")
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # --- Lewa karta: Kreator nowej grupy ---
        create_card = QFrame()
        create_card.setObjectName("Card")
        create_card.setMaximumWidth(380)
        apply_card_shadow(create_card)

        create_layout = QVBoxLayout(create_card)
        create_layout.setContentsMargins(18, 18, 18, 18)
        create_layout.setSpacing(10)

        card_title = QLabel("Utwórz nową grupę (min. 2 osoby)")
        card_title.setObjectName("SectionTitle")
        create_layout.addWidget(card_title)

        create_layout.addWidget(QLabel("Nazwa grupy:"))
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("np. Wyjazd w Bieszczady / Mieszkanie")
        create_layout.addWidget(self.group_name_input)

        create_layout.addSpacing(4)
        create_layout.addWidget(QLabel("Uczestnicy grupy:"))

        member_add_row = QHBoxLayout()
        self.member_name_input = QLineEdit()
        self.member_name_input.setPlaceholderText("Imię uczestnika (np. Ania)")
        self.member_name_input.returnPressed.connect(self.handle_add_member_to_draft)

        self.add_member_btn = QPushButton("Dodaj")
        self.add_member_btn.setIcon(get_safe_icon("fa5s.user-plus"))
        self.add_member_btn.clicked.connect(self.handle_add_member_to_draft)

        member_add_row.addWidget(self.member_name_input)
        member_add_row.addWidget(self.add_member_btn)
        create_layout.addLayout(member_add_row)

        self.draft_members_list = QListWidget()
        self.draft_members_list.setObjectName("MembersDraftList")
        self.draft_members_list.setMaximumHeight(170)
        create_layout.addWidget(self.draft_members_list)

        self.remove_member_btn = QPushButton("Usuń zaznaczoną osobę")
        self.remove_member_btn.clicked.connect(self.handle_remove_member_from_draft)
        create_layout.addWidget(self.remove_member_btn)

        create_layout.addSpacing(8)
        self.create_group_btn = QPushButton("Utwórz grupę")
        self.create_group_btn.setObjectName("PrimaryBtn")
        self.create_group_btn.setIcon(get_safe_icon("fa5s.check", "#ffffff"))
        self.create_group_btn.clicked.connect(self.handle_create_group)
        create_layout.addWidget(self.create_group_btn)

        create_layout.addStretch()
        content_layout.addWidget(create_card)

        # --- Prawa kolumna: Lista zapisanych grup i szczegóły ---
        right_layout = QVBoxLayout()
        right_layout.setSpacing(14)

        groups_card = QFrame()
        groups_card.setObjectName("Card")
        apply_card_shadow(groups_card)
        groups_list_layout = QVBoxLayout(groups_card)
        groups_list_layout.setContentsMargins(18, 18, 18, 18)
        groups_list_layout.setSpacing(10)

        groups_title = QLabel("Twoje grupy")
        groups_title.setObjectName("SectionTitle")
        groups_list_layout.addWidget(groups_title)

        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(4)
        self.groups_table.setHorizontalHeaderLabels(
            ["ID", "Nazwa grupy", "Liczba osób", "Uczestnicy"]
        )
        self.groups_table.setColumnHidden(0, True)
        self.groups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.groups_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.groups_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.groups_table.itemSelectionChanged.connect(self.handle_group_selected)
        groups_list_layout.addWidget(self.groups_table)

        groups_actions_row = QHBoxLayout()
        self.delete_group_btn = QPushButton("Usuń zaznaczoną grupę")
        self.delete_group_btn.setObjectName("DangerBtn")
        self.delete_group_btn.setIcon(get_safe_icon("fa5s.trash-alt", "#dc2626"))
        self.delete_group_btn.clicked.connect(self.handle_delete_group)
        groups_actions_row.addWidget(self.delete_group_btn)
        groups_actions_row.addStretch()
        groups_list_layout.addLayout(groups_actions_row)

        right_layout.addWidget(groups_card)

        details_card = QFrame()
        details_card.setObjectName("Card")
        apply_card_shadow(details_card)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(18, 16, 18, 16)
        details_layout.setSpacing(6)

        details_title = QLabel("Szczegóły i rozliczenia wybranej grupy")
        details_title.setObjectName("SectionTitle")
        details_layout.addWidget(details_title)

        self.selected_group_label = QLabel(
            "Wybierz grupę z tabeli powyżej, aby zobaczyć jej skład."
        )
        self.selected_group_label.setWordWrap(True)
        details_layout.addWidget(self.selected_group_label)

        next_step_hint = QLabel(
            "Następny etap rozwoju tego modułu: dodawanie wspólnych rachunków "
            "(kto zapłacił i na kogo dzielimy kwotę) oraz automatyczne wyliczanie długów."
        )
        next_step_hint.setWordWrap(True)
        next_step_hint.setObjectName("MutedText")
        details_layout.addWidget(next_step_hint)

        right_layout.addWidget(details_card)
        content_layout.addLayout(right_layout, stretch=1)

        main_layout.addLayout(content_layout)
        theme_manager.theme_changed.connect(self.on_theme_changed)
        self.refresh_groups_table()

    def on_theme_changed(self, _mode: str) -> None:
        self.add_member_btn.setIcon(get_safe_icon("fa5s.user-plus"))
        danger_color = theme_manager.get_colors()["DANGER_TEXT"]
        self.delete_group_btn.setIcon(get_safe_icon("fa5s.trash-alt", danger_color))

    def handle_add_member_to_draft(self) -> None:
        name = self.member_name_input.text().strip()
        if not name:
            return

        existing = [
            self.draft_members_list.item(i).text().lower()
            for i in range(self.draft_members_list.count())
        ]
        if name.lower() in existing:
            QMessageBox.information(
                self, "Duplikat", f"Osoba '{name}' jest już na liście uczestników."
            )
            return

        self.draft_members_list.addItem(name)
        self.member_name_input.clear()
        self.member_name_input.setFocus()

    def handle_remove_member_from_draft(self) -> None:
        row = self.draft_members_list.currentRow()
        if row >= 0:
            self.draft_members_list.takeItem(row)

    def handle_create_group(self) -> None:
        group_name = self.group_name_input.text()
        members = [
            self.draft_members_list.item(i).text()
            for i in range(self.draft_members_list.count())
        ]

        try:
            database.create_group(group_name, members)
        except ValueError as err:
            QMessageBox.warning(self, "Błąd tworzenia grupy", str(err))
            return

        self.group_name_input.clear()
        self.member_name_input.clear()
        self.draft_members_list.clear()
        self.refresh_groups_table()

    def handle_delete_group(self) -> None:
        selected_rows = self.groups_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Informacja", "Zaznacz grupę do usunięcia.")
            return

        row_index = selected_rows[0].row()
        group_id = int(self.groups_table.item(row_index, 0).text())
        group_name = self.groups_table.item(row_index, 1).text()

        reply = QMessageBox.question(
            self,
            "Potwierdzenie",
            f"Czy na pewno usunąć grupę '{group_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            database.delete_group(group_id)
            self.refresh_groups_table()
            self.selected_group_label.setText(
                "Wybierz grupę z tabeli powyżej, aby zobaczyć jej skład."
            )

    def handle_group_selected(self) -> None:
        selected_rows = self.groups_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row_index = selected_rows[0].row()
        group_name = self.groups_table.item(row_index, 1).text()
        members_str = self.groups_table.item(row_index, 3).text()
        self.selected_group_label.setText(
            f"Aktywna grupa: <b>{group_name}</b><br>Uczestnicy: {members_str}"
        )

    def refresh_groups_table(self) -> None:
        groups = database.get_all_groups()
        self.groups_table.setRowCount(len(groups))

        for row_idx, (g_id, g_name, _created_at, members) in enumerate(groups):
            self.groups_table.setItem(row_idx, 0, QTableWidgetItem(str(g_id)))
            self.groups_table.setItem(row_idx, 1, QTableWidgetItem(g_name))
            count_item = QTableWidgetItem(str(len(members)))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.groups_table.setItem(row_idx, 2, count_item)
            self.groups_table.setItem(row_idx, 3, QTableWidgetItem(", ".join(members)))