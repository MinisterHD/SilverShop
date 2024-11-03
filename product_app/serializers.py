from rest_framework import serializers
from .models import *

class SubcategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'category', 'category_name', 'slugname']

class CategorySerializer(serializers.ModelSerializer):
    sub_categories = SubcategorySerializer(many=True, read_only=True, source='subcategory_set')

    class Meta:
        model = Category
        fields = ['id', 'name', 'slugname', 'sub_categories']

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=100000, allow_empty_file=False, use_url=True),
        write_only=True,
        required=False
    )
    images_list = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_images_list(self, obj):
        request = self.context.get('request')
        return obj.get_image_urls(request)

    def create(self, validated_data):
        images = validated_data.pop('images', None)
        product = Product.objects.create(**validated_data)

        if images and isinstance(images, list):
            if len(images) > 0:
                product.image1 = images[0]
            if len(images) > 1:
                product.image2 = images[1]
            if len(images) > 2:
                product.image3 = images[2]
            if len(images) > 3:
                product.image4 = images[3]

        product.save()
        return product

    def update(self, instance, validated_data):
        images = validated_data.get('images', None)
        if images and isinstance(images, list):
            instance.image1 = None
            instance.image2 = None
            instance.image3 = None
            instance.image4 = None

            if len(images) > 0:
                instance.image1 = images[0]
            if len(images) > 1:
                instance.image2 = images[1]
            if len(images) > 2:
                instance.image3 = images[2]
            if len(images) > 3:
                instance.image4 = images[3]

        for attr, value in validated_data.items():
            if hasattr(instance, attr) and attr != 'images':
                setattr(instance, attr, value)

        instance.save()
        return instance

class CommentSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'owner', 'owner_name', 'owner_email', 'text', 'created_at', 'product')
        read_only_fields = ['id', 'created_at']

    def get_owner_name(self, obj):
        return obj.owner.username

    def get_owner_email(self, obj):
        return obj.owner.email

class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class RatingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'product']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'