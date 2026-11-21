from django import forms

from .models import Book, Session, Volunteer


class VolunteerForm(forms.Form):
    volunteer = forms.ModelChoiceField(
        queryset=Volunteer.objects.filter(active=True),
        required=False,
        empty_label="— select existing —",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )
    new_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg',
                                       'placeholder': '…or type a new name'}),
    )


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name', 'date', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'location': forms.TextInput(attrs={'class': 'form-control form-control-lg',
                                                'placeholder': 'Optional, e.g. Temple hall'}),
        }


class BookTransactionForm(forms.Form):
    book = forms.ModelChoiceField(
        queryset=Book.objects.all(),
        empty_label="— select book —",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_book'}),
    )
    # Language is populated dynamically via HTMX once a book is chosen.
    language = forms.ChoiceField(
        choices=[('', 'Select a book first…')], required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg', 'id': 'id_language', 'disabled': True}),
    )
    quantity = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_quantity',
                                        'oninput': 'updateAmount()'}),
    )
    amount_paid = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'id': 'id_amount_paid',
                                        'step': '0.01', 'placeholder': 'Amount paid'}),
    )
    person_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'autocomplete': 'name',
                                       'placeholder': 'Person name'}),
    )
    mobile = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'inputmode': 'numeric',
                                       'autocomplete': 'tel', 'placeholder': 'Mobile (optional)'}),
    )
    notes = forms.CharField(
        max_length=300, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes (optional)'}),
    )

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        if session is not None:
            self.fields['book'].widget.attrs.update({
                'hx-get': f'/session/{session.id}/book-options/',
                'hx-trigger': 'change',
                'hx-target': '#book-options',
                'hx-swap': 'innerHTML',
            })


class DonationForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'step': '0.01',
                                        'placeholder': 'Donation amount', 'autofocus': True}),
    )
    person_name = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'autocomplete': 'name',
                                       'placeholder': 'Person name (optional)'}),
    )
    mobile = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'inputmode': 'numeric',
                                       'placeholder': 'Mobile (optional)'}),
    )
    notes = forms.CharField(
        max_length=300, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notes (optional)'}),
    )
