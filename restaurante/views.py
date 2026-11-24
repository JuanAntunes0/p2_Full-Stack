import csv
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .dashboard import obter_metricas_dashboard
from .forms import PratoForm
from .models import Combo, Comanda, Item, Mesa, Prato


def org_atual(request):
    return request.user.perfil.organizacao


def papel_requerido(*papeis):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            perfil = getattr(request.user, 'perfil', None)
            if not perfil or perfil.papel not in papeis:
                return HttpResponseForbidden('Acesso restrito ao perfil autorizado.')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@login_required
def inicio(request):
    return render(request, 'restaurante/inicio.html')


@login_required
def lista_pratos(request):
    org = org_atual(request)
    pratos = Prato.objects.filter(organizacao=org)

    q = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')

    if q:
        pratos = pratos.filter(Q(nome__icontains=q) | Q(descricao__icontains=q))

    if categoria:
        pratos = pratos.filter(categoria=categoria)

    return render(
        request,
        'restaurante/lista_pratos.html',
        {
            'pratos': pratos,
            'categorias': Prato.CATEGORIA_CHOICES,
        }
    )


@login_required
@papel_requerido('admin')
def criar_prato(request):
    org = org_atual(request)

    if request.method == 'POST':
        form = PratoForm(request.POST)
        if form.is_valid():
            prato = form.save(commit=False)
            prato.organizacao = org
            prato.save()
            return redirect('lista_pratos')
    else:
        form = PratoForm()

    return render(request, 'restaurante/form_prato.html', {'form': form, 'titulo': 'Cadastrar Prato'})


@login_required
@papel_requerido('admin')
def editar_prato(request, prato_id):
    org = org_atual(request)
    prato = get_object_or_404(Prato, id=prato_id, organizacao=org)

    if request.method == 'POST':
        form = PratoForm(request.POST, instance=prato)
        if form.is_valid():
            prato = form.save(commit=False)
            prato.organizacao = org
            prato.save()
            return redirect('lista_pratos')
    else:
        form = PratoForm(instance=prato)

    return render(request, 'restaurante/form_prato.html', {'form': form, 'titulo': 'Editar Prato'})


@login_required
@papel_requerido('admin')
def excluir_prato(request, prato_id):
    org = org_atual(request)
    prato = get_object_or_404(Prato, id=prato_id, organizacao=org)
    prato.delete()
    return redirect('lista_pratos')


@login_required
def lista_combos(request):
    org = org_atual(request)
    combos = Combo.objects.filter(organizacao=org)

    return render(
        request,
        'restaurante/lista_combos.html',
        {'combos': combos}
    )


@login_required
def lista_mesas(request):
    org = org_atual(request)
    mesas = Mesa.objects.filter(organizacao=org).order_by('numero')

    return render(
        request,
        'restaurante/lista_mesas.html',
        {'mesas': mesas}
    )


@login_required
def abrir_comanda(request, mesa_id):
    org = org_atual(request)
    mesa = get_object_or_404(Mesa, id=mesa_id, organizacao=org)

    comanda = Comanda.objects.filter(
        mesa=mesa,
        organizacao=org,
        status='ABERTA'
    ).first()

    if not comanda:
        comanda = Comanda.objects.create(mesa=mesa, organizacao=org)

        mesa.status = 'OCUPADA'
        mesa.save()

    pratos = Prato.objects.filter(organizacao=org, disponivel=True)
    combos = Combo.objects.filter(organizacao=org, disponivel=True)

    itens = comanda.itens.filter(organizacao=org)

    total = 0

    for item in itens:
        if item.prato:
            total += item.prato.preco * item.quantidade

        elif item.combo:
            total += item.combo.preco * item.quantidade

    return render(
        request,
        'restaurante/comanda.html',
        {
            'mesa': mesa,
            'comanda': comanda,
            'pratos': pratos,
            'combos': combos,
            'itens': itens,
            'total': total,
        }
    )


@login_required
def adicionar_prato(request, comanda_id, prato_id):
    org = org_atual(request)
    comanda = get_object_or_404(Comanda, id=comanda_id, organizacao=org)
    prato = get_object_or_404(Prato, id=prato_id, organizacao=org)

    item = Item.objects.filter(
        comanda=comanda,
        prato=prato,
        organizacao=org,
    ).first()

    if item:
        item.quantidade += 1
        item.save()
    else:
        Item.objects.create(
            comanda=comanda,
            prato=prato,
            organizacao=org,
            quantidade=1
        )

    return redirect('abrir_comanda', mesa_id=comanda.mesa.id)


@login_required
def adicionar_combo(request, comanda_id, combo_id):
    org = org_atual(request)
    comanda = get_object_or_404(Comanda, id=comanda_id, organizacao=org)
    combo = get_object_or_404(Combo, id=combo_id, organizacao=org)

    item = Item.objects.filter(
        comanda=comanda,
        combo=combo,
        organizacao=org,
    ).first()

    if item:
        item.quantidade += 1
        item.save()
    else:
        Item.objects.create(
            comanda=comanda,
            combo=combo,
            organizacao=org,
            quantidade=1
        )

    return redirect('abrir_comanda', mesa_id=comanda.mesa.id)


@login_required
def fechar_comanda(request, comanda_id):
    org = org_atual(request)
    comanda = get_object_or_404(Comanda, id=comanda_id, organizacao=org)

    comanda.status = 'FECHADA'
    comanda.save()

    mesa = comanda.mesa
    mesa.status = 'LIVRE'
    mesa.save()

    return redirect('lista_mesas')


@login_required
def remover_item(request, item_id):
    org = org_atual(request)
    item = get_object_or_404(Item, id=item_id, organizacao=org)

    mesa_id = item.comanda.mesa.id

    if item.quantidade > 1:
        item.quantidade -= 1
        item.save()
    else:
        item.delete()

    return redirect('abrir_comanda', mesa_id=mesa_id)


@login_required
def dashboard(request):
    org = org_atual(request)
    perfil = request.user.perfil
    dados = obter_metricas_dashboard(request, org)
    dados['mostra_series'] = perfil.eh_admin
    dados['pode_exportar'] = perfil.eh_admin
    return render(request, 'restaurante/dashboard.html', dados)


@login_required
@papel_requerido('admin')
def exportar_dashboard_csv(request):
    org = org_atual(request)
    dados = obter_metricas_dashboard(request, org)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="dashboard_restaurante.csv"'

    writer = csv.writer(response)
    writer.writerow(['Comanda', 'Mesa', 'Item', 'Quantidade', 'Data Abertura'])

    for item in dados['itens_filtrados']:
        nome_item = item.prato.nome if item.prato else (item.combo.nome if item.combo else '-')
        writer.writerow([
            item.comanda.id,
            item.comanda.mesa.numero,
            nome_item,
            item.quantidade,
            item.comanda.data_abertura.strftime('%Y-%m-%d %H:%M'),
        ])

    return response
