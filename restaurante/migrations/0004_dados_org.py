from django.db import migrations


def org_padrao(apps, schema_editor):
    Organizacao = apps.get_model('core', 'Organizacao')
    Prato = apps.get_model('restaurante', 'Prato')
    Combo = apps.get_model('restaurante', 'Combo')
    Mesa = apps.get_model('restaurante', 'Mesa')
    Comanda = apps.get_model('restaurante', 'Comanda')
    Item = apps.get_model('restaurante', 'Item')

    org, _ = Organizacao.objects.get_or_create(nome='Organização padrão')

    for model in (Prato, Combo, Mesa, Comanda, Item):
        model.objects.filter(organizacao__isnull=True).update(organizacao=org)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        ('restaurante', '0003_comanda_organizacao_combo_organizacao_and_more'),
    ]

    operations = [
        migrations.RunPython(org_padrao, migrations.RunPython.noop),
    ]