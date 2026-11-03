"""Padrões do ano (CorPadrao): impacto de mudar nome/cor (T07, D-076, D-175).

Comum ao admin (`admin/cadastro.py`, `CorPadraoAdmin`) e à tela B (`urls/ui_anos.py`): a tela B
não pode importar do admin (import circular).
"""

from django import forms
from django.utils.functional import cached_property
from django.utils.html import format_html

from nucleo.matriz import ImpactoForm
from nucleo.models import ProjetoCor, Revista
from nucleo.servicos import resolver, validacao
from nucleo.servicos.impacto import nomes  # noqa: F401 (admin/cadastro e ui_anos importam daqui)

CAMPOS_DO_HASH = {"nome", "cor"}


def revistas_afetadas_padrao(cor_padrao, campos):
    """(afetadas, perdem o "Validado") ao mudar `campos` ⊆ {"nome", "cor"} do padrão do ano.

    Afetada: revista ativa do ano que tem o padrão N em alguma etapa e que não sobrescreve no
    projeto o que muda (`pdNN` para o nome, `ProjetoCor` N para a cor). Arquivada lê a foto.
    """
    n, pd = cor_padrao.padrao, f"pd{cor_padrao.padrao:02d}"
    com_cor = set(ProjetoCor.objects.filter(padrao=n, projeto__ano_id=cor_padrao.ano_id).values_list("projeto_id", flat=True))
    afetadas, perdem = [], []
    revistas = Revista.objects.filter(ano_id=cor_padrao.ano_id, arquivada_em__isnull=True).select_related(
        "projeto__parceiro_ano__parceiro", "projeto__ano", "componente"
    ).order_by("projeto__parceiro_ano__parceiro__nome", "componente__codigo")
    for r in revistas:
        if not (("nome" in campos and not getattr(r.projeto, pd).strip())
                or ("cor" in campos and r.projeto_id not in com_cor)):
            continue  # fmt: skip
        # ponytail: resolve cada candidata no GET e no POST; guardar na sessão se ficar lento.
        resolvido = resolver.resolver(r)
        if not any(len(d["padroes"]) >= n for d in resolvido["f1"]["dados"].values()):
            continue
        afetadas.append(r)
        if validacao.validada(r, resolver.hash_validado(r, resolvido)):
            perdem.append(r)
    return afetadas, perdem


class PadraoImpactoForm(ImpactoForm):
    """Confirmação só quando nome/cor mudam (no GET, o pior caso: os dois). `impacto` vem do admin."""

    impacto = None  # função(campos) -> (afetadas, perdem); None na inclusão

    @cached_property
    def resultado(self):
        campos = CAMPOS_DO_HASH & set(self.changed_data) if self.is_bound else CAMPOS_DO_HASH
        return self.impacto(campos) if self.impacto and campos else ([], [])

    @property
    def afetadas(self):
        return len(self.resultado[0])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        afetadas, perdem = self.resultado
        if afetadas and perdem and not self.modal:
            campo = self.fields["confirmar_impacto"]
            campo.label += f"; {len(perdem)} perdem o “Validado”"
            campo.help_text = format_html(
                "Perdem o “Validado”: {}.{}", nomes(perdem),
                " As demais afetadas ainda não estavam validadas." if len(afetadas) > len(perdem) else "",
            )  # fmt: skip
        # changed_data criou os BoundFields com o rótulo antigo (o BoundField copia label e help_text).
        self._bound_fields_cache.clear()

    def clean(self):
        dados = super(ImpactoForm, self).clean()
        if not self.modal and self.afetadas and not dados.get("confirmar_impacto"):
            p, ano = self.instance.padrao, self.instance.ano.ano
            raise forms.ValidationError(
                f"Não salvo: mudar o nome ou a cor do Padrão {p} de {ano} afeta {self.afetadas} revista(s) "
                f"ativa(s) (as que não sobrescrevem pd{p:02d} ou a cor no projeto). "
                "Confira a lista, marque a confirmação e salve de novo."
            )
        return dados
