import csv
from datetime import datetime

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
    review_html = book["review_text"].replace('\n', '<br /><br />')
    shelf_data = " ".join(book["shelves"])
    shelf_tags_html = "".join(
        f'<span class="shelf-tag">{s}</span>' for s in book["shelves"]
    )
    html_books += f'''
<details class="bookbox" data-shelves="{shelf_data}">
    <summary>
        <strong>{book["title"]}</strong> by {book["author"]}<br/>
        My rating: {book["stars"]}<br/>
        {shelf_tags_html}
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
    <link rel="stylesheet" href="../blog/blogstyles.css">
    <style>
        .bookbox summary {{
            cursor: pointer;
            list-style: none;
        }}
        .bookbox summary::-webkit-details-marker {{
            display: none;
        }}
        .bookbox summary::after {{
            content: "▸ read review";
            display: block;
            font-size: 1em;
            opacity: 1;
        }}
        .bookbox[open] summary::after {{
            content: "▾ hide review";
        }}
        .bookbox .review {{
            margin-top: 0.75em;
        }}

        /* Shelf filter bar */
        .shelf-filter {{
            margin-bottom: 1.5em;
            display: flex;
            flex-wrap: wrap;
            gap: 0.4em;
            align-items: center;
        }}
        .shelf-filter-label {{
            font-size: 0.85em;
            opacity: 1;
            margin-right: 0.3em;
        }}
        .shelf-btn {{
            padding: 0.2em 0.7em;
            font-size: 0.8em;
            border: 1px solid currentColor;
            background: transparent;
            cursor: pointer;
            border-radius: 2em;
            font-family: inherit;
            color: inherit;
            transition: background 0.15s, color 0.15s;
        }}
        .shelf-btn:hover {{
            background: rgba(0,0,0,0.08);
        }}
        .shelf-btn.active {{
            background: currentColor;
        }}
        .shelf-btn.active span {{
            color: white;
        }}
        #clear-filter {{
            padding: 0.2em 0.7em;
            font-size: 0.8em;
            border: none;
            background: transparent;
            cursor: pointer;
            font-family: inherit;
            text-decoration: underline;
            display: none;
        }}
        #clear-filter.visible {{
            display: inline;
        }}

        /* Shelf tags on each book */
        .shelf-tag {{
            display: inline-block;
            font-size: 0.75em;
            padding: 0.1em 0.55em;
            border: 1px solid currentColor;
            border-radius: 2em;
            margin: 0.2em 0.2em 0 0;
        }}

        /* Hidden books */
        .bookbox.hidden {{
            display: none;
        }}

        #no-results {{
            display: none;
            opacity: 0.6;
            font-style: italic;
            margin: 1em 0;
        }}
    </style>
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

# ===== SAVE HTML =====
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML page generated successfully: {OUTPUT_HTML}")