from typing import Optional

from django.db import IntegrityError
from django.db.models import Sum
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from src.accounts.models import AdvUser
from src.accounts.serializers import UserSlimSerializer
from src.activity.models import TokenHistory
from src.games.exceptions import AlreadyListed
from src.games.signals import category_added, game_created, subcategory_added_updated
from src.networks.serializers import NetworkSerializer
from src.store.models import Collection, Ownership, Status, Token
from src.store.serializers import CollectionSlimSerializer
from src.utilities import AddressField

from .models import GameCategory, GameCompany, GameSubCategory


class GameSubCategorySerializer(serializers.ModelSerializer):
    collections = serializers.SerializerMethodField()
    owner = serializers.CharField(source="category.game.user.id")
    website = serializers.CharField(source="category.game.website", read_only=True)
    twitter = serializers.CharField(source="category.game.twitter", read_only=True)
    instagram = serializers.CharField(source="category.game.instagram", read_only=True)
    telegram = serializers.CharField(source="category.game.telegram", read_only=True)
    discord = serializers.CharField(source="category.game.discord", read_only=True)
    medium = serializers.CharField(source="category.game.medium", read_only=True)
    facebook = serializers.CharField(source="category.game.facebook", read_only=True)
    network = NetworkSerializer(source="category.game.network", read_only=True)
    owners_count = serializers.SerializerMethodField()
    volume_traded = serializers.SerializerMethodField()
    floor_price = serializers.SerializerMethodField()
    tokens_count = serializers.SerializerMethodField()

    def get_floor_price(self, obj) -> int:
        token = self.get_token_with_min_price(obj)
        if token:
            return token.price
        return 0

    def get_tokens_count(self, obj) -> int:
        return (
            Token.objects.committed().filter(collection__game_subcategory=obj).count()
        )

    def get_owners_count(self, obj) -> int:
        return (
            AdvUser.objects.filter(owned_tokens__collection__game_subcategory=obj)
            .distinct()
            .count()
        )

    def get_volume_traded(self, obj) -> float:
        return (
            TokenHistory.objects.filter(
                token__collection__game_subcategory=obj,
                method="Buy",
            )
            .aggregate(usd_sum=Sum("USD_price"))
            .get("usd_sum")
        )

    def get_token_with_min_price(self, obj) -> Optional["Token"]:
        tokens = list(
            Token.objects.committed().filter(collection__game_subcategory=obj)
        )
        owners = Ownership.objects.filter(token__in=tokens).filter(
            selling=True, currency__isnull=False
        )
        min_price_owner = None
        owners = [owner for owner in owners if owner.price_or_minimal_bid_usd]
        if owners:
            min_price_owner = sorted(
                list(owners), key=lambda x: x.price_or_minimal_bid_usd
            )[0]
        if min_price_owner:
            token = min_price_owner.token
            return token

    class Meta:
        model = GameSubCategory
        fields = (
            "id",
            "name",
            "avatar",
            "cover",
            "address_list",
            "collections",
            "owner",
            "website",
            "twitter",
            "instagram",
            "telegram",
            "discord",
            "medium",
            "facebook",
            "network",
            "owners_count",
            "tokens_count",
            "volume_traded",
            "floor_price",
        )

    @swagger_serializer_method(serializer_or_field=CollectionSlimSerializer(many=True))
    def get_collections(self, obj):
        return CollectionSlimSerializer(obj.collections.committed(), many=True).data


class GameSubCategoryPatchSerializer(GameSubCategorySerializer):
    class Meta:
        model = GameSubCategory
        fields = ("name", "avatar_ipfs", "cover_ipfs")


class GameCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    owner = serializers.CharField(source="game.user.id")
    website = serializers.CharField(source="game.website")
    twitter = serializers.CharField(source="game.twitter", read_only=True)
    instagram = serializers.CharField(source="game.instagram", read_only=True)
    telegram = serializers.CharField(source="game.telegram", read_only=True)
    discord = serializers.CharField(source="game.discord", read_only=True)
    medium = serializers.CharField(source="game.medium", read_only=True)
    facebook = serializers.CharField(source="game.facebook", read_only=True)
    network = NetworkSerializer(source="game.network", read_only=True)
    owners_count = serializers.SerializerMethodField()
    volume_traded = serializers.SerializerMethodField()
    floor_price = serializers.SerializerMethodField()
    tokens_count = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=GameSubCategorySerializer(many=True))
    def get_subcategories(self, obj):
        return GameSubCategorySerializer(
            obj.subcategories.filter(is_approved=True), many=True
        ).data

    def get_floor_price(self, obj) -> int:
        token = self.get_token_with_min_price(obj)
        if token:
            return token.price
        return 0

    def get_tokens_count(self, obj) -> int:
        return (
            Token.objects.committed()
            .filter(collection__game_subcategory__category=obj)
            .count()
        )

    def get_owners_count(self, obj) -> int:
        return (
            AdvUser.objects.filter(
                owned_tokens__collection__game_subcategory__category=obj
            )
            .distinct()
            .count()
        )

    def get_volume_traded(self, obj) -> float:
        return (
            TokenHistory.objects.filter(
                token__collection__game_subcategory__category=obj,
                method="Buy",
            )
            .aggregate(usd_sum=Sum("USD_price"))
            .get("usd_sum")
        )

    def get_token_with_min_price(self, obj) -> Optional["Token"]:
        tokens = list(
            Token.objects.committed().filter(collection__game_subcategory__category=obj)
        )
        owners = Ownership.objects.filter(token__in=tokens).filter(
            selling=True, currency__isnull=False
        )
        min_price_owner = None
        owners = [owner for owner in owners if owner.price_or_minimal_bid_usd]
        if owners:
            min_price_owner = sorted(
                list(owners), key=lambda x: x.price_or_minimal_bid_usd
            )[0]
        if min_price_owner:
            token = min_price_owner.token
            return token

    class Meta:
        model = GameCategory
        fields = (
            "id",
            "name",
            "avatar",
            "cover",
            "address_list",
            "subcategories",
            "owner",
            "website",
            "twitter",
            "instagram",
            "telegram",
            "discord",
            "medium",
            "facebook",
            "network",
            "owners_count",
            "tokens_count",
            "volume_traded",
            "floor_price",
        )


