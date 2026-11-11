"""Revista e textos B (T21): /ui/revista/<ano>/<pk>/. A lista do ano (T20) virou a aba Lista de Projetos (U7a). Convenções: docs/telas/design-system.md.

Regra em `nucleo/revista.py` (a mesma do admin), "Validado" em `servicos/validacao.py`, zip em
`servicos/empacotar.py`. Permissões iguais às do admin de Revista:
- ver: `view_revista` ou `change_revista` (403);
- arquivos: `change_revista`; templates: + `change_revistafasciculo`; textos: + `add/change_revistasecao`;
  "Validado": + `validar_revista`. Revista ou projeto arquivado: só leitura, POST 403.
- bloqueio: a revista trava o projeto dela (D-140), pela peça comum `ui_bloqueio.com_bloqueio`.
Página em duas colunas (U8b): templates, infográficos, capa e textos à esquerda; a coluna Situação (a única
lista de pendências, com o "Validar revista") fixa à direita. Envios (`acao`):
- `templates` e `arquivos`: autosave (protocolo de `ui_autosave`, `?acao=` na URL), um campo por vez,
  com o modal de impacto (U2); a resposta 200 traz em `trocar` o HTML novo das partes afetadas.
- `texto`: autosave do texto de uma seção (`?acao=texto&secao=F1:id`), mesmo protocolo.
- `infografico`: autosave de um campo do infográfico do F2 (regra em `nucleo/infografico.py`).
- `secao`: HTMX, botões "Manter meu texto" e "Descartar cópia" (e o envio sem JS); devolve o painel
  da seção + lista de seções, Situação e mensagens (oob).
- `validar`: HTMX com HX-Redirect.
"""

import hashlib
from pathlib import PurePosixPath

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
from nucleo.infografico import familia, form_do_campo
from nucleo.models import Ano, Revista, RevistaFasciculo, RevistaInfografico
from nucleo.models.revista import EtapaReferencial, Marca
from nucleo.revista import (
    FasciculoForm,
    RevistaForm,
    blocos_de_texto,
    diff,
    estado_validacao,
    form_de_textos,
    frase_descarte,
    gravar_textos,
    nome,
)
from nucleo.servicos import arquivos, resolver, validacao
from nucleo.servicos.empacotar import Pendente, zip_revista
from nucleo.ui_autosave import Conflito, erros, quer_json, responder_campo
from nucleo.ui_bloqueio import com_bloqueio, e_htmx
from nucleo.urls.painel import link as link_pendencia

ERRO_FORM = "Nada foi gravado: corrija os erros marcados."
PERMS_TEXTO = ["nucleo.add_revistasecao", "nucleo.change_revistasecao"]
# Campo `inf-<pk>-<família>-…`: a família diz a tabela; o resto é do RevistaInfografico (só `change`).
PERMS_INFOGRAFICO = {
    "etapa": ["nucleo.add_revistainfograficoetapa", "nucleo.change_revistainfograficoetapa"],
    "item": ["nucleo.add_revistainfograficoitem", "nucleo.change_revistainfograficoitem"],
}
PASSOS_INFOGRAFICO = (("habilidades", "Habilidades"), ("progressao", "Progressão"), ("tarefas", "Tarefas"))  # PASSOS_DESLIGAVEIS
PERMS_INFOGRAFICO_TODAS = ["nucleo.change_revistainfografico", *PERMS_INFOGRAFICO["etapa"], *PERMS_INFOGRAFICO["item"]]


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
@login_required
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
    ("Infográficos", ("infografico",)),
    ("Capa", ("capa",)),
    ("Dados do projeto", ("variaveis", "nome_projeto")),
)


