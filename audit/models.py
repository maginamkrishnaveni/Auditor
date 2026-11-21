import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


LANGUAGE_CHOICES = [
    ('Telugu', 'Telugu'),
    ('English', 'English'),
    ('Hindi', 'Hindi'),
    ('Any', 'Any'),
]


class Book(models.Model):
    """A title in the fixed distribution catalogue."""
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BookPrice(models.Model):
    """Price of a book for a given language.

    A book sold in multiple languages at different prices (e.g. Srimad
    Bhagavatham) has one row per language. A book with a single flat price
    regardless of language has one row with language='Any'.

    price may be NULL when the price is not decided yet; in that case the
    volunteer enters the amount manually for that book.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='prices')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Leave blank if price not decided yet; volunteer enters amount manually.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'language')
        ordering = ['book__name', 'language']

    def __str__(self):
        price_str = f"₹{self.price}" if self.price is not None else "price pending"
        return f"{self.book.name} ({self.language}) — {price_str}"


class Volunteer(models.Model):
    """Someone handing out books during a session."""
    name = models.CharField(max_length=100, unique=True)
    pin = models.CharField(max_length=20, blank=True, help_text="Optional simple PIN.")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Session(models.Model):
    """One distribution event. Many volunteers can log transactions to it."""
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.date})"

    def total_books(self):
        """Total number of books handed out (sum of quantities)."""
        agg = self.transactions.filter(type=Transaction.BOOK).aggregate(t=models.Sum('quantity'))
        return agg['t'] or 0

    def book_sale_total(self):
        """Money from book sales only."""
        agg = self.transactions.filter(type=Transaction.BOOK).aggregate(t=models.Sum('amount_paid'))
        return agg['t'] or Decimal('0')

    def donation_total(self):
        """Money from pure donations."""
        agg = self.transactions.filter(type=Transaction.DONATION).aggregate(t=models.Sum('amount_paid'))
        return agg['t'] or Decimal('0')

    def total_collected(self):
        """All money collected this session (books + donations)."""
        agg = self.transactions.aggregate(t=models.Sum('amount_paid'))
        return agg['t'] or Decimal('0')

    def temple_amount(self):
        """Amount to hand over to the temple = everything collected."""
        return self.total_collected()

    def book_count(self):
        return self.transactions.filter(type=Transaction.BOOK).count()

    def transaction_count(self):
        return self.transactions.count()


class Transaction(models.Model):
    """One record: a book handed out, or a donation received."""
    BOOK = 'BOOK'
    DONATION = 'DONATION'
    TYPE_CHOICES = [(BOOK, 'Book Sale'), (DONATION, 'Donation')]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='transactions')
    volunteer = models.ForeignKey(Volunteer, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=BOOK)

    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    book_price = models.ForeignKey(BookPrice, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="The specific price row used for this sale.")
    language = models.CharField(max_length=20, blank=True)

    person_name = models.CharField(max_length=200, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.CharField(max_length=300, blank=True)

    # For future offline PWA sync: dedupe by client-generated UUID.
    client_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.type == self.DONATION:
            return f"Donation ₹{self.amount_paid} — {self.person_name or 'anonymous'}"
        book = self.book.name if self.book else 'Unknown'
        return f"{self.quantity}× {book} ({self.language}) — {self.person_name or 'anonymous'}"

    def expected_amount(self):
        """What they should have paid for the books, or None if price is pending."""
        if self.book_price and self.book_price.price is not None:
            return self.book_price.price * self.quantity
        return None
