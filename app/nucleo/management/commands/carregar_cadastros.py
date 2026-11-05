from django.core.management.base import BaseCommand
from django.db import transaction

from nucleo.models import Ano, Componente, CorPadrao, Etapa

ETAPAS = [("2EF", 1000), ("5EF", 500), ("9EF", 500), ("3EM", 500)]  # na ordem de exibição
COMPONENTES = [("LP", "Língua Portuguesa"), ("MT", "Matemática")]
# Padrões 1 a 4: --color-padrao-1..4 de revista/styles.css; o 5º é branco (D-064).
CORES = ["#F72628", "#FF8D43", "#B3CCFF", "#0ED3FF", "#FFFFFF"]


class Command(BaseCommand):
    help = "Cria ano, etapas, componentes e cores e nomes dos padrões. Idempotente: não altera o que já existe."

    def add_arguments(self, parser):
        parser.add_argument("--ano", type=int, required=True)

    @transaction.atomic
    def handle(self, *args, ano, **opcoes):
        # get_or_create (e não update_or_create): rodar de novo não desfaz edição feita no admin.
        ano_obj, novo = Ano.objects.get_or_create(ano=ano)
        criados = int(novo)
        for ordem, (codigo, escala_max) in enumerate(ETAPAS, start=1):
            criados += Etapa.objects.get_or_create(
                ano=ano_obj, codigo=codigo, defaults={"escala_max": escala_max, "ordem": ordem}
            )[1]
        for codigo, nome in COMPONENTES:
            criados += Componente.objects.get_or_create(ano=ano_obj, codigo=codigo, defaults={"nome": nome})[1]
        for padrao, cor in enumerate(CORES, start=1):
            criados += CorPadrao.objects.get_or_create(
                ano=ano_obj, padrao=padrao, defaults={"cor": cor, "nome": f"Padrão {padrao:02d}"}
            )[1]
        self.stdout.write(f"{ano}: {criados} registro(s) criado(s).")
