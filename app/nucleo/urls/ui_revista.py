"""Revistas e textos B (T20/T21): /ui/revista/<ano>/, rota ui_revista. Convenções: docs/telas/design-system.md.

Regra em `nucleo/revista.py` (a mesma do admin), "Validado" em `servicos/validacao.py`, zip em
`servicos/empacotar.py`. Permissões iguais às do admin de Revista:
- ver: `view_revista` ou `change_revista` (403);
- arquivos: `change_revista`; templates: + `change_revistafasciculo`; textos: + `add/change_revistasecao`;
  "Validado": + `validar_revista`. Revista ou projeto arquivado: só leitura, POST 403.
- bloqueio: a revista trava o projeto dela (D-140), pela peça comum `ui_bloqueio.com_bloqueio`.
A página tem quatro formulários (`acao`): arquivos, templates e validar recarregam (PRG); a seção
vai por HTMX e devolve o painel da seção + lista de seções, card "Validado" e mensagens (oob).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET, require_http_methods

from nucleo.models import Ano, Revista, RevistaFasciculo
from nucleo.revista import (
    FasciculoForm,
    RevistaForm,
    avisar_descartes,
    blocos_de_texto,
    diff,
    estado_validacao,
    form_de_textos,
    frase_descarte,
    gravar_arquivos,
    gravar_textos,
    ids_do_f2,
    nome,
)
from nucleo.servicos import resolver, validacao
from nucleo.servicos.empacotar import Pendente, zip_revista
from nucleo.ui_bloqueio import com_bloqueio, e_htmx

ERRO_FORM = "Nada foi gravado: corrija os erros marcados."
PERMS_TEXTO = ["nucleo.add_revistasecao", "nucleo.change_revistasecao"]


def pode_ver(user):
    return user.has_perm("nucleo.view_revista") or user.has_perm("nucleo.change_revista")


def arquivada(revista):
    return revista.arquivada_em is not None or revista.projeto.arquivado_em is not None


def _revista(ano, pk):
    return get_object_or_404(
        Revista.objects.select_related("projeto__parceiro_ano__parceiro", "projeto__ano", "componente", "ano", "validado_por"),
        pk=pk, ano__ano=ano,
    )  # fmt: skip


def _alvo(request, ano, pk):
    """Trava o projeto da revista (D-140); arquivada não trava (só leitura)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    request.revista = _revista(ano, pk)
    return None if arquivada(request.revista) else request.revista.projeto


@require_GET
@login_required(login_url="admin:login")
def lista(request, ano=None):
    """T20: revistas do ano com abrir, preview e zip."""
    if not pode_ver(request.user):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:
        return redirect("ui_revista", anos[0].ano) if anos else TemplateResponse(request, "ui/revista/lista.html", {"anos": anos})
    ano = get_object_or_404(Ano, ano=ano)
    revistas = (
        Revista.objects.filter(ano=ano)
        .select_related("projeto__parceiro_ano__parceiro", "componente")
        .order_by(F("arquivada_em").asc(nulls_first=True), "projeto__parceiro_ano__parceiro__nome", "componente__codigo")
    )  # ativas primeiro
    return TemplateResponse(request, "ui/revista/lista.html", {"ano": ano, "anos": anos, "secao": "revistas", "revistas": revistas})


def _secao_ativa(blocos, chave):
    """`F1:introducao` → (bloco, secao); sem chave ou chave velha: a primeira seção."""
    todas = [(b, s) for b in blocos for s in b.secoes]
    return next(((b, s) for b, s in todas if f"{b.rf.fasciculo}:{s.id}" == chave), todas[0] if todas else (None, None))


