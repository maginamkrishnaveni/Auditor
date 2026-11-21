import functools
from io import BytesIO

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

import openpyxl
from openpyxl.styles import Font, PatternFill

from .models import Book, BookPrice, Session, Volunteer, Transaction
from .forms import VolunteerForm, SessionForm, BookTransactionForm, DonationForm

VOL_SESSION_KEY = 'volunteer_id'

# Languages offered for flat-priced ("Any") books so the actual language given
# is still recorded even though the price is the same.
SPOKEN_LANGS = ['Telugu', 'English', 'Hindi']


def get_volunteer(request):
    vid = request.session.get(VOL_SESSION_KEY)
    if vid:
        try:
            return Volunteer.objects.get(pk=vid, active=True)
        except Volunteer.DoesNotExist:
            request.session.pop(VOL_SESSION_KEY, None)
    return None


def volunteer_required(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not get_volunteer(request):
            messages.info(request, "Please select a volunteer to continue.")
            return redirect('volunteer_select')
        return view(request, *args, **kwargs)
    return wrapper


def home(request):
    volunteer = get_volunteer(request)
    if not volunteer:
        return redirect('volunteer_select')
    active_sessions = Session.objects.filter(is_active=True)
    recent_sessions = Session.objects.all()[:10]
    return render(request, 'audit/home.html', {
        'volunteer': volunteer,
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions,
    })


@require_http_methods(["GET", "POST"])
def volunteer_select(request):
    if request.method == 'POST':
        form = VolunteerForm(request.POST)
        if form.is_valid():
            vol = form.cleaned_data.get('volunteer')
            new_name = (form.cleaned_data.get('new_name') or '').strip()
            if new_name and not vol:
                vol, _ = Volunteer.objects.get_or_create(name=new_name)
            if vol:
                request.session[VOL_SESSION_KEY] = vol.id
                messages.success(request, f"Welcome, {vol.name}!")
                return redirect('home')
            messages.error(request, "Pick an existing volunteer or type a new name.")
        else:
            messages.error(request, "Invalid selection, try again.")
    else:
        form = VolunteerForm()
    return render(request, 'audit/volunteer_select.html', {'form': form})


def volunteer_change(request):
    request.session.pop(VOL_SESSION_KEY, None)
    return redirect('volunteer_select')


@require_http_methods(["GET", "POST"])
@volunteer_required
def session_create(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(request, f"Session '{session.name}' created.")
            return redirect('dashboard', session_id=session.id)
    else:
        now = timezone.now()
        form = SessionForm(initial={'name': now.strftime('%d %b %Y') + ' Distribution',
                                     'date': now.date()})
    return render(request, 'audit/session_form.html', {'form': form, 'title': 'New Session'})


@volunteer_required
def dashboard(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    recent = session.transactions.select_related('book', 'volunteer', 'book_price').all()[:10]
    return render(request, 'audit/dashboard.html', {
        'session': session,
        'volunteer': get_volunteer(request),
        'recent': recent,
    })


@require_http_methods(["GET", "POST"])
@volunteer_required
def add_book(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    volunteer = get_volunteer(request)

    if request.method == 'POST':
        form = BookTransactionForm(request.POST, session=session)
        if form.is_valid():
            book = form.cleaned_data['book']
            language = form.cleaned_data['language'] or 'Any'
            quantity = form.cleaned_data['quantity']
            amount = form.cleaned_data['amount_paid']

            # Resolve the price row: exact language match, else the 'Any' flat row.
            book_price = None
            try:
                book_price = BookPrice.objects.get(book=book, language=language)
            except BookPrice.DoesNotExist:
                try:
                    book_price = BookPrice.objects.get(book=book, language='Any')
                except BookPrice.DoesNotExist:
                    book_price = None

            if book_price is None:
                form.add_error('book', "No price is configured for this book.")
            else:
                Transaction.objects.create(
                    session=session, volunteer=volunteer, type=Transaction.BOOK,
                    book=book, book_price=book_price, language=language,
                    person_name=form.cleaned_data['person_name'],
                    mobile=form.cleaned_data['mobile'],
                    quantity=quantity, amount_paid=amount,
                    notes=form.cleaned_data.get('notes', ''),
                )
                lang_show = '' if language == 'Any' else f' ({language})'
                messages.success(request, f"Saved: {quantity}× {book.name}{lang_show} — ₹{amount}")
                return redirect('dashboard', session_id=session.id)
    else:
        form = BookTransactionForm(session=session)
    return render(request, 'audit/add_book.html', {
        'form': form, 'session': session, 'volunteer': volunteer,
    })


def book_options(request, session_id):
    """HTMX endpoint: returns the language dropdown + prices for a chosen book."""
    book_id = request.GET.get('book')
    if not book_id:
        return HttpResponse('')
    book = get_object_or_404(Book, pk=book_id)
    prices = list(BookPrice.objects.filter(book=book))
    any_row = next((bp for bp in prices if bp.language == 'Any'), None)
    specific = [bp for bp in prices if bp.language != 'Any']

    # Build (language, price) rows to show.
    if specific:
        rows = [(bp.language, bp.price) for bp in specific]
    elif any_row:
        # Flat-priced book: still let the volunteer record the real language given.
        rows = [(lang, any_row.price) for lang in SPOKEN_LANGS]
        rows.append(('Any', any_row.price))
    else:
        rows = []

    options = ['<option value="" selected>— choose language —</option>']
    for lang, price in rows:
        price_attr = '' if price is None else str(price)
        if price is None:
            label = f"{lang} — price pending (enter amount)"
        else:
            label = f"{lang} — ₹{price}"
        options.append(f'<option value="{lang}" data-price="{price_attr}">{label}</option>')

    html = (
        '<label class="form-label fs-5" for="id_language">Language</label>'
        '<select name="language" id="id_language" class="form-select form-select-lg" '
        'onchange="updateAmount()">'
        + ''.join(options) +
        '</select>'
    )
    return HttpResponse(html)


@require_http_methods(["GET", "POST"])
@volunteer_required
def add_donation(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    volunteer = get_volunteer(request)

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            Transaction.objects.create(
                session=session, volunteer=volunteer, type=Transaction.DONATION,
                person_name=form.cleaned_data['person_name'],
                mobile=form.cleaned_data['mobile'],
                quantity=1, amount_paid=form.cleaned_data['amount'],
                notes=form.cleaned_data.get('notes', ''),
            )
            messages.success(request, f"Donation recorded: ₹{form.cleaned_data['amount']}")
            return redirect('dashboard', session_id=session.id)
    else:
        form = DonationForm()
    return render(request, 'audit/add_donation.html', {
        'form': form, 'session': session, 'volunteer': volunteer,
    })


@require_POST
@volunteer_required
def end_session(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    session.is_active = False
    session.closed_at = timezone.now()
    session.save()
    messages.success(request, f"Session '{session.name}' ended.")
    return redirect('report', session_id=session.id)


@volunteer_required
def report(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    transactions = session.transactions.select_related('book', 'volunteer', 'book_price').all()
    return render(request, 'audit/report.html', {'session': session, 'transactions': transactions})


@volunteer_required
def export_excel(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"
    headers = ['#', 'Time', 'Type', 'Book', 'Language', 'Person', 'Mobile',
               'Qty', 'Amount Paid', 'Expected', 'Volunteer', 'Notes']
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill(start_color="FFE8A0", end_color="FFE8A0", fill_type="solid")

    for i, t in enumerate(session.transactions.select_related('book', 'volunteer', 'book_price').all(), 1):
        expected = ''
        exp = t.expected_amount()
        if exp is not None:
            expected = float(exp)
        ws.append([
            i,
            timezone.localtime(t.created_at).strftime('%d %b %Y %H:%M'),
            t.get_type_display(),
            t.book.name if t.book else '',
            t.language,
            t.person_name,
            t.mobile,
            t.quantity,
            float(t.amount_paid),
            expected,
            t.volunteer.name if t.volunteer else '',
            t.notes,
        ])

    # Totals row.
    ws.append([])
    total_row = ['TOTAL', '', '', '', '', '', '',
                 session.total_books(), float(session.total_collected()),
                 '', '', '']
    ws.append(total_row)
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)

    # Summary sheet.
    ws2 = wb.create_sheet("Summary")
    summary = [
        ['Session', session.name],
        ['Date', str(session.date)],
        ['Location', session.location or ''],
        ['Status', 'Active' if session.is_active else 'Closed'],
        [],
        ['Metric', 'Value'],
        ['Books distributed', session.total_books()],
        ['Book-sale transactions', session.book_count()],
        ['Book sales total', float(session.book_sale_total())],
        ['Donations total', float(session.donation_total())],
        ['Total collected', float(session.total_collected())],
        ['Temple amount due', float(session.temple_amount())],
        ['Total transactions', session.transaction_count()],
    ]
    for row in summary:
        ws2.append(row)
    for c in ws2['A6']:
        c.font = Font(bold=True)
    for c in ws2['B6']:
        c.font = Font(bold=True)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(buf.getvalue(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"{session.name}_{session.date}.xlsx".replace(' ', '_').replace('/', '-')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


# --- HTMX live-update fragments (read-only, safe without volunteer) ---

def totals_fragment(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    return render(request, 'audit/_totals.html', {'session': session})


def recent_fragment(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    recent = session.transactions.select_related('book', 'volunteer', 'book_price').all()[:10]
    return render(request, 'audit/_recent.html', {'session': session, 'recent': recent})
