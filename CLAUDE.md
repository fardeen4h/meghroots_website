# meghRoots: project guide for Claude Code

meghRoots is an e-commerce site for a small seller of Meghalaya (Shillong) products: Lakadong turmeric, pepper, cinnamon, red rice and sticky rice. Each product comes in several pack sizes. The brand is story-led (origin, farmers, Meghalaya), delivery is pan-India, and the owner is a solo seller who is new to Django. Explain what you change in plain language and keep changes small and reviewable.

## Stack

* Python and Django, PostgreSQL (Homebrew `postgresql@15` locally), Tailwind via CDN, plain Django templates (no JS framework)
* Razorpay for online payments (test mode so far) and Cash on Delivery
* Shiprocket API for live courier rates; Porter (local Kolkata delivery) is planned
* Local machine: macOS, virtualenv in `venv/`. Settings are read from `.env` with `python-decouple`
* Hosting is not chosen yet. The goal is free tiers (see the roadmap)

## Commands

```bash
source venv/bin/activate
python manage.py runserver
python manage.py check
python manage.py makemigrations <app> && python manage.py migrate
python manage.py release_unpaid_orders --minutes 30   # cancels abandoned online orders, returns stock
python manage.py check_shiprocket --pickup <PIN> --delivery <PIN> --weight 0.5 [--cod 1] [--declared 300]
```

There are no automated tests yet. Adding them is the first task on the roadmap. Run `python manage.py check` after every change.

## Layout

* `config/`: settings and root URLs (`core`, `catalog`, `cart`, `orders` are included)
* `core/`: home, about, contact pages
* `catalog/`: `Category`, `Product`, `Variant`. Price, stock, SKU, `weight_grams` and an optional `amazon_url` live on the Variant, not the product
* `cart/`: session-based cart (`cart/cart.py`, `Cart` class) plus a context processor that exposes `cart` to every template
* `orders/`: `Order`/`OrderItem` models, checkout form, views, `payments.py` (Razorpay), `shipping.py` (Shiprocket), admin, management commands
* `templates/`: `base.html`, `core/`, `catalog/`, `cart/`, `orders/`

## Domain rules (do not break these)

* Money is always `Decimal`, never float. Prices are in rupees. Only convert to paise at the Razorpay call (`to_paise`).
* The server is the source of truth for prices. The browser only displays shipping and totals. Checkout recomputes shipping on submit and refuses the order if the quoted amount no longer matches.
* Order items are snapshots (name, size label, SKU, price, quantity). Never rebuild past orders from live catalogue data.
* Stock is reserved when an order is created, inside `transaction.atomic()` using `select_for_update`. Returning stock goes through `release_stock` (guarded by `Order.stock_released`, so it is idempotent).
* Online orders: created as `pending_payment`, then `mark_paid` (in `orders/payments.py`) sets them `placed` and `paid`. `mark_paid` is idempotent and is called both from the browser callback and the webhook. Never mark an order paid from anything the browser sent without verifying the Razorpay signature.
* Razorpay amounts are fixed once payment starts. Do not change an order's total after a Razorpay order exists. The admin shipping override refuses to apply in that case.
* Customer pages for an order use an unguessable `access_token` UUID in the URL (guest checkout, no accounts).
* Shipping options are built from live Shiprocket quotes in `orders/shipping.py`: Standard is the cheapest courier, Express is the cheapest courier within a day of the fastest. The customer price is the courier cost plus an optional packaging fee, rounded up. The order value is sent as `declared_value` because courier COD charges depend on it. If Shiprocket is unreachable, a single estimated fallback rate is used so checkout never breaks.
* Free text shown to customers must be escaped. Do not use `|safe` on customer-supplied data.

## Environment variables (names only, never commit values)

`SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `SHIPROCKET_EMAIL`, `SHIPROCKET_PASSWORD`, `STORE_PICKUP_PINCODE`, `SHIPPING_PACKAGING_FEE`, `SHIPPING_ROUND_TO`, `FREE_SHIPPING_ABOVE`

`.env.example` lists the same names with placeholder values and must stay in sync when a variable is added.

## Safety rules

* Never read out, print, log or commit the contents of `.env`, API keys or passwords. If a task needs a new secret, add the variable name to `.env.example` and tell the owner to fill it in.
* Use Razorpay and Shiprocket test or sandbox credentials only. Do not place real orders, move real money or book real shipments. Ask before any command that calls a paid or live external API.
* Never edit a migration that has already been applied. Create a new one. Ask before any migration that deletes data or columns.
* Do not delete files or run destructive git commands without asking.
* Order data contains customer names, phone numbers and addresses. Do not add it to logs, fixtures or commits.
* Make a git commit after each completed step with a clear message. Do not push unless asked.

## How to work

* For anything bigger than a small fix, write a short plan first and wait for approval.
* Match the existing style: simple Django views and models, no new frameworks, no new dependencies without asking.
* After changes: run `python manage.py check` and the tests. For UI changes, say which pages the owner should open and what they should see.
* When something is ambiguous in the business rules (pricing, refunds, shipping policy), ask the owner. Do not guess.

## Roadmap, in order

1. Tests and hardening. Cover the cart, order creation and stock locking, `mark_paid` idempotency and the cancel and cleanup paths, shipping option building (use recorded Shiprocket responses, no network), and the checkout price mismatch check. Add rate limiting to the public `shipping/options/` endpoint, which triggers Shiprocket calls.
2. Order management (Phase 4). Admin actions to move orders Placed, Packed, Shipped, Delivered and Cancelled (cancel returns stock). Mark COD orders paid. Store courier, AWB and tracking URL on the order. A "book shipment" action for Shiprocket (create order, assign courier, request pickup). Customer emails (console backend in development, SMTP later). A simple dashboard of orders to process. Refund handling for paid orders that are cancelled.
3. Porter for local Kolkata delivery. A second shipping provider selected by a `LOCAL_PIN_PREFIXES` setting. It needs Porter API credentials and documentation from the owner (the quote needs pickup and drop coordinates, so decide how addresses are geocoded). Keep the option format shared with `ShippingOption` so the checkout page does not change.
4. Content and polish. Real About, Contact and brand-story pages, product copy, image sizes, and a product page "story" section.
5. Deployment on free tiers. Gunicorn and WhiteNoise, a free managed PostgreSQL, free image storage for uploaded product photos (free hosts wipe local files), `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HTTPS settings, a scheduled `release_unpaid_orders`, and Razorpay webhook registration at `/orders/razorpay/webhook/` (it needs a public https URL). Add the policy pages payment providers usually require: terms, privacy, refund and cancellation, shipping, contact. Verify current free-tier limits before choosing.

## Known limitations

* Shipping prices are estimates. Couriers can re-weigh parcels, so compare real invoices with what customers were charged.
* COD currently passes the full courier COD charge to the customer. A cap may be added later.
* The Razorpay webhook cannot be tested locally because it needs a public URL.
* Product weights must be the packed weight (including packaging) for quotes to be right.
