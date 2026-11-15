from datetime import date
from decimal import Decimal, InvalidOperation
import os
import sqlite3
import sys

DEFAULT_EXPENSE_CATEGORIES = [
    ("Jedzenie", "#f97316", "fa5s.utensils"),
    ("Mieszkanie i rachunki", "#3b82f6", "fa5s.home"),
    ("Transport", "#8b5cf6", "fa5s.car"),
    ("Rozrywka", "#ec4899", "fa5s.film"),
    ("Zakupy", "#eab308", "fa5s.shopping-bag"),
    ("Zdrowie", "#14b8a6", "fa5s.heartbeat"),
    ("Inne", "#64748b", "fa5s.tag"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Wynagrodzenie", "#10b981", "fa5s.briefcase"),
    ("Premia / Bonus", "#06b6d4", "fa5s.star"),
    ("Prezent", "#8b5cf6", "fa5s.gift"),
    ("Sprzedaż", "#f59e0b", "fa5s.store"),
    ("Inne przychody", "#64748b", "fa5s.coins"),
]


def get_db_path() -> str:
    """Zwraca ścieżkę do pliku bazy danych obok skryptu .py lub przyszłego pliku .exe."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "finanse.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def init_db() -> None:
    """Tworzy i aktualizuje tabele dla wydatków, przychodów oraz grup."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense',
                color TEXT NOT NULL DEFAULT '#3b82f6',
                icon TEXT NOT NULL DEFAULT 'fa5s.tag'
            )
        """)

        if not _column_exists(cursor, "categories", "type"):
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'"
            )
        if not _column_exists(cursor, "categories", "color"):
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN color TEXT NOT NULL DEFAULT '#3b82f6'"
            )
        if not _column_exists(cursor, "categories", "icon"):
            cursor.execute(
                "ALTER TABLE categories ADD COLUMN icon TEXT NOT NULL DEFAULT 'fa5s.tag'"
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount_grosze INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense',
                paid_by TEXT NOT NULL DEFAULT 'Ja',
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        if not _column_exists(cursor, "transactions", "type"):
            cursor.execute(
                "ALTER TABLE transactions ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'"
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                member_name TEXT NOT NULL,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            )
        """)

        for name, color, icon in DEFAULT_EXPENSE_CATEGORIES:
            cursor.execute(
                "UPDATE categories SET color = ?, icon = ? WHERE name = ? AND type = 'expense'",
                (color, icon, name),
            )

        for name, color, icon in DEFAULT_INCOME_CATEGORIES:
            cursor.execute(
                "UPDATE categories SET color = ?, icon = ? WHERE name = ? AND type = 'income'",
                (color, icon, name),
            )

        cursor.execute("SELECT COUNT(*) FROM categories WHERE type = 'expense'")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO categories (name, type, color, icon) VALUES (?, 'expense', ?, ?)",
                DEFAULT_EXPENSE_CATEGORIES,
            )

        cursor.execute("SELECT COUNT(*) FROM categories WHERE type = 'income'")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO categories (name, type, color, icon) VALUES (?, 'income', ?, ?)",
                DEFAULT_INCOME_CATEGORIES,
            )

        conn.commit()


# =========================================================
# FUNKCJE MODUŁU 1: WYDATKI I PRZYCHODY OSOBISTE
# =========================================================


def get_categories(entry_type: str = "expense") -> list[tuple[int, str, str, str]]:
    """Zwraca listę krotek (id, nazwa, kolor_hex, ikona) dla 'expense' lub 'income'."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, color, icon FROM categories WHERE type = ? ORDER BY id ASC",
            (entry_type,),
        )
        return cursor.fetchall()
def add_category(
    name: str,
    entry_type: str,
    color_hex: str,
    icon_name: str,
) -> int:
    """Tworzy nową kategorię wydatków lub przychodów i zwraca jej ID."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Podaj nazwę kategorii (np. Zwierzęta, Paliwo, Kawa).")

    if entry_type not in ("expense", "income"):
        raise ValueError("Niepoprawny typ kategorii.")

    clean_color = color_hex.strip() or "#3b82f6"
    clean_icon = icon_name.strip() or "fa5s.tag"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?) AND type = ?",
            (clean_name, entry_type),
        )
        if cursor.fetchone() is not None:
            raise ValueError(
                f"Kategoria '{clean_name}' już istnieje w tej zakładce."
            )

        cursor.execute(
            """
            INSERT INTO categories (name, type, color, icon)
            VALUES (?, ?, ?, ?)
            """,
            (clean_name, entry_type, clean_color, clean_icon),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_categories_with_counts(
    entry_type: str = "expense",
) -> list[tuple[int, str, str, str, int]]:
    """
    Zwraca listę wszystkich kategorii dla danego typu wraz z liczbą przypisanych wpisów:
    (id, name, color_hex, icon_name, transactions_count)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                c.id,
                c.name,
                c.color,
                c.icon,
                COUNT(t.id) AS tx_count
            FROM categories c
            LEFT JOIN transactions t ON t.category_id = c.id
            WHERE c.type = ?
            GROUP BY c.id, c.name, c.color, c.icon
            ORDER BY c.id ASC
            """,
            (entry_type,),
        )
        return cursor.fetchall()