class GameCategoryPatchSerializer(GameCategorySerializer):
    class Meta:
        model = GameCategory
        fields = ("name", "avatar_ipfs", "cover_ipfs")


class GameCompanySerializer(serializers.ModelSerializer):
    user = UserSlimSerializer(read_only=True)
    network = NetworkSerializer(read_only=True)
    categories = GameCategorySerializer(many=True)
    avatar = serializers.CharField(read_only=True)
    banner = serializers.CharField(read_only=True)
    video_covers = serializers.ListField(child=serializers.CharField(), required=False)
    photos = serializers.ListField(child=serializers.CharField(), required=False)

    @swagger_serializer_method(serializer_or_field=GameCategorySerializer(many=True))
    def get_categories(self, obj):
        return GameCategorySerializer(
            obj.categories.filter(is_approved=True), many=True
        ).data

    class Meta:
        model = GameCompany
        fields = (
            "name",
            "email",
            "whitepaper_link",
            "background_color",
            "description",
            "website",
            "twitter",
            "instagram",
            "telegram",
            "discord",
            "medium",
            "facebook",
            "user",
            "network",
            "categories",
            "avatar",
            "banner",
            "videos",
            "video_covers",
            "developer",
            "release_status",
            "platform",
            "genre",
            "photos",
        )

    def create(self, validated_data):
        context = self.context
        categories = validated_data.pop("categories")
        game_instance = self.Meta.model.objects.create(
            **validated_data,
            network_id=context.get("network"),
            user_id=context.get("user"),
        )
        for category in categories:
            create_category(context, game_instance, category)

        game_created.send(sender=self.Meta.model.__class__, instance=game_instance)
        return game_instance


class GameCollectionCreateSerializer(serializers.Serializer):
    addresses = serializers.ListField(child=serializers.DictField(child=AddressField()))

    def create(self, validated_data):
        context = self.context
        subcategory_instance = GameSubCategory.objects.get(
            id=context.get("subcategory")
        )
        addresses = validated_data.pop("addresses")
        subcategory_instance.category.game.validating_result = None
        subcategory_instance.category.game.save()
        create_collections(context, subcategory_instance, addresses)
        subcategory_added_updated.send(
            sender=GameSubCategory.__class__, instance=subcategory_instance
        )
        return subcategory_instance


class GameSubCategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    addresses = serializers.ListField(child=serializers.DictField(child=AddressField()))

    def create(self, validated_data):
        context = self.context
        category = GameCategory.objects.get(id=context.get("category"))
        addresses = validated_data.pop("addresses")
        subcategory_instance = create_subcategory(
            context, category, addresses, {**validated_data}
        )
        category.game.validating_result = None
        category.game.save()
        subcategory_added_updated.send(
            sender=GameSubCategory.__class__, instance=subcategory_instance
        )
        return subcategory_instance


class GameCategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    subcategories = GameSubCategoryCreateSerializer(many=True)

    def create(self, validated_data):
        context = self.context
        game_company = GameCompany.objects.get(id=context.get("game"))
        category_instance = create_category(context, game_company, {**validated_data})
        category_instance.game.validating_result = None
        category_instance.game.save()
        category_added.send(sender=GameCategory.__class__, instance=category_instance)
        return category_instance


class GameCompanyCreateSerializer(GameCompanySerializer):
    avatar = serializers.CharField()
    categories = GameCategoryCreateSerializer(many=True)


def create_collections(context, subcategory, addresses):
    for address in addresses:
        col = Collection.objects.filter(
            network_id=context.get("network"),
            address__iexact=address["address"],
            game_subcategory__isnull=True,
        ).first()
        if col:
            col.game_subcategory = subcategory
            col.save(update_fields=("game_subcategory",))
            return
        try:
            Collection.objects.create(
                network_id=context.get("network"),
                address=address["address"],
                creator_id=context.get("user"),
                creator_royalty=0,
                game_subcategory=subcategory,
                is_imported=True,
                status=Status.PENDING,
            )

        except IntegrityError:
            raise AlreadyListed(
                detail=f"Collection {address['address']} already listed"
            )


def create_subcategory(context, category, addresses, subcategory_data):
    subcategory_instance = GameSubCategory.objects.create(
        category=category, **subcategory_data
    )
    create_collections(context, subcategory_instance, addresses)
    return subcategory_instance


def create_category(context, game_company, input_data):
    subcategories = input_data.pop("subcategories")
    category_instance = GameCategory.objects.create(game=game_company, **input_data)
    for subcategory in subcategories:
        addresses = subcategory.pop("addresses")
        create_subcategory(context, category_instance, addresses, subcategory)

    return category_instance