def _contexto_secao(request, blocos, chave, form=None):
    b, s = _secao_ativa(blocos, chave)
    if s is None:
        return {"bloco": None, "s": None}
    f = b.rf.fasciculo
    campo = nome("secao", f, s.id)
    return {
        "bloco": b, "s": s, "chave": f"{f}:{s.id}",
        "campo": campo, "campo_versao": nome("versao", f), "campo_manter": nome("manter", f, s.id),
        "campo_descartar": nome("descartar", f, s.id),
        "valor": form[campo].value() if form is not None and form.is_bound else s.corpo,
        "erros": form.errors.get(campo) if form is not None else None,
        "diff": diff(s.corpo, s.do_template) if s.desatualizada else "",
        "pode_textos": request.pode_gravar and request.user.has_perms(PERMS_TEXTO),
    }


def _forms_fasciculo(request, revista, dados=None):
    pode_descartar = request.user.has_perms(PERMS_TEXTO)
    forms_ = []
    for rf in RevistaFasciculo.objects.filter(revista=revista).select_related("template").order_by("fasciculo"):
        f = FasciculoForm(dados, instance=rf, prefix=rf.fasciculo)
        f.pode_descartar = pode_descartar  # o admin põe o mesmo por subclasse (FasciculoInline.get_formset)
        f.fields["template"].empty_label = "Sem template"
        f.fields["template"].widget.attrs.update({"class": "select", "id": f"template-{rf.fasciculo}"})
        f.copias = rf.revistasecao_set.count()
        f.frase = frase_descarte(f.copias) if f.copias else ""
        forms_.append(f)
    return forms_


def _validacao(request, revista):
    return {
        **estado_validacao(revista.pk),
        "pode": request.user.has_perm("nucleo.validar_revista") and request.bloqueio is not None,
    }


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_alvo, lambda u: u.has_perm("nucleo.change_revista"))
def revista(request, ano, pk):
    """T21. GET HTMX com `?secao=` devolve só o painel da seção (+ lista de seções, oob).
    POST pelo HTMX: erro e seção salva devolvem a página inteira e o form escolhe os pedaços
    (`hx-select`/`hx-select-oob`); o resto vai para a página de novo (HX-Redirect libera o bloqueio)."""
    revista = request.revista
    request.pode_gravar = request.pode_gravar and not arquivada(revista)
    if request.method == "POST":
        if arquivada(revista):
            raise PermissionDenied
        acao = request.POST.get("acao")
        if acao == "secao":
            return _salvar_secao(request, revista)
        if acao == "validar":
            return _validar(request, revista)
        if acao == "templates":
            return _salvar_templates(request, revista)
        if acao == "arquivos":
            return _salvar_arquivos(request, revista)
        raise Http404
    if e_htmx(request) and "secao" in request.GET:
        blocos = blocos_de_texto(revista)
        contexto = {"revista": revista, "blocos": blocos, "oob": True, **_contexto_secao(request, blocos, request.GET["secao"])}
        return TemplateResponse(request, "ui/parciais/revista_secao.html", contexto)
    return _pagina(request, revista)


def _pagina(request, revista, fasciculos=None, arquivos=None, chave=None, form=None):
    so_foto = arquivada(revista)
    contexto = {
        "revista": revista, "ano": revista.ano, "anos": list(Ano.objects.order_by("-ano")), "secao": "revistas",
        "arquivada": so_foto, "validacao": _validacao(request, revista),
        "pode_templates": request.pode_gravar and request.user.has_perm("nucleo.change_revistafasciculo"),
        "fasciculos": fasciculos or _forms_fasciculo(request, revista),
        "arquivos": arquivos or RevistaForm(instance=revista),
        "ids": ids_do_f2(revista) if revista.svg_f2 else None,
        "sem_template": list(RevistaFasciculo.objects.filter(revista=revista, template__isnull=True).order_by("fasciculo").values_list("fasciculo", flat=True)),
    }  # fmt: skip
    if so_foto:
        # Arquivada: as seções da foto de arquivamento (D-117), já renderizadas e escapadas.
        r = resolver.resolver(resolver.carregar(revista.pk))
        contexto["foto"] = [(f.upper(), r[f]["secoes"]) for f in ("f1", "f2") if r[f]["secoes"]]
    else:
        contexto["blocos"] = blocos = blocos_de_texto(revista)
        contexto.update(_contexto_secao(request, blocos, chave or request.GET.get("secao"), form))
    return TemplateResponse(request, "ui/revista/revista.html", contexto)


