from django.conf import settings
from django.db import models
from django.db.models import F, Func, Q
from django.db.models.lookups import Exact

from nucleo.db import max_len

from .matriz import MatrizEtapaCC
from .projeto import Projeto
from .texto import Template

ALVOS = ("matriz_etapa_cc", "projeto", "template")


class Bloqueio(models.Model):
    """Trava de escrita com exatamente um alvo; expira em 30 s (D-081, D-109).

    Sem histórico. Apagar o alvo apaga a trava (CASCADE): trava é efêmera.
    """

    matriz_etapa_cc = models.ForeignKey(MatrizEtapaCC, on_delete=models.CASCADE, null=True, blank=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(Template, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sessao_edicao = models.TextField()  # aba do navegador
    expira_em = models.DateTimeField()

    class Meta:
        db_table = "bloqueio"
        constraints = [
            models.CheckConstraint(
                condition=Exact(
                    Func(*map(F, ALVOS), function="num_nonnulls", output_field=models.IntegerField()),
                    1,
                ),
                name="bloqueio_um_alvo",
            ),
            # Parciais para o INSERT … ON CONFLICT (alvo) WHERE … da aquisição.
            *[
                models.UniqueConstraint(
                    fields=[a], condition=Q(**{f"{a}__isnull": False}), name=f"bloqueio_{a}_uniq"
                )
                for a in ALVOS
            ],
            max_len("bloqueio", "sessao_edicao", 100),
        ]
