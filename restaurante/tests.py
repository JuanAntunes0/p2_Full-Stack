from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Organizacao, Perfil
from restaurante.models import Comanda, Item, Mesa, Prato


class MultiTenantEApiTest(TestCase):
    def setUp(self):
        self.org_a = Organizacao.objects.create(nome='Restaurante A')
        self.org_b = Organizacao.objects.create(nome='Restaurante B')

        self.user_a = User.objects.create_user(username='admin_a', password='123')
        self.user_b = User.objects.create_user(username='admin_b', password='123')

        Perfil.objects.create(usuario=self.user_a, organizacao=self.org_a, papel='admin')
        Perfil.objects.create(usuario=self.user_b, organizacao=self.org_b, papel='admin')

        self.prato_a = Prato.objects.create(
            organizacao=self.org_a,
            nome='Prato A',
            descricao='Desc A',
            preco=Decimal('20.00'),
        )
        self.prato_b = Prato.objects.create(
            organizacao=self.org_b,
            nome='Prato B',
            descricao='Desc B',
            preco=Decimal('35.00'),
        )

        self.mesa_a = Mesa.objects.create(organizacao=self.org_a, numero=1)
        self.comanda_a = Comanda.objects.create(organizacao=self.org_a, mesa=self.mesa_a)
        Item.objects.create(
            organizacao=self.org_a,
            comanda=self.comanda_a,
            prato=self.prato_a,
            quantidade=2,
        )

    def test_isolamento_lista_e_detalhe_api(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)

        resp_lista = client.get('/api/pratos/')
        self.assertEqual(resp_lista.status_code, 200)
        nomes = [p['nome'] for p in resp_lista.data]
        self.assertIn('Prato A', nomes)
        self.assertNotIn('Prato B', nomes)

        resp_alheio = client.get(f'/api/pratos/{self.prato_b.id}/')
        self.assertEqual(resp_alheio.status_code, 404)

    def test_dashboard_isolado_por_organizacao(self):
        self.client.force_login(self.user_a)
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['kpis']['receita_total'], Decimal('40.00'))

        self.client.force_login(self.user_b)
        resp_b = self.client.get('/dashboard/')
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(resp_b.context['kpis']['receita_total'], 0)