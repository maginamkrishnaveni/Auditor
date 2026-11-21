# Voice Auditor

Offline-capable book distribution audit tool. Runs on a laptop at the
distribution venue; volunteers use their phones over the local WiFi to log
every book handed out and every donation — no internet required.

## What it tracks (per transaction)
- Book (from a fixed catalogue with fixed prices) + language
- Person name, mobile
- Amount paid
- Donations (no book) — also go to the temple

Live dashboard shows running totals: **books given**, **money collected**,
and **temple amount due** (= all collected). End-of-session report + one-click
Excel export for the temple.

## Setup (one time)

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py load_books          # loads the fixed catalogue + prices
# optional: python manage.py createsuperuser   # for the /admin/ setup page
```

## Run during a distribution event

On the laptop at the venue:

```powershell
python manage.py runserver 0.0.0.0:8000
```

`0.0.0.0` lets other devices on the same WiFi reach the laptop. Find the
laptop's LAN IP with `ipconfig` (look for the IPv4 Address on the WiFi/ethernet
adapter). Volunteers then open on their phone:

```
http://<laptop-ip>:8000
```

No internet is needed — Django, Bootstrap, and HTMX are all served from the
laptop.

## How to use
1. Open the site on a phone → pick/create your volunteer name.
2. **New Session** → name it (date prefilled) → opens the dashboard.
3. **Add Book**: choose book → language auto-loads with its price → amount
   auto-fills (editable) → enter name/mobile → save. Returns to dashboard.
4. **Donation**: enter amount (name/mobile optional) → save.
5. Watch the live totals update every few seconds across all volunteers.
6. At the end: **End Session**, then **Report** → **Export Excel** to hand to
   the temple.

## Notes
- Prices come from the fixed catalogue (see `load_books` command). Wrong prices
  cannot be entered by hand for priced books.
- `Chaithanya Charithamrutham` shows "price pending" until a fixed price is set
  — the volunteer types the amount for those. Update the price in `load_books`
  or via `/admin/` once decided.
- All money collected (book sales + donations) is the temple amount due.
