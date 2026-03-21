from django.contrib import admin
from django.contrib.admin import actions
from .models import Category, Product, Cart, CartItem, Order, OrderItem, ProductReview, Payment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'available', 'stock']
    list_filter = ['available', 'category']
    prepopulated_fields = {'slug': ('name',)}

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'paid', 'created']
    list_filter = ['status', 'paid', 'created']
    search_fields = ['id', 'user__username']
    inlines = [OrderItemInline, PaymentInline]
    
    actions = ['confirm_payment', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def confirm_payment(self, request, queryset):
        updated = 0
        for order in queryset:
            if hasattr(order, 'payment') and order.payment.status == 'PENDING':
                order.payment.status = 'PAID'
                order.payment.save()
                order.paid = True
                order.status = 'PROCESSING'
                order.save()
                updated += 1
        self.message_user(request, f'Confirmed payment for {updated} order(s).')
    confirm_payment.short_description = 'Confirm selected pending payments'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='PROCESSING')
        self.message_user(request, f'Marked {updated} order(s) as PROCESSING.')
    mark_as_processing.short_description = 'Mark selected as PROCESSING'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='SHIPPED')
        self.message_user(request, f'Marked {updated} order(s) as SHIPPED.')
    mark_as_shipped.short_description = 'Mark selected as SHIPPED'
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='DELIVERED')
        self.message_user(request, f'Marked {updated} order(s) as DELIVERED.')
    mark_as_delivered.short_description = 'Mark selected as DELIVERED'

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ProductReview)
