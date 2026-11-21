from django.contrib import admin

from .models import Book, BookPrice, Volunteer, Session, Transaction


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(BookPrice)
class BookPriceAdmin(admin.ModelAdmin):
    list_display = ('book', 'language', 'price')
    list_filter = ('language',)
    search_fields = ('book__name',)


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_at')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'location')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'session', 'type', 'book', 'language', 'person_name', 'quantity', 'amount_paid', 'volunteer')
    list_filter = ('type', 'session')
    search_fields = ('person_name', 'mobile', 'book__name')
