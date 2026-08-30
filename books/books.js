const searchInput = document.querySelector("#book-search");
const sortSelect = document.querySelector("#book-sort");
const shelfButtons = document.querySelector("#shelf-buttons");
const clearButton = document.querySelector("#clear-filter");
const resultCount = document.querySelector("#result-count");
const noResults = document.querySelector("#no-results");
const bookList = document.querySelector("#book-list");
const shelfFilter = document.querySelector("#shelf-filter");

const SEARCH_DELAY_MS = 180;
let searchTimer;

const state = {
  books: [],
  search: "",
  sort: "newest",
  shelves: new Set(),
};

function normalise(value) {
  return value.toLocaleLowerCase().trim();
}

function starsFor(rating) {
  return rating > 0 ? `${"★".repeat(rating)}${"☆".repeat(5 - rating)}` : "Unrated";
}

function formatDate(dateRead) {
  if (!dateRead) return "Date not recorded";
  return `Read ${new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${dateRead}T00:00:00Z`))}`;
}

function bookAnchor(book) {
  return book.id ? `book-${book.id}` : "";
}

function shelfLink(shelf) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("shelf", shelf);
  return url.toString();
}

async function copyReviewLink(book, button) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = bookAnchor(book);

  try {
    await navigator.clipboard.writeText(url.toString());
    button.textContent = "Copied!";
  } catch {
    button.textContent = "Copy failed";
  }

  window.setTimeout(() => {
    button.textContent = "Copy link";
  }, 1800);
}

function createBookCard(book) {
  const card = document.createElement("details");
  card.className = "bookbox";
  card.id = bookAnchor(book);

  const summary = document.createElement("summary");
  const heading = document.createElement("strong");
  heading.textContent = book.title;
  summary.append(heading, document.createTextNode(` by ${book.author}`));

  const metadata = document.createElement("span");
  metadata.className = "book-metadata";
  metadata.textContent = `${starsFor(book.rating)} · ${formatDate(book.dateRead)}`;
  summary.append(metadata);

  const tags = document.createElement("span");
  tags.className = "shelf-tags";
  for (const shelf of book.shelves) {
    const tag = document.createElement("a");
    tag.className = "shelf-tag";
    tag.textContent = shelf;
    tag.href = shelfLink(shelf);
    tag.title = `Filter by ${shelf}`;
    tag.addEventListener("click", (event) => {
      event.stopPropagation();
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      state.shelves.add(shelf);
      renderBooks();
      shelfFilter.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    tags.append(tag);
  }
  summary.append(tags);

  const review = document.createElement("div");
  review.className = "review";
  review.textContent = book.review.replace(/<br\s*\/?\s*>/gi, "\n");

  const reviewActions = document.createElement("div");
  reviewActions.className = "review-actions";
  const copyLink = document.createElement("button");
  copyLink.type = "button";
  copyLink.className = "copy-link";
  copyLink.textContent = "Copy link";
  copyLink.addEventListener("click", () => copyReviewLink(book, copyLink));
  reviewActions.append(copyLink);

  card.append(summary, review, reviewActions);
  return card;
}

function compareDates(first, second, direction) {
  if (!first.dateRead && !second.dateRead) return 0;
  if (!first.dateRead) return 1;
  if (!second.dateRead) return -1;
  return direction * first.dateRead.localeCompare(second.dateRead);
}

function sortedBooks(books) {
  const sorted = [...books];
  const textSort = (field) => (first, second) =>
    first[field].localeCompare(second[field], undefined, { sensitivity: "base" });
  const comparators = {
    newest: (first, second) => compareDates(first, second, -1),
    oldest: (first, second) => compareDates(first, second, 1),
    rating: (first, second) => second.rating - first.rating || compareDates(first, second, -1),
    title: textSort("title"),
    author: textSort("authorSort"),
  };
  return sorted.sort(comparators[state.sort]);
}

function visibleBooks() {
  const query = normalise(state.search);
  return sortedBooks(
    state.books.filter((book) => {
      const matchesSearch =
        !query || normalise(book.title).includes(query) || normalise(book.author).includes(query);
      const matchesShelves = [...state.shelves].every((shelf) => book.shelves.includes(shelf));
      return matchesSearch && matchesShelves;
    }),
  );
}

function updateUrl() {
  const url = new URL(window.location.href);
  url.search = "";
  if (state.search) url.searchParams.set("q", state.search);
  if (state.sort !== "newest") url.searchParams.set("sort", state.sort);
  for (const shelf of [...state.shelves].sort()) url.searchParams.append("shelf", shelf);
  history.replaceState(null, "", url);
}

function renderBooks({ updateLocation = true } = {}) {
  const visible = visibleBooks();
  const fragment = document.createDocumentFragment();
  for (const book of visible) fragment.append(createBookCard(book));
  bookList.replaceChildren(fragment);

  const total = state.books.length;
  resultCount.textContent = `Showing ${visible.length} of ${total} ${total === 1 ? "review" : "reviews"}.`;
  noResults.hidden = visible.length !== 0;
  clearButton.classList.toggle("visible", state.shelves.size > 0 || Boolean(state.search));

  for (const button of shelfButtons.querySelectorAll(".shelf-btn")) {
    const active = state.shelves.has(button.dataset.shelf);
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  }

  if (updateLocation) updateUrl();
}

function createShelfFilters() {
  const shelves = [...new Set(state.books.flatMap((book) => book.shelves))].sort((first, second) =>
    first.localeCompare(second, undefined, { sensitivity: "base" }),
  );
  const fragment = document.createDocumentFragment();

  for (const shelf of shelves) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "shelf-btn";
    button.dataset.shelf = shelf;
    button.setAttribute("aria-pressed", "false");
    const label = document.createElement("span");
    label.textContent = shelf;
    button.append(label);
    button.addEventListener("click", () => {
      if (state.shelves.has(shelf)) state.shelves.delete(shelf);
      else state.shelves.add(shelf);
      renderBooks();
    });
    fragment.append(button);
  }

  shelfButtons.replaceChildren(fragment);
}

function loadStateFromUrl() {
  const parameters = new URLSearchParams(window.location.search);
  state.search = parameters.get("q") || "";
  const requestedSort = parameters.get("sort");
  state.sort = ["newest", "oldest", "rating", "title", "author"].includes(requestedSort)
    ? requestedSort
    : "newest";

  const validShelves = new Set(state.books.flatMap((book) => book.shelves));
  state.shelves = new Set(parameters.getAll("shelf").filter((shelf) => validShelves.has(shelf)));
  searchInput.value = state.search;
  sortSelect.value = state.sort;
}

function openLinkedBook() {
  if (!window.location.hash) return;
  const linkedBook = document.getElementById(decodeURIComponent(window.location.hash.slice(1)));
  if (linkedBook instanceof HTMLDetailsElement) {
    linkedBook.open = true;
    linkedBook.scrollIntoView({ block: "start" });
  }
}

searchInput.addEventListener("input", () => {
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(() => {
    state.search = searchInput.value;
    renderBooks();
  }, SEARCH_DELAY_MS);
});

sortSelect.addEventListener("change", () => {
  state.sort = sortSelect.value;
  renderBooks();
});

clearButton.addEventListener("click", () => {
  window.clearTimeout(searchTimer);
  state.search = "";
  state.shelves.clear();
  searchInput.value = "";
  renderBooks();
  searchInput.focus();
});

window.addEventListener("hashchange", openLinkedBook);

fetch("books.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    return response.json();
  })
  .then((books) => {
    state.books = books;
    loadStateFromUrl();
    createShelfFilters();
    renderBooks({ updateLocation: false });
    openLinkedBook();
  })
  .catch((error) => {
    console.error("Unable to load book reviews", error);
    resultCount.textContent = "The book reviews could not be loaded.";
  });
