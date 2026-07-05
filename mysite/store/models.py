import uuid

from django.contrib.auth.models import User
from django.db import models


class Agent(models.Model):
    PLAN_CHOICES = [
        ("free", "Free Plan"),
        ("premium", "Premium Plan"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("inactive", "Inactive"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="agent_profile",
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    registration_code = models.CharField(max_length=20, unique=True, blank=True)
    password = models.CharField(max_length=255, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    subscription_days = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @classmethod
    def generate_registration_code(cls):
        count = cls.objects.count()
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        while True:
            letter = alphabet[count % len(alphabet)]
            number = 20 + (count * 10)
            code = f"{letter}{number}"
            if not cls.objects.filter(registration_code__iexact=code).exists():
                return code
            count += 1

    def save(self, *args, **kwargs):
        if self.registration_code:
            self.registration_code = self.registration_code.strip().upper()
        else:
            self.registration_code = self.generate_registration_code()
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"registration_code"}
        super().save(*args, **kwargs)


class Product(models.Model):
    CAROUSEL_BADGE_CHOICES = [
        ("trending", "Trending"),
        ("hot", "Hot Post"),
        ("popular", "Popular"),
        ("featured", "Featured"),
        ("editors_pick", "Editor's Pick"),
        ("just_arrived", "Just Arrived"),
        ("best_deal", "Best Deal"),
        ("flash_sale", "Flash Sale"),
        ("top_rated", "Top Rated"),
        ("limited_stock", "Limited Stock"),
        ("most_loved", "Most Loved"),
        ("staff_favorite", "Staff Favorite"),
        ("weekend_pick", "Weekend Pick"),
        ("new_drop", "New Drop"),
        ("vip_choice", "VIP Choice"),
        ("fresh_finds", "Fresh Finds"),
        ("mega_save", "Mega Save"),
        ("premium_pick", "Premium Pick"),
        ("city_choice", "City Choice"),
        ("crowd_favorite", "Crowd Favorite"),
        ("fast_moving", "Fast Moving"),
        ("showroom_pick", "Showroom Pick"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default="Uncategorized")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.URLField(blank=True)
    image_urls = models.JSONField(default=list, blank=True)
    cloudinary_public_id = models.CharField(max_length=255, blank=True)
    cloudinary_public_ids = models.JSONField(default=list, blank=True)
    available = models.BooleanField(default=True)
    trending = models.BooleanField(default=False)
    carousel_badge = models.CharField(
        max_length=50,
        choices=CAROUSEL_BADGE_CHOICES,
        default="trending",
    )
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_link = models.URLField(blank=True)
    location_link = models.URLField(blank=True)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    is_claimed = models.BooleanField(default=False)
    claimed_by_name = models.CharField(max_length=255, blank=True)
    claimed_by_email = models.EmailField(blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    claimed_service_confirmed = models.BooleanField(default=False)
    promo_id = models.CharField(max_length=36, blank=True)
    trending_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trending", "-created_at"]),
            models.Index(fields=["category", "available"]),
            models.Index(fields=["agent"]),
        ]

    def __str__(self):
        return self.title


class Promotion(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("upcoming", "Upcoming"),
        ("expired", "Expired"),
        ("archived", "Archived"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="promotions")
    post_count = models.IntegerField(default=1)
    days_count = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Promotions"

    def __str__(self):
        return f"Promo for {self.agent.full_name} ({self.start_date} to {self.end_date})"


class UserBag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bag_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product_bag"),
        ]
        ordering = ["-added_at"]
        verbose_name_plural = "User Bags"

    def __str__(self):
        return f"{self.user.email or self.user.username} - {self.product.title}"


class ShopSettings(models.Model):
    key = models.CharField(max_length=100, unique=True, primary_key=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shop Settings"

    def __str__(self):
        return self.key


class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    role = models.CharField(max_length=50, default="admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email or self.user.username} ({self.role})"