def delete_category(category_id: int) -> None:
    """Usuwa pustą kategorię (zabezpiecza przed usunięciem kategorii z istniejącymi wpisami)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT type FROM categories WHERE id = ?",
            (category_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return
        entry_type = row[0]

        cursor.execute(
            "SELECT COUNT(*) FROM transactions WHERE category_id = ?",
            (category_id,),
        )
        tx_count = int(cursor.fetchone()[0])
        if tx_count > 0:
            raise ValueError(
                f"Nie można usunąć kategorii, ponieważ przypisano do niej {tx_count} wpis(ów)."
            )

        cursor.execute(
            "SELECT COUNT(*) FROM categories WHERE type = ?",
            (entry_type,),
        )
        if int(cursor.fetchone()[0]) <= 1:
            raise ValueError("Musi pozostać co najmniej jedna kategoria w tej zakładce.")

        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()

def add_personal_transaction(
    title: str,
    amount_str: str,
    category_id: int,
    date_str: str,
    entry_type: str = "expense",
) -> None:
    if not title.strip():
        raise ValueError("Podaj nazwę lub opis pozycji.")

    normalized = amount_str.strip().replace(",", ".")
    try:
        amount_decimal = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("Niepoprawny format kwoty (np. wpisz 45.50).") from exc

    if amount_decimal <= 0:
        raise ValueError("Kwota musi być większa od zera.")

    amount_grosze = int(round(amount_decimal * 100))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (title, amount_grosze, category_id, date, type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title.strip(), amount_grosze, category_id, date_str, entry_type),
        )
        conn.commit()


def get_category_summary(
    entry_type: str = "expense",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[tuple[int, str, str, str, int, int]]:
    """
    Zwraca podsumowanie pogrupowane po kategoriach dla wybranego zakresu dat:
    (category_id, category_name, color_hex, icon_name, total_grosze, entries_count)
    """
    query = """
        SELECT
            c.id,
            c.name,
            c.color,
            c.icon,
            SUM(t.amount_grosze) AS total_grosze,
            COUNT(t.id) AS entries_count
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.type = ?
    """
    params: list[object] = [entry_type]

    if start_date is not None:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date is not None:
        query += " AND t.date <= ?"
        params.append(end_date)

    query += """
        GROUP BY c.id, c.name, c.color, c.icon
        ORDER BY total_grosze DESC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
def get_period_totals(
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[int, int]:
    """
    Zwraca krotkę (przychody_grosze, wydatki_grosze) dla podanego zakresu dat.
    """
    query = """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount_grosze ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount_grosze ELSE 0 END), 0)
        FROM transactions
        WHERE 1 = 1
    """
    params: list[object] = []

    if start_date is not None:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date is not None:
        query += " AND date <= ?"
        params.append(end_date)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return int(row[0]), int(row[1])

def get_transactions_by_category(
    category_id: int,
    entry_type: str = "expense",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[tuple[int, str, str, int]]:
    """Zwraca pojedyncze wpisy w wybranej kategorii i zakresie dat."""
    query = """
        SELECT id, date, title, amount_grosze
        FROM transactions
        WHERE category_id = ? AND type = ?
    """
    params: list[object] = [category_id, entry_type]

    if start_date is not None:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date is not None:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def delete_personal_transaction(transaction_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
def get_personal_transaction_by_id(
    transaction_id: int,
) -> tuple[int, str, int, int, str, str] | None:
    """Zwraca (id, title, amount_grosze, category_id, date, type) dla pojedynczego wpisu."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, amount_grosze, category_id, date, type
            FROM transactions
            WHERE id = ?
            """,
            (transaction_id,),
        )
        return cursor.fetchone()


def update_personal_transaction(
    transaction_id: int,
    title: str,
    amount_str: str,
    category_id: int,
    date_str: str,
) -> None:
    """Aktualizuje istniejący wydatek lub przychód."""
    if not title.strip():
        raise ValueError("Podaj nazwę lub opis pozycji.")

    normalized = amount_str.strip().replace(" ", "").replace(",", ".")
    try:
        amount_decimal = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("Niepoprawny format kwoty (np. wpisz 45.50).") from exc

    if amount_decimal <= 0:
        raise ValueError("Kwota musi być większa od zera.")

    amount_grosze = int(round(amount_decimal * 100))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE transactions
            SET title = ?, amount_grosze = ?, category_id = ?, date = ?
            WHERE id = ?
            """,
            (title.strip(), amount_grosze, category_id, date_str, transaction_id),
        )
        conn.commit()

# =========================================================
# FUNKCJE MODUŁU 2: GRUPY (SPLITWISE)
# =========================================================


def create_group(group_name: str, members: list[str]) -> int:
    clean_name = group_name.strip()
    if not clean_name:
        raise ValueError("Podaj nazwę grupy (np. Wyjazd w góry, Mieszkanie).")

    cleaned_members: list[str] = []
    seen_lower: set[str] = set()
    for member in members:
        m = member.strip()
        if m and m.lower() not in seen_lower:
            cleaned_members.append(m)
            seen_lower.add(m.lower())

    if len(cleaned_members) < 2:
        raise ValueError("Grupa musi składać się z co najmniej 2 różnych osób.")

    today_str = date.today().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO groups (name, created_at) VALUES (?, ?)",
            (clean_name, today_str),
        )
        group_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO group_members (group_id, member_name) VALUES (?, ?)",
            [(group_id, member_name) for member_name in cleaned_members],
        )
        conn.commit()
        return int(group_id)


def get_all_groups() -> list[tuple[int, str, str, list[str]]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM groups ORDER BY id DESC")
        groups_rows = cursor.fetchall()

        result: list[tuple[int, str, str, list[str]]] = []
        for g_id, g_name, created_at in groups_rows:
            cursor.execute(
                "SELECT member_name FROM group_members WHERE group_id = ? ORDER BY id ASC",
                (g_id,),
            )
            members = [row[0] for row in cursor.fetchall()]
            result.append((g_id, g_name, created_at, members))
        return result


def delete_group(group_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        conn.commit()