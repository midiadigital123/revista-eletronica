"""Apaga do banco de dev o que os specs do Playwright criam e não desfazem (D-224).

Parceiros "E2E …" (com parceiro-ano, cortes, projetos e revistas que a cascata criou), matrizes e
templates "E2E …", e só os que o usuário de teste criou (o registro de criação no histórico é dele). O
`globalTeardown` do Playwright (app/e2e/limpar.ts) roda este comando no fim de toda execução: spec
que falha no meio também deixa de acumular lixo. Só com DEBUG.

    python manage.py limpar_e2e [--usuario e2e] [--simular]
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nucleo.models import Corte, FotoRevista, Matriz, Parceiro, ParceiroAno, Projeto, ProjetoCor, ProjetoPasso, Revista, Template
from nucleo.servicos.exclusao import EmUso, _apagar, excluir

PREFIXO = "E2E "


def criados_por(modelo, usuario):
    """Os "E2E …" de `modelo` cujo registro de criação no histórico (history_type "+") é de `usuario`."""
    criados = modelo.history.filter(history_type="+", history_user=usuario).values("id")
    return modelo.objects.filter(nome__startswith=PREFIXO, pk__in=criados)


def dependentes(parceiros):
    """Folhas primeiro, como exclusao.ORDEM_ANO, filtrado pelos parceiros."""
    pas = ParceiroAno.objects.filter(parceiro__in=parceiros)
    return [
        (FotoRevista, {"revista__projeto__parceiro_ano__in": pas}), (Revista, {"projeto__parceiro_ano__in": pas}),
        (ProjetoPasso, {"projeto__parceiro_ano__in": pas}), (ProjetoCor, {"projeto__parceiro_ano__in": pas}),
        (Projeto, {"parceiro_ano__in": pas}), (Corte, {"parceiro_ano__in": pas}), (ParceiroAno, {"pk__in": pas}),
    ]  # fmt: skip


class Command(BaseCommand):
    help = 'Apaga parceiros, matrizes e templates "E2E …" que o usuário de teste criou (só com DEBUG).'

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="e2e", help="login do E2E (padrão: e2e)")
        parser.add_argument("--simular", action="store_true", help="só lista o que sairia")

    def handle(self, *args, usuario, simular, **opcoes):
        if not settings.DEBUG:
            raise CommandError("limpar_e2e só roda com DEBUG (desenvolvimento).")
        u = get_user_model().objects.filter(username=usuario).first()
        if u is None:
            raise CommandError(f"Usuário {usuario!r} não existe.")
        parceiros = list(criados_por(Parceiro, u))
        livres = [*criados_por(Matriz, u), *criados_por(Template, u)]  # depois dos parceiros que os usam
        if simular:
            self.stdout.write(f"Sairiam: {', '.join(map(str, parceiros + livres)) or '-'}")
            return
        with transaction.atomic():
            for modelo, filtro in dependentes(parceiros):
                _apagar(modelo.objects.filter(**filtro), u)
            _apagar(Parceiro.objects.filter(pk__in=[p.pk for p in parceiros]), u)
        apagados, ficaram = [p.nome for p in parceiros], []
        for obj in livres:  # pela regra da tela (D-205, D-207): sai com as partes, se nada o usa
            try:
                excluir(obj, u)
                apagados.append(obj.nome)
            except EmUso:  # ex.: spec que parou com o template ainda escolhido numa revista real
                ficaram.append(obj.nome)
        self.stdout.write(f"Apagados: {', '.join(apagados) or '-'}")
        if ficaram:
            self.stderr.write(f"Em uso, ficaram: {', '.join(ficaram)}. Tire o uso (template da revista, matriz do parceiro) e rode de novo.")
