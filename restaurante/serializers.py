from rest_framework import serializers
from restaurante.models import Combo, Comanda, Item, Mesa, Prato


class OrganizacaoScopedSerializerMixin:
    """Garante que ForeignKeys internos pertençam à mesma organização do utilizador."""

    def _filtrar_queryset_por_org(self, field_name):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'perfil'):
            org = request.user.perfil.organizacao
            field = self.fields.get(field_name)
            if field is not None and hasattr(field, 'queryset') and field.queryset is not None:
                field.queryset = field.queryset.filter(organizacao=org)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in getattr(self.Meta, 'org_fk_fields', []):
            self._filtrar_queryset_por_org(field_name)


class PratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prato
        fields = '__all__'
        read_only_fields = ['organizacao']


class ComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = Combo
        fields = '__all__'
        read_only_fields = ['organizacao']


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = '__all__'
        read_only_fields = ['organizacao']


class ComandaSerializer(OrganizacaoScopedSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Comanda
        fields = '__all__'
        read_only_fields = ['organizacao', 'data_abertura']
        org_fk_fields = ['mesa']


class ItemSerializer(OrganizacaoScopedSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['organizacao']
        org_fk_fields = ['comanda', 'prato', 'combo']