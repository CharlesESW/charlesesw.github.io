import html
import json
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


SITE_URL = "https://charliew.net"


def load_posts(metadata_path, blog_directory):
    with metadata_path.open(encoding="utf-8") as metadata_file:
        posts = json.load(metadata_file)

    required_fields = {"slug", "title", "published", "description"}
    seen_slugs = set()

    for post in posts:
        missing_fields = required_fields - post.keys()
        if missing_fields:
            raise ValueError(f"Post is missing fields: {', '.join(sorted(missing_fields))}")
        if post["slug"] in seen_slugs:
            raise ValueError(f"Duplicate post slug: {post['slug']}")
        if not (blog_directory / post["slug"] / "index.html").is_file():
            raise FileNotFoundError(f"No article page found for post: {post['slug']}")

        published = datetime.fromisoformat(post["published"])
        if published.tzinfo is None:
            raise ValueError(f"Post timestamp needs a timezone: {post['slug']}")
        post["published_datetime"] = published
        seen_slugs.add(post["slug"])

    if not posts:
        raise ValueError("At least one blog post is required")

    return sorted(posts, key=lambda post: post["published_datetime"], reverse=True)


def generate_index(posts):
    post_items = "\n".join(
        "          <li>\n"
        f'            <time datetime="{post["published_datetime"].date().isoformat()}">'
        f'{post["published_datetime"].strftime("%d/%m/%Y")}</time>\n'
        f'            <a href="/blog/{html.escape(post["slug"], quote=True)}/">'
        f'{html.escape(post["title"])}</a>\n'
        "          </li>"
        for post in posts
    )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Charlie's Blog</title>
    <link rel="icon" type="image/x-icon" href="../favicon.ico" />
    <link rel="stylesheet" href="blogstyles.css" />
    <link rel="alternate" type="application/rss+xml" title="Charlie's Blog RSS" href="/RSS.xml" />
  </head>
  <body>
    <nav class="topnav" aria-label="Primary navigation">
      <a href="/">Home</a>
      <a class="active" href="/blog/" aria-current="page">Blog</a>
      <a href="/books/">Books</a>
    </nav>
    <header>
      <h1>Blog</h1>
      <p><a href="/RSS.xml">Subscribe to my RSS feed</a></p>
    </header>
    <main class="content">
      <div class="sidebar"></div>
      <div class="main">
        <ul class="post-list">
{post_items}
        </ul>
      </div>
      <div class="sidebar"></div>
    </main>
  </body>
</html>
'''


def generate_rss(posts):
    items = "\n".join(
        "    <item>\n"
        f"      <title>{xml_escape(post['title'])}</title>\n"
        f"      <link>{SITE_URL}/blog/{xml_escape(post['slug'])}/</link>\n"
        f'      <guid isPermaLink="true">{SITE_URL}/blog/{xml_escape(post["slug"])}/</guid>\n'
        f"      <pubDate>{format_datetime(post['published_datetime'], usegmt=True)}</pubDate>\n"
        f"      <description>{xml_escape(post['description'])}</description>\n"
        "    </item>"
        for post in posts
    )
    last_build_date = format_datetime(posts[0]["published_datetime"], usegmt=True)

    return f'''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Charlie's Blog</title>
    <link>{SITE_URL}/blog/</link>
    <atom:link href="{SITE_URL}/RSS.xml" rel="self" type="application/rss+xml" />
    <description>Updates on my life, computers and books.</description>
    <language>en-gb</language>
    <lastBuildDate>{last_build_date}</lastBuildDate>
{items}
  </channel>
</rss>
'''


def main():
    blog_directory = Path(__file__).resolve().parent
    project_root = blog_directory.parent
    posts = load_posts(blog_directory / "posts.json", blog_directory)

    (blog_directory / "index.html").write_text(generate_index(posts), encoding="utf-8", newline="\n")
    (project_root / "RSS.xml").write_text(generate_rss(posts), encoding="utf-8", newline="\n")
    print(f"Generated blog index and RSS feed for {len(posts)} posts.")


if __name__ == "__main__":
    main()
