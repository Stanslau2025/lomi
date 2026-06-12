from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Agent, Product, Promotion, UserBag
from .serializers import (
    AgentSerializer,
    ProductSerializer,
    PromotionSerializer,
    ShopSettingsSerializer,
    SignupSerializer,
    UserBagSerializer,
)


def home(request):
    return render(request, "index.html")


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAdminOrAgentProductOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or hasattr(request.user, "agent_profile"))
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return hasattr(request.user, "agent_profile") and obj.agent_id == request.user.agent_profile.id


def serialize_auth_user(user):
    payload = {
        "id": user.id,
        "email": user.email,
        "token": Token.objects.get_or_create(user=user)[0].key,
        "role": "admin" if user.is_staff else "customer",
        "fullName": user.get_full_name() or user.username,
    }
    if hasattr(user, "agent_profile"):
        payload["role"] = "agent"
        payload["agentId"] = str(user.agent_profile.id)
        payload["fullName"] = user.agent_profile.full_name
    return payload


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("agent").all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrAgentProductOwner]
    search_fields = ["title", "description", "category", "id_number"]
    ordering_fields = ["created_at", "price", "trending"]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = {
            "category": self.request.query_params.get("category"),
            "available": self.request.query_params.get("available"),
            "trending": self.request.query_params.get("trending"),
            "agent_id": self.request.query_params.get("agent"),
        }
        if filters["category"] and filters["category"] != "all":
            queryset = queryset.filter(category=filters["category"])
        if filters["available"] in {"true", "false"}:
            queryset = queryset.filter(available=filters["available"] == "true")
        if filters["trending"] in {"true", "false"}:
            queryset = queryset.filter(trending=filters["trending"] == "true")
        if filters["agent_id"]:
            queryset = queryset.filter(agent_id=filters["agent_id"])
        return queryset

    def perform_create(self, serializer):
        agent = getattr(self.request.user, "agent_profile", None) if self.request.user.is_authenticated else None
        if agent and not self.request.user.is_staff:
            serializer.save(agent=agent)
            return
        serializer.save()

    def perform_update(self, serializer):
        agent = getattr(self.request.user, "agent_profile", None) if self.request.user.is_authenticated else None
        if agent and not self.request.user.is_staff:
            serializer.save(agent=agent)
            return
        serializer.save()

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def bulk_update_trending(self, request):
        product_ids = request.data.get("product_ids", [])
        trending = bool(request.data.get("trending", False))
        badge = request.data.get("carousel_badge", "trending")
        updated = Product.objects.filter(id__in=product_ids).update(
            trending=trending,
            carousel_badge=badge,
        )
        return Response({"updated": updated}, status=status.HTTP_200_OK)


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.select_related("user").all().order_by("-created_at")
    serializer_class = AgentSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["full_name", "email"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        try:
            agent = request.user.agent_profile
        except Agent.DoesNotExist:
            return Response({"detail": "Agent profile not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(agent).data)


class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.select_related("agent").all().order_by("-created_at")
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminOrReadOnly]
    ordering_fields = ["created_at", "start_date", "total_amount"]

    def get_queryset(self):
        queryset = super().get_queryset()
        agent = self.request.query_params.get("agent")
        status_value = self.request.query_params.get("status")
        if agent:
            queryset = queryset.filter(agent_id=agent)
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def archive_expired(self, request):
        expired = Promotion.objects.filter(
            end_date__lt=timezone.now().date(),
            status__in=["active", "upcoming"],
        )
        count = expired.count()
        expired.update(status="archived")
        return Response({"archived": count}, status=status.HTTP_200_OK)


class UserBagViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        bag_items = UserBag.objects.filter(user=request.user).select_related("product")
        serializer = UserBagSerializer(bag_items, many=True)
        return Response([item["product"] for item in serializer.data])

    @action(detail=False, methods=["post"])
    def add(self, request):
        serializer = UserBagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bag_item, created = UserBag.objects.get_or_create(
            user=request.user,
            product=serializer.validated_data["product"],
        )
        return Response(
            UserBagSerializer(bag_item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def remove(self, request):
        product_id = request.data.get("product_id")
        UserBag.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        UserBag.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShopSettingsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        return Response(ShopSettingsSerializer.from_store())

    @action(detail=False, methods=["patch"], permission_classes=[permissions.IsAdminUser])
    def update_settings(self, request):
        if not request.user.is_staff:
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ShopSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        ShopSettingsSerializer.save_to_store(serializer.validated_data)
        return Response(ShopSettingsSerializer.from_store())


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"])
    def login(self, request):
        email = (request.data.get("email") or "").lower()
        password = request.data.get("password") or ""
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None

        if user:
            if not user.is_active:
                return Response(
                    {"detail": "Account is not activated. Check your email for the verification link."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user:
                login(request, authenticated_user)
                return Response(serialize_auth_user(authenticated_user))

        try:
            agent = Agent.objects.select_related("user").get(email__iexact=email)
        except Agent.DoesNotExist:
            agent = None

        agent_password_valid = False
        if agent:
            stored_password = agent.password or ""
            agent_password_valid = check_password(password, stored_password)
            if not agent_password_valid and stored_password == password:
                # Upgrade any legacy plain-text agent password on successful login.
                agent.password = make_password(password)
                agent.save(update_fields=["password"])
                agent_password_valid = True

        if agent and agent_password_valid and agent.status != "suspended":
            if agent.user is None:
                agent.user = User.objects.create_user(
                    username=f"agent__{agent.id}",
                    email=agent.email,
                    password=User.objects.make_random_password(),
                    first_name=agent.full_name,
                )
                agent.save(update_fields=["user"])
            login(request, agent.user, backend="django.contrib.auth.backends.ModelBackend")
            return Response(serialize_auth_user(agent.user))

        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["post"])
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        # If a user exists and is active, reject; if exists but inactive, we'll resend verification
        user = User.objects.filter(email__iexact=email).first()
        if user and user.is_active:
            return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data.get("name", ""),
            )
            user.is_active = False
            user.save()

        # Send verification email
        try:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activate_path = f"/store/activate/{uid}/{token}/"
            activation_link = request.build_absolute_uri(activate_path)
            subject = "Activate your account"
            message = render_to_string(
                "emails/activation_email.txt",
                {"activation_link": activation_link, "user": user},
            )
            send_mail(subject, message, None, [user.email], fail_silently=False)
        except Exception:
            pass

        return Response({"verification_required": True, "detail": "Verification email sent."}, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, "activation_success.html")

    return render(request, "activation_failed.html")
