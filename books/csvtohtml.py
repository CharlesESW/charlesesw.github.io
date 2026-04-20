import csv
import html
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ===== CONFIG =====
INPUT_CSV = "goodreads_library_export.csv"  # your exported CSV
OUTPUT_HTML = "index.html"
PAGE_TITLE = "Charlie's Books"

# Shelves to exclude from the tag display and filter
# (these are Goodreads system shelves, not user-created genre tags)
EXCLUDE_SHELVES = {"read", "currently-reading", "to-read", "wanna-reread", "audiobooked", "kindled", "loaned", "libraried"}

# ===== HELPER FUNCTION FOR STARS =====
def rating_to_stars(rating):
    try:
        num = int(float(rating))
    except:
        num = 0
    return "★" * num + "☆" * (5 - num)

# ===== HELPER FUNCTION TO PARSE DATE READ =====
def parse_date(date_str):
    date_str = date_str.strip()
    if not date_str:
        return datetime(1900, 1, 1)
    try:
        return datetime.strptime(date_str, "%Y/%m/%d")
    except:
        return datetime(1900, 1, 1)

# ===== READ AND FILTER CSV =====
books = []
all_shelves = set()

with open(INPUT_CSV, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        exclusive_shelf = row.get("Exclusive Shelf", "").lower()
        if exclusive_shelf != "read":
            continue

        review_text = row.get("My Review", "").strip()
        if not review_text:
            continue

        title = row.get("Title", "Unknown Title")
        author = row.get("Author", "Unknown Author")
        rating = row.get("My Rating", "0")
        stars = rating_to_stars(rating)
        date_read = parse_date(row.get("Date Read", ""))

        # Parse user shelves from "Bookshelves" column
        raw_shelves = row.get("Bookshelves", "")
        shelves = [
            s.strip() for s in raw_shelves.split(",")
            if s.strip() and s.strip().lower() not in EXCLUDE_SHELVES
        ]
        for s in shelves:
            all_shelves.add(s)

        books.append({
            "title": title,
            "author": author,
            "review_text": review_text,
            "stars": stars,
            "date_read": date_read,
            "shelves": shelves,
        })

# ===== SORT =====
books.sort(key=lambda x: x["date_read"], reverse=True)
sorted_shelves = sorted(all_shelves)

# ===== GENERATE FILTER BUTTONS =====
filter_buttons = ""
for shelf in sorted_shelves:
    filter_buttons += f'        <button class="shelf-btn" data-shelf="{shelf}"><span>{shelf}</span></button>\n'

# ===== GENERATE BOOK CARDS =====
html_books = ""
for book in books:
    review_html = html.escape(book["review_text"])
    review_html = review_html.replace('&lt;br&gt;', '<br />')
    review_html = review_html.replace('&lt;br/&gt;', '<br />')
    review_html = review_html.replace('&lt;br /&gt;', '<br />')
    review_html = review_html.replace('\n', '<br /><br />')
    title_html = html.escape(book["title"])
    author_html = html.escape(book["author"])
    shelf_data = html.escape(" ".join(book["shelves"]))
    shelf_tags_html = "".join(
        f'<span class="shelf-tag">{html.escape(s)}</span>' for s in book["shelves"]
    )
    html_books += f'''
<details class="bookbox" data-shelves="{shelf_data}">
    <summary>
        <strong>{title_html}</strong> by {author_html}<br/>
        My rating: {book["stars"]}<br/>
        <span class="shelf-tags">{shelf_tags_html}</span>
    </summary>
    <div class="review">
        {review_html}
    </div>
</details>
'''

# ===== GENERATE FULL HTML =====
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{PAGE_TITLE}</title>
    <link rel="icon" type="image/x-icon" href="../../favicon.ico">
    <link rel="stylesheet" href="books.css">
</head>
<body>
    <div class="topnav">
        <a href="/">Home</a>
        <a href="/blog/">Blog</a>
        <a class="active" href="/books/">Books</a>
    </div>
    <header>
        <h1>Recent Book Reviews</h1>
    </header>
    <div class="content">
        <div class="sidebar"></div>
        <div class="main">

<div class="shelf-filter">
    <span class="shelf-filter-label">Filter by shelf:</span>
{filter_buttons}    <button id="clear-filter">clear</button>
</div>
<p id="no-results">No books match all selected shelves.</p>

{html_books}

<a href="https://www.goodreads.com/user/show/133445889-charlie">View all my books</a>
        </div>
        <div class="sidebar"></div>
    </div>

<script>
    const buttons = document.querySelectorAll('.shelf-btn');
    const books = document.querySelectorAll('.bookbox');
    const clearBtn = document.getElementById('clear-filter');
    const noResults = document.getElementById('no-results');
    let activeFilters = new Set();

    function applyFilters() {{
        let visibleCount = 0;
        books.forEach(book => {{
            if (activeFilters.size === 0) {{
                book.classList.remove('hidden');
                visibleCount++;
                return;
            }}
            // AND logic: book must have ALL active shelves
            const bookShelves = book.dataset.shelves.split(' ');
            const matchesAll = [...activeFilters].every(f => bookShelves.includes(f));
            if (matchesAll) {{
                book.classList.remove('hidden');
                visibleCount++;
            }} else {{
                book.classList.add('hidden');
            }}
        }});
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        clearBtn.classList.toggle('visible', activeFilters.size > 0);
    }}

    buttons.forEach(btn => {{
        btn.addEventListener('click', () => {{
            const shelf = btn.dataset.shelf;
            if (activeFilters.has(shelf)) {{
                activeFilters.delete(shelf);
                btn.classList.remove('active');
            }} else {{
                activeFilters.add(shelf);
                btn.classList.add('active');
            }}
            applyFilters();
        }});
    }});

    clearBtn.addEventListener('click', () => {{
        activeFilters.clear();
        buttons.forEach(b => b.classList.remove('active'));
        applyFilters();
    }});
</script>
</body>
</html>
"""

project_root = Path(__file__).resolve().parents[1]
output_path = Path(__file__).resolve().parent / OUTPUT_HTML
prettier_config = project_root / ".prettierrc"


def run_prettier(cmd):
    subprocess.run(cmd, check=True, cwd=project_root)

# ===== SAVE HTML =====
# Write with LF to align with .prettierrc endOfLine setting.
with open(OUTPUT_HTML, "w", encoding="utf-8", newline="\n") as f:
    f.write(html)

# If prettier is available, format the generated HTML using the repo config.
try:
    prettier_exe = shutil.which("prettier")
    npx_exe = shutil.which("npx")

    if prettier_exe:
        run_prettier([
            prettier_exe,
            "--config",
            str(prettier_config),
            "--write",
            str(output_path),
        ])
    elif npx_exe:
        run_prettier([
            npx_exe,
            "--yes",
            "prettier",
            "--config",
            str(prettier_config),
            "--write",
            str(output_path),
        ])
    else:
        print("Prettier not found in PATH; skipped formatting step.")
except (FileNotFoundError, subprocess.CalledProcessError) as exc:
    print(f"Prettier formatting failed ({exc}); output HTML was still generated.")

print(f"HTML page generated successfully: {OUTPUT_HTML}")