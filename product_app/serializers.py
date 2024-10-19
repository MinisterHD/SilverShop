from rest_framework import serializers
from .models import *
from django.core.files.storage import default_storage
from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField

class SubcategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Subcategory)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = Subcategory
        fields = ['id', 'translations','category','category_name','slugname'] 
    def get_translations(self, obj):
            return {
                lang: {
                 'name': obj.safe_translation_getter('name', language_code=lang)
                }
                 for lang in obj.get_available_languages()   }
    
class CategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Category)
    sub_categories = SubcategorySerializer(many=True, read_only=True, source='subcategory_set')

    class Meta:
        model = Category
        fields = ['id', 'translations', 'slugname', 'sub_categories']

class ProductSerializer(TranslatableModelSerializer):
    translations_en_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    translations_en_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    translations_fa_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    translations_fa_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    images = serializers.ListField(
        child=serializers.ImageField(max_length=100000, allow_empty_file=False, use_url=True),
        write_only=True,
        required=False
    )

    slugname = serializers.CharField(required=False)
    stock = serializers.IntegerField(required=False)
    price = serializers.IntegerField(required=False)

    translations = serializers.SerializerMethodField(read_only=True)
    category_name_en = serializers.SerializerMethodField(read_only=True)
    category_name_fa = serializers.SerializerMethodField(read_only=True)
    category_slug = serializers.SerializerMethodField(read_only=True)
    subcategory_name_en = serializers.SerializerMethodField(read_only=True)
    subcategory_name_fa = serializers.SerializerMethodField(read_only=True)
    subcategory_slug = serializers.SerializerMethodField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_translations(self, obj):
        return {
            'en': {
                'name': obj.safe_translation_getter('name', language_code='en'),
                'description': obj.safe_translation_getter('description', language_code='en')
            },
            'fa': {
                'name': obj.safe_translation_getter('name', language_code='fa'),
                'description': obj.safe_translation_getter('description', language_code='fa')
            },
        }

    def get_category_name_en(self, obj):
        return obj.category.safe_translation_getter('name', language_code='en') if obj.category else None

    def get_category_name_fa(self, obj):
        return obj.category.safe_translation_getter('name', language_code='fa') if obj.category else None

    def get_category_slug(self, obj):
        return obj.category.slugname if obj.category else None

    def get_subcategory_name_en(self, obj):
        return obj.subcategory.safe_translation_getter('name', language_code='en') if obj.subcategory else None

    def get_subcategory_name_fa(self, obj):
        return obj.subcategory.safe_translation_getter('name', language_code='fa') if obj.subcategory else None

    def get_subcategory_slug(self, obj):
        return obj.subcategory.slugname if obj.subcategory else None

    def create(self, validated_data):
        translations_en_name = validated_data.pop('translations_en_name', None)
        translations_en_description = validated_data.pop('translations_en_description', None)
        translations_fa_name = validated_data.pop('translations_fa_name', None)
        translations_fa_description = validated_data.pop('translations_fa_description', None)
        images = validated_data.pop('images', None)

        product = Product.objects.create(**validated_data)

        translations = {
            'en': {
                'name': translations_en_name,
                'description': translations_en_description,
            },
            'fa': {
                'name': translations_fa_name,
                'description': translations_fa_description,
            },
        }

        if translations:
            for lang, translation in translations.items():
                product.set_current_language(lang)
                product.name = translation['name']
                product.description = translation['description']
                product.save_translations()

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

        translations = {
            'en': {
                'name': validated_data.get('translations_en_name', instance.safe_translation_getter('name', default=None, language_code='en')),
                'description': validated_data.get('translations_en_description', instance.safe_translation_getter('description', default=None, language_code='en')),
            },
            'fa': {
                'name': validated_data.get('translations_fa_name', instance.safe_translation_getter('name', default=None, language_code='fa')),
                'description': validated_data.get('translations_fa_description', instance.safe_translation_getter('description', default=None, language_code='fa')),
            },
        }

        for lang, translation in translations.items():
            instance.set_current_language(lang)
            if 'name' in translation:
                instance.name = translation['name']
            if 'description' in translation:
                instance.description = translation['description']
            instance.save_translations()

        images = validated_data.get('images', None)
        if images and isinstance(images, list):
            if len(images) > 0:
                instance.image1 = images[0]
            if len(images) > 1:
                instance.image2 = images[1]
            if len(images) > 2:
                instance.image3 = images[2]
            if len(images) > 3:
                instance.image4 = images[3]

        for attr, value in validated_data.items():
            if hasattr(instance, attr):  
                setattr(instance, attr, value)

        instance.save()
        return instance
    
class ProductDetailSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    class Meta:
        model = Product
        fields = '__all__' 

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
        read_only_fields = ['user', 'created_at','product']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'  




