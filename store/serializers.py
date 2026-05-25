from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Agent, Product, Promotion, ShopSettings, UserBag


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "id_number",
            "title",
            "category",
            "description",
            "price",
            "old_price",
            "image",
            "images",
            "image_urls",
            "cloudinary_public_id",
            "cloudinary_public_ids",
            "available",
            "trending",
            "carousel_badge",
            "phone",
            "whatsapp_link",
            "location_link",
            "agent",
            "is_claimed",
            "claimed_by_name",
            "claimed_by_email",
            "claimed_at",
            "claimed_service_confirmed",
            "promo_id",
            "trending_until",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_images(self, obj):
        if obj.image_urls:
            return obj.image_urls
        return [obj.image] if obj.image else []


class AgentSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source="products.count", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "password",
            "plan",
            "subscription_days",
            "status",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        if password:
            validated_data["password"] = make_password(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.password = make_password(password)
        instance.save()
        return instance


class PromotionSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.full_name", read_only=True)
    agent_email = serializers.CharField(source="agent.email", read_only=True)

    class Meta:
        model = Promotion
        fields = [
            "id",
            "agent",
            "agent_name",
            "agent_email",
            "post_count",
            "days_count",
            "start_date",
            "end_date",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserBagSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )

    class Meta:
        model = UserBag
        fields = ["id", "product", "product_id", "added_at"]
        read_only_fields = ["id", "added_at"]


class ShopSettingsSerializer(serializers.Serializer):
    defaultLocationLink = serializers.CharField(required=False, allow_blank=True)
    productIdSequence = serializers.IntegerField(required=False, min_value=1)
    promoPricePerDay = serializers.IntegerField(required=False, min_value=0)

    @staticmethod
    def from_store():
        data = {
            "defaultLocationLink": "",
            "productIdSequence": 1,
            "promoPricePerDay": 200,
        }
        for setting in ShopSettings.objects.all():
            value = setting.value
            if setting.key in {"productIdSequence", "promoPricePerDay"}:
                try:
                    value = int(value)
                except ValueError:
                    pass
            data[setting.key] = value
        return data

    @staticmethod
    def save_to_store(validated_data):
        for key, value in validated_data.items():
            ShopSettings.objects.update_or_create(
                key=key,
                defaults={"value": str(value)},
            )


class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()
