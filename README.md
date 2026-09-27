# LinkNest

A link-shortening tool built for one specific problem: **college WhatsApp groups are where useful links go to die.** Notes, PYQ drive folders, feedback forms, group signup sheets — shared once, scrolled past, never found again.

LinkNest turns any long link into a short, memorable one (`linknest.xyz/dbms-notes`), with a QR code for posters/noticeboards, a click counter so you know if anyone actually opened it, and automatic 30-day expiry so old links don't pile up forever.

## Inspiration

This project is inspired by the **"Build your own URL Shortener"** category from [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) — but built around a specific real use case (campus resource sharing) rather than a generic shortener, with expiry, analytics, and QR generation layered on top.

## Features

- **Shorten any URL**, with an optional custom short code (`/dbms-notes` instead of a random string)
- **Auto-expiry** — every link expires 30 days after creation, keeping the dashboard from turning into dead-link clutter
- **Click tracking** — every link has a live open-count, so you know if people actually used it
- **QR code generation** — every short link gets an auto-generated QR code, useful for noticeboards/posters
- Clean dashboard showing all active links, total opens, and expired-link count

## Tech stack

- **Backend:** Python, Flask
- **Database:** SQLite (zero setup, single file)
- **QR codes:** `qrcode` + Pillow
- **Frontend:** server-rendered HTML/CSS (no JS framework — kept deliberately simple)

## Running it locally

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd linknest

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run it
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Project structure

```
linknest/
├── app.py                 # Flask app: routes, DB logic, QR generation
├── requirements.txt
├── templates/
│   ├── index.html          # dashboard + create-link form
│   └── 404.html            # shown for expired/missing links
└── static/
    └── style.css
```

## Possible extensions

- User accounts, so each student's links are private to them
- Per-link analytics over time (not just a total count)
- A browser extension / WhatsApp bot for one-tap shortening
- Bulk import from a shared Google Sheet

## Note on AI usage

Claude was used to help write and debug the Flask application code (the "build" itself). The project report and pitch deck were written independently, as required by the challenge guidelines.
