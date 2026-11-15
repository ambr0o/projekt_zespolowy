from datetime import date, timedelta
import database


def seed_sample_data() -> None:
    database.init_db()

    expense_cats = {name: cat_id for cat_id, name, _c, _i in database.get_categories("expense")}
    income_cats = {name: cat_id for cat_id, name, _c, _i in database.get_categories("income")}

    today = date.today()

    # Lista przykładowych transakcji: (dni_wstecz, typ, kategoria, opis, kwota)
    sample_entries: list[tuple[int, str, str, str, str]] = [
        # --- Dzisiaj ---
        (0, "expense", "Jedzenie", "Kawa i kanapka na mieście", "28.50"),
        (0, "expense", "Transport", "Bilet dobowy komunikacja", "15.00"),
        (0, "income", "Sprzedaż", "Sprzedaż starego monitora OLX", "350.00"),
        # --- Bieżący tydzień (kilka dni wstecz) ---
        (1, "expense", "Jedzenie", "Zakupy spożywcze Biedronka", "142.80"),
        (2, "expense", "Rozrywka", "Bilety do kina + popcorn", "86.00"),
        (3, "expense", "Zdrowie", "Apteka — witaminy i leki", "64.20"),
        (4, "expense", "Zakupy", "Koszulka i skarpetki", "119.99"),
        (5, "expense", "Jedzenie", "Pizza ze znajomymi", "74.00"),
        (6, "expense", "Transport", "Tankowanie paliwa", "235.50"),
        # --- Wcześniej w bieżącym miesiącu ---
        (8, "expense", "Mieszkanie i rachunki", "Czynsz za mieszkanie", "1850.00"),
        (8, "expense", "Mieszkanie i rachunki", "Internet światłowodowy", "79.99"),
        (9, "income", "Wynagrodzenie", "Wypłata — etat", "6400.00"),
        (10, "expense", "Jedzenie", "Zakupy Lidl na cały tydzień", "218.40"),
        (11, "expense", "Rozrywka", "Subskrypcja Spotify + Netflix", "72.00"),
        (12, "expense", "Zakupy", "Słuchawki bezprzewodowe", "299.00"),
        (13, "expense", "Jedzenie", "Obiad w barze mlecznym", "34.00"),
        (14, "income", "Premia / Bonus", "Premia projektowa", "850.00"),
        # --- Poprzedni miesiąc (ok. 30-45 dni temu) ---
        (25, "expense", "Mieszkanie i rachunki", "Rachunek za prąd", "195.40"),
        (27, "expense", "Jedzenie", "Zakupy Auchan", "264.10"),
        (29, "expense", "Transport", "Przegląd techniczny auta", "99.00"),
        (31, "expense", "Zdrowie", "Wizyta u stomatologa", "320.00"),
        (33, "expense", "Rozrywka", "Koncert klubowy", "140.00"),
        (35, "expense", "Zakupy", "Kurtka jesienna", "389.00"),
        (37, "expense", "Jedzenie", "Restauracja sushi", "168.00"),
        (38, "expense", "Mieszkanie i rachunki", "Czynsz za mieszkanie", "1850.00"),
        (39, "income", "Wynagrodzenie", "Wypłata — etat", "6400.00"),
        (41, "income", "Prezent", "Prezent urodzinowy od rodziny", "400.00"),
        (42, "expense", "Inne", "Prezent dla kolegi", "110.00"),
        # --- 2 miesiące temu (ok. 60-75 dni temu) ---
        (58, "expense", "Transport", "Bilet PKP Intercity", "124.00"),
        (60, "expense", "Jedzenie", "Zakupy spożywcze", "198.75"),
        (62, "expense", "Rozrywka", "Wyjście na kręgle", "95.00"),
        (64, "expense", "Zakupy", "Książki techniczne", "145.50"),
        (66, "expense", "Mieszkanie i rachunki", "Czynsz + media", "1920.00"),
        (68, "income", "Wynagrodzenie", "Wypłata — etat", "6200.00"),
        (70, "expense", "Zdrowie", "Karnet na siłownię", "139.00"),
        (72, "expense", "Jedzenie", "Kawiarnia i ciasto", "42.00"),
        (74, "income", "Inne przychody", "Zwrot podatku / nadpłata", "280.00"),
        # --- 3 miesiące temu (ok. 90-100 dni temu) ---
        (90, "expense", "Transport", "Paliwo na wyjazd weekendowy", "270.00"),
        (92, "expense", "Rozrywka", "Park rozrywki / bilety", "210.00"),
        (94, "expense", "Jedzenie", "Zakupy grillowe", "165.30"),
        (96, "expense", "Mieszkanie i rachunki", "Czynsz za mieszkanie", "1850.00"),
        (98, "income", "Wynagrodzenie", "Wypłata — etat", "6200.00"),
        (100, "expense", "Inne", "Fryzjer", "80.00"),
    ]

    added_count = 0
    for days_ago, entry_type, category_name, title, amount_str in sample_entries:
        target_date = (today - timedelta(days=days_ago)).isoformat()
        cats_map = expense_cats if entry_type == "expense" else income_cats
        cat_id = cats_map.get(category_name)
        if cat_id is None:
            continue

        database.add_personal_transaction(
            title=title,
            amount_str=amount_str,
            category_id=cat_id,
            date_str=target_date,
            entry_type=entry_type,
        )
        added_count += 1

    print(f"Gotowe! Dodano {added_count} przykładowych wpisów do bazy finanse.db.")


if __name__ == "__main__":
    seed_sample_data()