def _situacao(revista, pendencias):
    projeto = reverse("ui_projeto", args=[revista.projeto_id])
    links = {
        "matriz": f"{projeto}?aba=matriz", "corte_sem_matriz": link_pendencia("corte_sem_matriz", revista),  # U7b; a etapa que falta: a matriz
        "corte_invalido": f"{projeto}?aba=cortes",
        "template_f1": "#templates", "template_f2": "#templates",
        "infografico": "#infograficos", "capa": "#arquivos",
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
@login_required
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
        if acao == "texto" and quer_json(request):
            return _texto(request, revista)
        if acao == "templates" and quer_json(request):
            return _template(request, revista)
        if acao == "arquivos" and quer_json(request):
            return _arquivo(request, revista)
        if acao == "infografico" and quer_json(request):
            return _infografico(request, revista)
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
        "capa_tamanho": _tamanho(revista.capa), "capa_max": arquivos.CAPA_MAX,
        "infograficos": _infograficos(revista), "item_max": arquivos.ITEM_MAX, "passos_infografico": PASSOS_INFOGRAFICO,
        "marcas": Marca.choices, "etapas_referencial": EtapaReferencial.choices,
        "pode_infograficos": request.pode_gravar and request.user.has_perms(PERMS_INFOGRAFICO_TODAS),
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
        contexto["textos_template"] = _textos_template(blocos)
        contexto.update(_contexto_secao(request, blocos, chave or request.GET.get("secao"), form))
    return contexto


# Seções do template F2 que cada passo do infográfico usa (servicos/f2.gerar e html.contexto_pagina),
# mostradas só para leitura no cartão (D-258).
SECOES_DO_PASSO = {
    "descritor": ("passo-descritor", "dlg-descritor"),
    "habilidades": ("passo-habilidades",),
    "progressao": ("passo-progressao",),
    "tarefas": ("passo-tarefas", "dlg-tarefas", "tarefas-fechamento"),
}


def _textos_template(blocos):
    """{passo: [Secao efetiva do F2]}; vazio sem template F2. Vale para os dois infográficos da revista."""
    secoes = {s.id: s for b in blocos if b.rf.fasciculo == "F2" for s in b.secoes}
    return {passo: [secoes[i] for i in ids if i in secoes] for passo, ids in SECOES_DO_PASSO.items()}


def _infograficos(revista):
    """Cartões do passo Infográficos: os ativos com as 12 etapas do referencial e os 4 itens, cada um
    com a linha gravada ou None (campos vazios; a linha nasce na 1ª gravação)."""
    # ponytail: "alfa" < "outras" na ordem alfabética, que é a ordem dos cartões; um tipo novo pede ordem explícita.
    infos = RevistaInfografico.objects.filter(revista=revista, arquivado_em__isnull=True).order_by("tipo")
    infos = list(infos.prefetch_related("revistainfograficoetapa_set", "revistainfograficoitem_set"))
    for inf in infos:
        etapas = {e.etapa: e for e in inf.revistainfograficoetapa_set.all()}
        itens = {i.posicao: i for i in inf.revistainfograficoitem_set.all()}
        for i in itens.values():
            i.nome_imagem = PurePosixPath(i.imagem).name if i.imagem else ""
        inf.grade = [(valor, rotulo, etapas.get(valor)) for valor, rotulo in EtapaReferencial.choices]
        inf.itens = [(p, itens.get(p)) for p in range(1, 5)]
    return infos


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
    dados = request.POST.copy()
    if any(k.startswith("descartar__") for k in dados):
        # "Descartar cópia" (botão): o texto da tela não conta; senão viraria "editou e descartou".
        for k in [k for k in dados if k.startswith(("secao__", "initial-secao__"))]:
            del dados[k]
    form = form_de_textos(blocos_de_texto(revista))(dados, instance=revista)
    chave = request.POST.get("chave")
    if not form.is_valid():
        messages.error(request, ERRO_FORM)
        return _pagina(request, revista, chave=chave, form=form)
    if any(n.startswith(("secao__", "manter__", "descartar__")) for n in form.changed_data):  # versao__ do outro fascículo não vem
        gravar_textos(request, form)
    else:
        messages.info(request, "Nada a salvar: o texto está igual ao que abriu.")
    return _pagina(request, revista, chave=chave)  # 200: segue com o bloqueio desta aba


def _texto(request, revista):
    """Autosave do texto de uma seção (`campo` = `secao__F1__introducao`; vêm junto a versão vista e o
    `original`, que vira o valor inicial do form: só o que mudou grava). Mesma regra do "Salvar" do
    admin (`gravar_textos`): a primeira mudança cria a cópia. A resposta troca a lista de seções, a
    Situação e o estado da seção (selo, aviso, Descartar)."""
    if not request.user.has_perms(PERMS_TEXTO):
        raise PermissionDenied
    campo = request.POST.get("campo", "")
    blocos = blocos_de_texto(revista)
    bloco = next((b for b in blocos for s in b.secoes if nome("secao", b.rf.fasciculo, s.id) == campo), None)
    if bloco is None:
        return erros(["Esta seção saiu do template. Recarregue a página."])
    versao = nome("versao", bloco.rf.fasciculo)
    dados = {campo: request.POST.get("valor", ""), f"initial-{campo}": request.POST.get("original", ""), versao: request.POST.get(versao, "")}
    form = form_de_textos(blocos)(dados, instance=revista)
    form.fields[campo].label = ""  # o erro já é do campo

    def gravar_quieto(_):
        # As mensagens do admin ("Textos do F1 salvos") não servem aqui: o status do autosave diz.
        # Aviso de não salvo (template trocado, revista arquivada) vira 409, desfazendo a gravação.
        gravar_textos(request, form)
        avisos = [str(m) for m in messages.get_messages(request) if m.level >= messages.WARNING]
        if avisos:
            raise Conflito(" ".join(avisos))

    def gravar(dados):
        gravar_quieto(dados)
        contexto = _contexto(request, revista)  # ?secao= da data-url: a mesma seção aberta
        estado = f"secao-estado-{contexto['bloco'].rf.fasciculo}-{contexto['s'].id}"
        trocar = {n: render_to_string(f"ui/parciais/revista_{n}.html", contexto, request=request) for n in ("secoes", "situacao")}
        trocar[estado] = render_to_string("ui/parciais/revista_secao_estado.html", contexto, request=request)
        return {"trocar": trocar}

    return responder_campo(
        request, form=form, gravar=gravar, simular=gravar_quieto, revistas=lambda: [revista], titulo="Salvar o texto da seção"
    )


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
    """Autosave da capa (`campo` = `arquivo_capa`, o arquivo em `valor`): mesma validação do admin
    (RevistaForm). O impacto simula só o sha256 (é o que entra no hash, D-118), sem gravar arquivo à toa."""
    campo = request.POST.get("campo", "")
    if campo != "arquivo_capa" or "valor" not in request.FILES:
        return erros(["Escolha o arquivo da capa e envie de novo."])
    form = RevistaForm({}, {campo: request.FILES["valor"]}, instance=revista)
    form.fields[campo].label = ""  # "Capa maior que 5 MB: …" já diz qual

    def simular(dados):
        Revista.objects.filter(pk=revista.pk).update(capa_sha256=hashlib.sha256(dados[campo]).hexdigest())

    def gravar(dados):
        arquivos.receber_capa(revista, dados[campo])
        return {"trocar": _pedacos(request, revista, "arquivos", "situacao")}

    return responder_campo(request, form=form, simular=simular, gravar=gravar, revistas=lambda: [revista], titulo="Trocar a capa")


def _infografico(request, revista):
    """Autosave de um campo do infográfico (nomes em `nucleo/infografico.py`; a imagem do item vem em
    `valor` nos FILES). A resposta troca a Situação; a imagem troca também o passo (a miniatura). Os
    textos não trocam o passo: o campo seguinte, já com o foco e talvez com texto digitado, se perderia."""
    campo = request.POST.get("campo", "")
    if not request.user.has_perms(PERMS_INFOGRAFICO.get(familia(campo), ["nucleo.change_revistainfografico"])):
        raise PermissionDenied
    achado = form_do_campo(revista, campo, request.POST.get("valor", ""), request.FILES.get("valor"))
    if achado is None:
        return erros(["Este campo não pode ser alterado aqui. Recarregue a página."])
    form, gravar, simular = achado
    # ponytail: a imagem troca o passo inteiro; um envio de texto de outro campo ainda em voo que volte 422
    # perde a mensagem (o campo foi substituído). Trocar só o item enviado, se isso aparecer.
    pedacos = ("infograficos", "situacao") if campo.endswith("-imagem") else ("situacao",)
    return responder_campo(
        # simular sem o `trocar`: renderizar a página dentro do savepoint desfeito dobraria as queries
        request, form=form, simular=simular or gravar, revistas=lambda: [revista], titulo="Salvar o infográfico",
        gravar=lambda dados: gravar(dados) or {"trocar": _pedacos(request, revista, *pedacos)},
    )  # fmt: skip


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
@login_required
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
