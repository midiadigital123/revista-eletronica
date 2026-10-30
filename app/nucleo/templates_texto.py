"""Regra dos templates de texto comum ao admin (`admin/templates.py`) e à tela B (`urls/ui_templates.py`).

D-099, D-102, D-118, D-123, D-162, D-163. Editar o texto = nova `TemplateVersao` (só INSERT):
- `com_uso`: a lista com versão atual e "usado por N (M com cópia)".
- `impacto`: o que a versão nova muda em cada revista ativa (tela de impacto).
- `assinatura` / `assinar` / `ler_assinatura`: a tela de impacto assina hash do texto + versão-base
  (30 min); o "Confirmar" só grava se bater.
- `criar_versao`: numeração serializada (duplo "Confirmar" não duplica a versão).
- `previa`: HTML do preview ao vivo (variáveis sem valor, coloridas) + erros de `texto.validar`.
"""

import hashlib

from django.core import signing
from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, IntegerField, Max, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from nucleo import texto
from nucleo.models import FotoRevista, RevistaFasciculo, Template, TemplateVersao
from nucleo.models.revista import Motivo
from nucleo.models.texto import Fasciculo
from nucleo.servicos.arquivos import ids_faltando
from nucleo.servicos.resolver import versao_atual

ASSINATURA = "_impacto"  # hidden da tela de impacto
SAL = "nucleo.admin.templates.impacto"
VALIDADE = 30 * 60  # segundos; a tela fica aberta sob o bloqueio, que se renova


def assinatura(novo, atual):
    """Conteúdo que a tela de impacto assina: hash do texto novo + número da versão-base."""
    return {"h": hashlib.sha256(novo.encode()).hexdigest(), "base": atual.numero if atual else 0}


def assinar(conteudo):
    return signing.dumps(conteudo, salt=SAL)


def ler_assinatura(post):
    """Conteúdo assinado pela tela de impacto, ou None (adulterado, ausente ou expirado)."""
    try:
        return signing.loads(post.get(ASSINATURA, ""), salt=SAL, max_age=VALIDADE)
    except signing.BadSignature:  # SignatureExpired é subclasse
        return None


def _contar(qs):
    """Subquery COUNT por template (sem JOIN na lista, que multiplicaria as linhas)."""
    sub = qs.filter(template=OuterRef("pk")).order_by().values("template")
    return Coalesce(Subquery(sub.annotate(n=Count("pk", distinct=True)).values("n")), 0)


def com_uso(qs):
    """Templates com `n_usado` (fascículos de revistas ativas), `n_copia` (desses, com cópia de
    seção) e `n_versao` (número da versão atual)."""
    ativas = RevistaFasciculo.objects.filter(revista__arquivada_em__isnull=True)
    versao = TemplateVersao.objects.filter(template=OuterRef("pk")).order_by().values("template")
    return qs.annotate(
        n_usado=_contar(ativas),
        n_copia=_contar(ativas.filter(revistasecao__isnull=False)),
        n_versao=Subquery(versao.annotate(m=Max("numero")).values("m"), output_field=IntegerField()),
    )


def impacto(template, novo):
    """Revistas ativas que usam o template, com o que muda para cada uma (D-099, D-118)."""
    novas = list(texto.secoes(novo))
    fascs = (
        RevistaFasciculo.objects.filter(template=template, revista__arquivada_em__isnull=True)
        .select_related("revista__projeto", "revista__componente")
        .annotate(impresso=Exists(FotoRevista.objects.filter(revista=OuterRef("revista"), motivo=Motivo.IMPRESSO)))
        .prefetch_related("revistasecao_set")
        .order_by("revista__projeto__nome", "revista__componente__codigo")
    )
    saida = []
    for rf in fascs:
        copias = sorted(c.secao for c in rf.revistasecao_set.all())
        faltando = []
        if template.fasciculo == "F2" and rf.revista.svg_f2:
            # Seções efetivas com o texto novo: as do template + as cópias (órfãs continuam).
            faltando = ids_faltando(rf.revista, novas + [c for c in copias if c not in novas])
        saida.append({"revista": rf.revista, "copias": copias, "impresso": rf.impresso, "ids_faltando": faltando})
    return saida


def criar_versao(template, novo, usuario):
    """Grava a versão N+1 com `novo`; devolve o número, ou None se o texto já é o da versão atual.
    Chamar dentro de uma transação: a trava do template serializa a numeração (duplo "Confirmar"
    da mesma aba passa junto pelo FOR SHARE do bloqueio) e a versão atual é relida sob ela."""
    Template.objects.select_for_update().get(pk=template.pk)
    atual = versao_atual(template.pk)
    if atual is not None and atual.texto == novo:
        return None
    numero = atual.numero + 1 if atual else 1
    TemplateVersao.objects.create(template=template, numero=numero, texto=novo, criada_por=usuario)
    return numero


def previa(corpo, fasciculo=None, so_corpo=False):
    """(html, erros) do preview: `texto.renderizar` sem valores (toda variável sai como
    `<span class="variavel-vazia">{{nome}}</span>`). Valida o documento do fascículo ou, com
    `so_corpo` (seção da revista: "## id\\ntítulo\\n\\n" + corpo), só o corpo."""
    corpo = corpo.replace("\r\n", "\n")
    erros = []
    try:
        if fasciculo in Fasciculo.values:
            texto.validar(corpo, fasciculo)
        elif so_corpo:
            texto.validar_corpo(corpo.split("\n\n", 1)[-1])
    except ValidationError as e:
        erros = e.messages
    # renderizar/renderizar_texto_puro já escapam; o id da seção é escapado pelo format_html.
    html = format_html_join(
        "",
        '<section class="secao"><p class="secao-id">## {}</p><h3>{}</h3>{}</section>',
        (
            (id_, mark_safe(texto.renderizar_texto_puro(titulo, {})), mark_safe(texto.renderizar(c, {})))
            for id_, (titulo, c) in texto.secoes(corpo).items()
        ),
    )
    return html, erros
