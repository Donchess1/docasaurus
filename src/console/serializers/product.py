from rest_framework import serializers

from console.models import Product, TicketPurchase
from utils.utils import EVENT_PRODUCT_FEE, generate_txn_reference


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "reference",
            "description",
            "price",
            "currency",
            "owner",
            "category",
            "quantity",
            "event",
            "tier",
            "is_active",
            "meta",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference",
            "slug",
            "owner",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        # Validate that only EVENT_TICKET category products can be linked to an event
        if data.get("event") and data.get("category") != "EVENT_TICKET":
            raise serializers.ValidationError(
                "Only products with category 'EVENT_TICKET' can be linked to an event."
            )
        if data.get("category") == "EVENT_TICKET" and not data.get("event"):
            raise serializers.ValidationError(
                "Products with the category 'EVENT_TICKET' must be linked to an event."
            )
        return data

    def create(self, validated_data):
        validated_data["reference"] = generate_txn_reference()
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "name" in validated_data and instance.name != validated_data["name"]:
            instance.slug = None  # Reset the slug so that it will be regenerated in the model's save method.
        return super().update(instance, validated_data)


class GenerateProductPaymentLinkSerializer(serializers.Serializer):
    product_reference = serializers.CharField()
    quantity = serializers.IntegerField()
    use_flat_fee = serializers.BooleanField(default=True)
    product_instance = None

    def validate_product_reference(self, value):
        instance = Product.objects.filter(reference=value).first()
        if not instance:
            raise serializers.ValidationError("Invalid product reference")
        self.product_instance = instance
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def validate(self, data):
        quantity = data.get("quantity")
        use_flat_fee = data.get("use_flat_fee")

        if use_flat_fee:
            charges = EVENT_PRODUCT_FEE
        else:
            charges = EVENT_PRODUCT_FEE * quantity

        data["product"] = self.product_instance
        data["charges"] = charges
        return data


class ProductTicketPurchaseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    ticket_name = serializers.CharField(source="ticket_product.name", read_only=True)
    amount_paid = serializers.CharField(source="transaction.amount", read_only=True)
    currency = serializers.CharField(source="transaction.currency", read_only=True)
    ticket_quantity = serializers.SerializerMethodField()

    class Meta:
        model = TicketPurchase
        fields = [
            "id",
            "purchase_date",
            "ticket_name",
            "ticket_code",
            "name",
            "email",
            "ticket_quantity",
            "amount_paid",
            "currency",
        ]

    def get_ticket_quantity(self, obj):
        if obj.transaction and obj.transaction.meta:
            return obj.transaction.meta.get("ticket_quantity", 1)
        return 1


class TicketPurchaseAnalyticsSerializer(serializers.Serializer):
    event = serializers.CharField()
    ticket_name = serializers.CharField()
    reference = serializers.CharField()
    count = serializers.IntegerField()
