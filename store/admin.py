from django.contrib import admin
from django.utils.html import format_html

from .models import AdminUser, Agent, Product, Promotion, ShopSettings, UserBag


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "email",
        "plan_badge",
        "product_count_display",
        "status_badge",
        "subscription_info",
        "created_at",
    ]
    list_filter = ["plan", "status", "created_at"]
    search_fields = ["full_name", "email"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def plan_badge(self, obj):
        colors = {"free": "#ffc107", "premium": "#28a745"}
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;">{}</span>',
            colors.get(obj.plan, "#6c757d"),
            obj.get_plan_display(),
        )

    def product_count_display(self, obj):
        return obj.products.count()

    def status_badge(self, obj):
        colors = {"active": "#28a745", "suspended": "#dc3545", "inactive": "#6c757d"}
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )

    def subscription_info(self, obj):
        if obj.subscription_days <= 0:
            return format_html('<span style="color:red;">Expired</span>')
        if obj.subscription_days <= 7:
            return format_html('<span style="color:orange;">{} days left</span>', obj.subscription_days)
        return format_html('<span style="color:green;">{} days left</span>', obj.subscription_days)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id_number",
        "title",
        "category",
        "price_display",
        "trending_badge",
        "availability_badge",
        "agent",
        "created_at",
    ]
    list_filter = ["category", "available", "trending", "created_at", "agent"]
    search_fields = ["title", "id_number", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at", "image_preview"]
    actions = ["mark_trending", "remove_trending", "mark_available", "mark_unavailable"]

    def price_display(self, obj):
        return "FREE" if obj.price <= 0 else f"${obj.price:,.2f}"

    def trending_badge(self, obj):
        if not obj.trending:
            return "Not trending"
        return format_html(
            '<span style="background:#ff9800;color:white;padding:3px 8px;border-radius:3px;">{}</span>',
            obj.get_carousel_badge_display(),
        )

    def availability_badge(self, obj):
        color = "#28a745" if obj.available else "#dc3545"
        label = "Available" if obj.available else "Unavailable"
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;">{}</span>',
            color,
            label,
        )

    def image_preview(self, obj):
        if not obj.image:
            return "No image"
        return format_html(
            '<img src="{}" style="max-width:200px;max-height:200px;border-radius:4px;" />',
            obj.image,
        )

    def mark_trending(self, request, queryset):
        updated = queryset.update(trending=True)
        self.message_user(request, f"{updated} products marked as trending.")

    def remove_trending(self, request, queryset):
        updated = queryset.update(trending=False)
        self.message_user(request, f"{updated} products removed from trending.")

    def mark_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f"{updated} products marked as available.")

    def mark_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f"{updated} products marked as unavailable.")


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = [
        "agent",
        "post_count",
        "days_count",
        "total_amount_display",
        "date_range",
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "created_at", "agent"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    actions = ["archive_promotions"]

    def total_amount_display(self, obj):
        return f"${obj.total_amount:,.2f}"

    def date_range(self, obj):
        return f"{obj.start_date} to {obj.end_date}"

    def status_badge(self, obj):
        colors = {
            "active": "#28a745",
            "upcoming": "#17a2b8",
            "expired": "#dc3545",
            "archived": "#6c757d",
            "cancelled": "#721c24",
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )

    def archive_promotions(self, request, queryset):
        updated = queryset.update(status="archived")
        self.message_user(request, f"{updated} promotions archived.")


@admin.register(UserBag)
class UserBagAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "added_at"]
    list_filter = ["added_at", "user"]
    search_fields = ["user__email", "user__username", "product__title"]
    readonly_fields = ["added_at"]
    ordering = ["-added_at"]

    def has_add_permission(self, request):
        return False


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ["key", "value_preview", "description", "updated_at"]
    ordering = ["key"]
    readonly_fields = ["updated_at"]

    def value_preview(self, obj):
        preview = str(obj.value)[:100]
        return preview + ("..." if len(obj.value) > 100 else "")


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["user__email", "user__username"]
    readonly_fields = ["created_at", "updated_at"]


admin.site.site_header = "Lomi-Store Administration"
admin.site.site_title = "Lomi-Store Admin"
admin.site.index_title = "Welcome to Lomi-Store Dashboard"

