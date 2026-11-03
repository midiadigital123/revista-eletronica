"""Revista e textos B (T21): /ui/revista/<ano>/<pk>/. A lista do ano (T20) virou a aba Lista de Projetos (U7a). Convenções: docs/telas/design-system.md.

Regra em `nucleo/revista.py` (a mesma do admin), "Validado" em `servicos/validacao.py`, zip em
`servicos/empacotar.py`. Permissões iguais às do admin de Revista:
- ver: `view_revista` ou `change_revista` (403);
- arquivos: `change_revista`; templates: + `change_revistafasciculo`; textos: + `add/change_revistasecao`;
  "Validado": + `validar_revista`. Revista ou projeto arquivado: só leitura, POST 403.
- bloqueio: a revista trava o projeto dela (D-140), pela peça comum `ui_bloqueio.com_bloqueio`.
Página em duas colunas (U8b): templates, arquivos e textos à esquerda; a coluna Situação (a única
lista de pendências, com o "Validar revista") fixa à direita. Envios (`acao`):
- `templates` e `arquivos`: autosave (protocolo de `ui_autosave`, `?acao=` na URL), um campo por vez,
  com o modal de impacto (U2); a resposta 200 traz em `trocar` o HTML novo das partes afetadas.
- `secao`: HTMX, devolve o painel da seção + lista de seções, Situação e mensagens (oob).
- `validar`: HTMX com HX-Redirect.
"""

import hashlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.db.models import F
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET, require_http_methods

from nucleo.contexto import ano_da_sessao
from nucleo.models import Ano, Revista, RevistaFasciculo
from nucleo.revista import (
    FasciculoForm,
    RevistaForm,
    blocos_de_texto,
    diff,
    estado_validacao,
    form_de_textos,
    frase_descarte,
    gravar_textos,
    ids_do_f2,
    nome,
)
from nucleo.servicos import arquivos, resolver, validacao
from nucleo.servicos.empacotar import Pendente, zip_revista
from nucleo.ui_autosave import erros, quer_json, responder_campo
from nucleo.ui_bloqueio import com_bloqueio, e_htmx
from nucleo.urls.painel import link as link_pendencia

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
    """A lista antiga (T20) virou a aba Lista de Projetos (U7a): GET redireciona (302)."""
    ano = ano or getattr(ano_da_sessao(request), "ano", None)
    return redirect("ui_projeto_lista", ano) if ano else redirect("ui_projeto_inicio")


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
        forms_.append(f)
    return forms_


# Coluna Situação (U8b): cada passo junta as pendências do resolver pelo código; cada uma aparece uma
# vez só, como link para o lugar que resolve. Código novo cai em "Outras pendências".
PASSOS = (
    ("Matriz e cortes", ("matriz", "corte_sem_matriz", "corte_invalido")),
    ("Template do F1", ("template_f1",)),
    ("Template do F2", ("template_f2",)),
    ("SVG do F2", ("svg", "ids_svg")),
    ("Capa", ("capa",)),
    ("Dados do projeto", ("variaveis", "nome_projeto")),
)


def _situacao(revista, pendencias):
    projeto = reverse("ui_projeto", args=[revista.projeto_id])
    links = {
        "matriz": f"{projeto}?aba=matriz", "corte_sem_matriz": link_pendencia("corte_sem_matriz", revista),  # U7b; a etapa que falta: a matriz
        "corte_invalido": f"{projeto}?aba=cortes",
        "template_f1": "#templates", "template_f2": "#templates",
        "svg": "#arquivos", "ids_svg": "#arquivos", "capa": "#arquivos",
        "variaveis": f"{projeto}#variaveis", "nome_projeto": f"{projeto}#nome",
    }  # fmt: skip
    passos = [{"rotulo": r, "pendencias": [p for p in pendencias if p.codigo in codigos]} for r, codigos in PASSOS]
    conhecidos = {c for _, codigos in PASSOS for c in codigos}
    outras = [p for p in pendencias if p.codigo not in conhecidos]
    if outras:
        passos.append({"rotulo": "Outras pendências", "pendencias": outras})
    for passo in passos:
        passo["pendencias"] = [{"mensagem": p.mensagem, "url": links.get(p.codigo)} for p in passo["pendencias"]]
    return {"passos": passos, "prontos": sum(not p["pendencias"] for p in passos)}


