from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.models import Perfil
from restaurante.models import Combo, Comanda, Item, Mesa, Prato
from restaurante.serializers import (
    ComboSerializer,
    ComandaSerializer,
    ItemSerializer,
    MesaSerializer,
    PratoSerializer,
)


def obter_organizacao_usuario(user):
    perfil = get_object_or_404(Perfil, usuario=user)
    return perfil.organizacao


class BaseOrganizacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = None

    def get_queryset(self):
        org = obter_organizacao_usuario(self.request.user)
        return self.model.objects.filter(organizacao=org)

    def perform_create(self, serializer):
        org = obter_organizacao_usuario(self.request.user)
        serializer.save(organizacao=org)


class PratoViewSet(BaseOrganizacaoViewSet):
    model = Prato
    serializer_class = PratoSerializer


class ComboViewSet(BaseOrganizacaoViewSet):
    model = Combo
    serializer_class = ComboSerializer


class MesaViewSet(BaseOrganizacaoViewSet):
    model = Mesa
    serializer_class = MesaSerializer


class ComandaViewSet(BaseOrganizacaoViewSet):
    model = Comanda
    serializer_class = ComandaSerializer


class ItemViewSet(BaseOrganizacaoViewSet):
    model = Item
    serializer_class = ItemSerializer