def _ir(request, revista):
    """Depois de gravar: volta à página (PRG). No HTMX, HX-Redirect (o com_bloqueio libera nos dois)."""
    url = reverse("ui_revista_editar", args=[revista.ano.ano, revista.pk])
    return HttpResponse(headers={"HX-Redirect": url}) if e_htmx(request) else redirect(url)


def _salvar_secao(request, revista):
    """Uma seção por envio (só os campos dela vêm no POST; os outros não mudam: `changed_data`)."""
    if not request.user.has_perms(PERMS_TEXTO):
        raise PermissionDenied
    form = form_de_textos(blocos_de_texto(revista))(request.POST, instance=revista)
    chave = request.POST.get("chave")
    if not form.is_valid():
        messages.error(request, ERRO_FORM)
        return _pagina(request, revista, chave=chave, form=form)
    if any(n.startswith(("secao__", "manter__", "descartar__")) for n in form.changed_data):  # versao__ do outro fascículo não vem
        gravar_textos(request, form)
    else:
        messages.info(request, "Nada a salvar: o texto está igual ao que abriu.")
    return _pagina(request, revista, chave=chave)  # 200: segue com o bloqueio desta aba


def _salvar_templates(request, revista):
    if not request.user.has_perm("nucleo.change_revistafasciculo"):
        raise PermissionDenied
    forms_ = _forms_fasciculo(request, revista, request.POST)
    validos = [f.is_valid() for f in forms_]  # valida todos, para mostrar todos os erros
    if not all(validos):
        messages.error(request, ERRO_FORM)
        return _pagina(request, revista, fasciculos=forms_)
    for f in forms_:
        if f.has_changed():
            f.save()
    avisar_descartes(request, forms_)
    messages.success(request, "Templates salvos.")
    return _ir(request, revista)


def _salvar_arquivos(request, revista):
    form = RevistaForm(request.POST, request.FILES, instance=revista)
    if not form.is_valid():
        messages.error(request, ERRO_FORM)
        return _pagina(request, revista, arquivos=form)
    if form.cleaned_data.get("arquivo_svg") or form.cleaned_data.get("arquivo_capa"):
        gravar_arquivos(request, revista, form.cleaned_data)
        messages.success(request, "Arquivos salvos.")
    else:
        messages.info(request, "Nada a salvar: escolha o SVG ou a capa antes de salvar.")
    return _ir(request, revista)


def _validar(request, revista):
    """Botão "Validado" (D-074, D-089): o hash que a página mostrou; o bloqueio já foi conferido."""
    if not request.user.has_perm("nucleo.validar_revista"):
        raise PermissionDenied
    motivo = validacao.validar(revista.pk, request.POST.get("hash_visto", ""), request.user)
    if motivo:
        messages.error(request, f"Não validada: {motivo.rstrip('.')}.")
    else:
        messages.success(request, "Revista validada.")
    return _ir(request, revista)


@require_GET
@login_required(login_url="admin:login")
def zip_(request, ano, pk):
    """Zip da revista (a action "Baixar zip" do admin): recusa com pendências (D-112)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    revista = _revista(ano, pk)
    try:
        nome_, dados = zip_revista(resolver.carregar(revista.pk))
    except Pendente as e:
        messages.error(request, f"Zip recusado. Pendências: {e}")
        return redirect("ui_revista", ano) if request.GET.get("voltar") == "lista" else redirect("ui_revista_editar", ano, pk)
    resposta = HttpResponse(dados, content_type="application/zip")
    resposta["Content-Disposition"] = f'attachment; filename="{nome_}"'
    return resposta


urlpatterns = [
    path("", lista, name="ui_revista_inicio"),
    path("<int:ano>/", lista, name="ui_revista"),
    path("<int:ano>/<int:pk>/", revista, name="ui_revista_editar"),
    path("<int:ano>/<int:pk>/zip/", zip_, name="ui_revista_zip"),
]
