from decimal import Decimal

from django.core.management.base import BaseCommand

from audit.models import Book, BookPrice

# Fixed distribution catalogue. Price varies by language for the big sets;
# smaller books have one flat "Any" price. A price of None means "not decided
# yet" — the volunteer enters the amount manually for that book.
BOOK_DATA = [
    ("Srimad Bhagavatham", [("Telugu", 7500), ("English", 10000), ("Hindi", 8000)]),
    ("Chaithanya Charithamrutham", [("Telugu", None), ("English", None), ("Hindi", None)]),
    ("Bhagavadgita", [("Any", 350)]),
    ("Ramayan", [("Any", 300)]),
    ("Krishna", [("Any", 350)]),
    ("Science of Self Realization", [("Any", 200)]),
    ("Small Books (Any book)", [("Any", 50)]),
]


class Command(BaseCommand):
    help = "Load the fixed book master with per-language prices."

    def handle(self, *args, **options):
        books_created = 0
        prices_created = 0
        prices_updated = 0
        for name, langs in BOOK_DATA:
            book, created = Book.objects.get_or_create(name=name)
            if created:
                books_created += 1
            for lang, price in langs:
                new_price = Decimal(price) if price is not None else None
                bp, c = BookPrice.objects.get_or_create(
                    book=book, language=lang, defaults={'price': new_price})
                if c:
                    prices_created += 1
                elif bp.price != new_price:
                    bp.price = new_price
                    bp.save()
                    prices_updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Done. Books created: {books_created} | "
            f"prices created: {prices_created} | prices updated: {prices_updated}"
        ))
