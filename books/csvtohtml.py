import csv
import json
from datetime import datetime
from pathlib import Path


INPUT_CSV = "goodreads_library_export.csv"
OUTPUT_JSON = "books.json"

EXCLUDE_SHELVES = {
    "read",
    "currently-reading",
    "to-read",
    "wanna-reread",
    "audiobooked",
    "kindled",
    "loaned",
    "libraried",
}


def parse_rating(value):
    try:
        rating = int(float(value))
    except (TypeError, ValueError):
        return 0
    return rating if 1 <= rating <= 5 else 0


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y/%m/%d").date()
    except ValueError:
        return None


def parse_shelves(value):
    shelves = {
        shelf.strip()
        for shelf in (value or "").split(",")
        if shelf.strip() and shelf.strip().lower() not in EXCLUDE_SHELVES
    }
    return sorted(shelves, key=str.casefold)


def load_books(input_path):
    books = []

    with input_path.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if row.get("Exclusive Shelf", "").strip().lower() != "read":
                continue

            review = row.get("My Review", "").strip()
            if not review:
                continue

            date_read = parse_date(row.get("Date Read"))
            books.append(
                {
                    "id": row.get("Book Id", "").strip(),
                    "title": row.get("Title", "").strip() or "Unknown Title",
                    "author": row.get("Author", "").strip() or "Unknown Author",
                    "authorSort": row.get("Author l-f", "").strip()
                    or row.get("Author", "").strip()
                    or "Unknown Author",
                    "rating": parse_rating(row.get("My Rating")),
                    "dateRead": date_read.isoformat() if date_read else None,
                    "shelves": parse_shelves(row.get("Bookshelves")),
                    "review": review,
                }
            )

    # Dated books appear newest first. Entries without a Date Read stay at the
    # end while retaining their order from the Goodreads export.
    books.sort(key=lambda book: book["dateRead"] or "", reverse=True)
    return books


def main():
    books_directory = Path(__file__).resolve().parent
    input_path = books_directory / INPUT_CSV
    output_path = books_directory / OUTPUT_JSON

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Goodreads export not found: {input_path}\n"
            "Place the CSV beside this script and run it again."
        )

    books = load_books(input_path)
    with output_path.open("w", encoding="utf-8", newline="\n") as json_file:
        json.dump(books, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")

    print(f"Generated {output_path.name} with {len(books)} reviewed books.")


if __name__ == "__main__":
    main()
