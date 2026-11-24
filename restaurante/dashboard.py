from django import forms
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from restaurante.models import Comanda, Item


class PeriodoForm(forms.Form):
    inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    fim = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


def filtrar_periodo(request, qs, campo_data='comanda__data_abertura'):
    form = PeriodoForm(request.GET)
    if form.is_valid():
        inicio = form.cleaned_data.get('inicio')
        fim = form.cleaned_data.get('fim')
        if inicio:
            qs = qs.filter(**{f'{campo_data}__date__gte': inicio})
        if fim:
            qs = qs.filter(**{f'{campo_data}__date__lte': fim})
    return qs, form


def obter_metricas_dashboard(request, org):
    comandas_org = Comanda.objects.filter(organizacao=org)
    itens_org = Item.objects.select_related('comanda', 'prato', 'combo').filter(organizacao=org)

    itens_filtrados, form = filtrar_periodo(request, itens_org)

    total_comandas = comandas_org.count()
    comandas_abertas = comandas_org.filter(status='ABERTA').count()

    receita_pratos = (
        itens_filtrados.filter(prato__isnull=False)
        .aggregate(total=Sum(F('prato__preco') * F('quantidade')))['total']
        or 0
    )
    receita_combos = (
        itens_filtrados.filter(combo__isnull=False)
        .aggregate(total=Sum(F('combo__preco') * F('quantidade')))['total']
        or 0
    )
    receita_total = receita_pratos + receita_combos

    kpis = {
        'total_comandas': total_comandas,
        'comandas_abertas': comandas_abertas,
        'total_itens': itens_filtrados.aggregate(total=Sum('quantidade'))['total'] or 0,
        'receita_total': receita_total,
    }

    ranking_pratos = list(
        itens_filtrados.filter(prato__isnull=False)
        .values('prato__nome')
        .annotate(total=Sum('quantidade'))
        .order_by('-total')[:5]
    )

    por_mes_qs = (
        itens_filtrados.annotate(mes=TruncMonth('comanda__data_abertura'))
        .values('mes')
        .annotate(total=Sum('quantidade'))
        .order_by('mes')
    )
    por_mes = [
        {
            'mes': r['mes'].strftime('%m/%Y') if r['mes'] else 'Sem data',
            'total': r['total'] or 0,
        }
        for r in por_mes_qs
    ]

    distribuicao_status = list(
        comandas_org.values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    return {
        'form': form,
        'kpis': kpis,
        'ranking_pratos': ranking_pratos,
        'por_mes': por_mes,
        'distribuicao_status': distribuicao_status,
        'itens_filtrados': itens_filtrados,
    }