def _validacao(request, revista):
    estado = estado_validacao(revista.pk)
    return {
        **estado, **_situacao(revista, estado["pendencias"]),
        "pode": request.user.has_perm("nucleo.validar_revista") and request.bloqueio is not None,
    }  # fmt: skip


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
        acao = request.POST.get("acao") or request.GET.get("acao")  # autosave: ?acao= na data-url
        if acao == "secao":
            return _salvar_secao(request, revista)
        if acao == "validar":
            return _validar(request, revista)
        if acao == "templates" and quer_json(request):
            return _template(request, revista)
        if acao == "arquivos" and quer_json(request):
            return _arquivo(request, revista)
        return HttpResponseBadRequest("Ação desconhecida. O nome do projeto se edita no Projeto (U5).")
    if e_htmx(request) and "secao" in request.GET:
        blocos = blocos_de_texto(revista)
        contexto = {"revista": revista, "blocos": blocos, "oob": True, **_contexto_secao(request, blocos, request.GET["secao"])}
        return TemplateResponse(request, "ui/parciais/revista_secao.html", contexto)
    return _pagina(request, revista)


def _tamanho(caminho):
    try:
        return default_storage.size(caminho) if caminho else None
    except OSError:  # caminho sem arquivo (dados de teste, storage limpo)
        return None


def _contexto(request, revista, chave=None, form=None):
    so_foto = arquivada(revista)
    contexto = {
        "revista": revista, "ano": revista.ano, "anos": list(Ano.objects.order_by("-ano")), "secao": "revistas",
        "arquivada": so_foto, "validacao": _validacao(request, revista),
        "pode_templates": request.pode_gravar and request.user.has_perm("nucleo.change_revistafasciculo"),
        "fasciculos": _forms_fasciculo(request, revista),
        "ids": ids_do_f2(revista) if revista.svg_f2 else None,
        "svg_tamanho": _tamanho(revista.svg_f2), "capa_tamanho": _tamanho(revista.capa),
        "svg_max": arquivos.SVG_MAX, "capa_max": arquivos.CAPA_MAX,
        # U5: o nome do projeto se edita só no Projeto; aqui fica o link "Editar no projeto".
        "pode_nome": request.pode_gravar and request.user.has_perm("nucleo.change_projeto"),
        "sem_template": RevistaFasciculo.objects.filter(revista=revista, template__isnull=True).exists(),
    }  # fmt: skip
    if so_foto:
        # Arquivada: as seções da foto de arquivamento (D-117), já renderizadas e escapadas.
        r = resolver.resolver(resolver.carregar(revista.pk))
        contexto["foto"] = [(f.upper(), r[f]["secoes"]) for f in ("f1", "f2") if r[f]["secoes"]]
    else:
        contexto["blocos"] = blocos = blocos_de_texto(revista)
        contexto.update(_contexto_secao(request, blocos, chave or request.GET.get("secao"), form))
    return contexto


def _pagina(request, revista, chave=None, form=None):
    return TemplateResponse(request, "ui/revista/revista.html", _contexto(request, revista, chave, form))


def _pedacos(request, revista, *nomes):
    """HTML novo das partes da página (`revista_<nome>.html`, raiz com id=<nome>) para o autosave
    trocar depois de gravar: o que a gravação muda fora do campo (Situação, textos, arquivos)."""
    contexto = _contexto(request, revista)
    return {n: render_to_string(f"ui/parciais/revista_{n}.html", contexto, request=request) for n in nomes}


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


