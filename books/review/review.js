const statusMessage = document.querySelector("#review-status");
const reviewDetail = document.querySelector("#review-detail");
const reviewTitle = document.querySelector("#review-title");
const reviewAuthor = document.querySelector("#review-author");
const reviewMetadata = document.querySelector("#review-metadata");
const reviewShelves = document.querySelector("#review-shelves");
const reviewText = document.querySelector("#review-text");
const copyLink = document.querySelector("#copy-review-link");

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

function shelfLink(shelf) {
  const url = new URL("../", window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("shelf", shelf);
  return url.toString();
}

function canonicalReviewLink(bookId) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("id", bookId);
  return url.toString();
}

function showError(message) {
  statusMessage.textContent = message;
  reviewDetail.hidden = true;
}

function renderReview(book) {
  document.title = `${book.title} by ${book.author} | Charlie's Books`;
  reviewTitle.textContent = book.title;
  reviewAuthor.textContent = `by ${book.author}`;
  reviewMetadata.textContent = `${starsFor(book.rating)} · ${formatDate(book.dateRead)}`;
  reviewText.textContent = book.review.replace(/<br\s*\/?\s*>/gi, "\n");
  const shelfFragment = document.createDocumentFragment();
  for (const shelf of book.shelves) {
    const tag = document.createElement("a");
    tag.className = "shelf-tag";
    tag.href = shelfLink(shelf);
    tag.textContent = shelf;
    tag.title = `View books on the ${shelf} shelf`;
    shelfFragment.append(tag);
  }
  reviewShelves.replaceChildren(shelfFragment);

  copyLink.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(canonicalReviewLink(book.id));
      copyLink.textContent = "Copied!";
    } catch {
      copyLink.textContent = "Copy failed";
    }
    window.setTimeout(() => {
      copyLink.textContent = "Copy link";
    }, 1800);
  });

  statusMessage.hidden = true;
  reviewDetail.hidden = false;
}

const bookId = new URLSearchParams(window.location.search).get("id");

if (!bookId) {
  showError("No book was specified. Choose a review from the Books page.");
} else {
  fetch("../books.json")
    .then((response) => {
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      return response.json();
    })
    .then((books) => {
      const book = books.find((candidate) => String(candidate.id) === bookId);
      if (!book) {
        showError("That book review could not be found.");
        return;
      }
      renderReview(book);
    })
    .catch((error) => {
      console.error("Unable to load book review", error);
      showError("The book review could not be loaded.");
    });
}