def _template(request, revista):
    """Autosave do select de template de um fascículo (`campo` = `F1-template`). Trocar com cópias de
    seção pede o modal com a frase "descartar N cópia(s)" (D-171), que volta no campo `confirmacao`."""
    if not request.user.has_perm("nucleo.change_revistafasciculo"):
        raise PermissionDenied
    campo = request.POST.get("campo", "")
    f = campo.removesuffix("-template")
    rf = RevistaFasciculo.objects.filter(revista=revista, fasciculo=f).first() if f != campo else None
    if rf is None:
        return erros(["Este campo não pode ser alterado aqui. Recarregue a página."])
    copias = rf.revistasecao_set.count()
    frase = frase_descarte(copias) if copias else ""
    # Sem confirmar, a frase vai certa só para validar e simular; o modal pede a frase de verdade.
    confirmacao = request.POST.get("confirmacao", "") if request.POST.get("confirmar_impacto") else frase
    form = FasciculoForm({campo: request.POST.get("valor", ""), f"{f}-confirmacao": confirmacao}, instance=rf, prefix=f)
    form.pode_descartar = request.user.has_perms(PERMS_TEXTO)
    form.fields["template"].label = ""  # o erro já diz o que é
    modal = {"copias": form.descartar, "frase": frase, "fasciculo": f} if form.is_valid() and form.descartar else None
    return responder_campo(
        request, form=form, simular=lambda _: form.save(), modal=modal, titulo=f"Trocar o template do {f}",
        gravar=lambda _: form.save() and {"trocar": _pedacos(request, revista, "textos", "situacao")},
        revistas=lambda: [revista],
    )  # fmt: skip


def _arquivo(request, revista):
    """Autosave de um arquivo (`campo` = `arquivo_svg` ou `arquivo_capa`, o arquivo em `valor`): mesma
    validação do admin (RevistaForm). O impacto simula só o sha256 (é o que entra no hash, D-118),
    sem gravar arquivo à toa."""
    campo = request.POST.get("campo", "")
    if campo not in ("arquivo_svg", "arquivo_capa") or "valor" not in request.FILES:
        return erros(["Escolha o arquivo do SVG ou da capa e envie de novo."])
    form = RevistaForm({}, {campo: request.FILES["valor"]}, instance=revista)
    form.fields[campo].label = ""  # "SVG maior que 3 MB: …" já diz qual

    def simular(dados):
        if campo == "arquivo_svg":
            limpo, ids = arquivos.sanitizar_svg(dados[campo])
            Revista.objects.filter(pk=revista.pk).update(svg_sha256=hashlib.sha256(limpo).hexdigest(), svg_ids=ids)
        else:
            Revista.objects.filter(pk=revista.pk).update(capa_sha256=hashlib.sha256(dados[campo]).hexdigest())

    def gravar(dados):
        (arquivos.receber_svg if campo == "arquivo_svg" else arquivos.receber_capa)(revista, dados[campo])
        return {"trocar": _pedacos(request, revista, "arquivos", "situacao")}

    titulo = "Trocar o SVG do F2" if campo == "arquivo_svg" else "Trocar a capa"
    return responder_campo(request, form=form, simular=simular, gravar=gravar, revistas=lambda: [revista], titulo=titulo)


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
        return redirect("ui_projeto_lista", ano) if request.GET.get("voltar") == "lista" else redirect("ui_revista_editar", ano, pk)
    resposta = HttpResponse(dados, content_type="application/zip")
    resposta["Content-Disposition"] = f'attachment; filename="{nome_}"'
    return resposta


urlpatterns = [
    path("", lista, name="ui_revista_inicio"),
    path("<int:ano>/", lista, name="ui_revista"),
    path("<int:ano>/<int:pk>/", revista, name="ui_revista_editar"),
    path("<int:ano>/<int:pk>/zip/", zip_, name="ui_revista_zip"),
]
