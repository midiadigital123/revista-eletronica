"""Matrizes e descritores B (T09-T11): /ui/matriz/<ano>/, rota ui_matriz. Convenções: docs/telas/design-system.md.

Mesma regra do admin (`admin/matriz.py`, `nucleo/matriz.py`, `servicos/matriz.py`): formulários,
impacto (D-076), duplicar (D-101, D-113, D-124), reimportar (D-071, D-141, D-146), arquivo do
item (D-180) e exclusão com confirmação forte (D-181). Escrita na etapa × CC (MEC) só com o
bloqueio dela (`ui_bloqueio.com_bloqueio`, alvo = MEC, D-081). Ficha: docs/telas/fichas/matriz.md.
"""

import re
from pathlib import PurePosixPath

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.forms import inlineformset_factory, modelform_factory
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo.contexto import ano_da_sessao
from nucleo.matriz import (
    DescritorForm,
    DuplicarForm,
    ExcluirForm,
    ImpactoForm,
    ItemForm,
    LinhasField,
    MatrizForm,
    ReimportarForm,
    excluir,
    gravar_item,
    reimportar,
)  # fmt: skip
from nucleo.models import Ano, Descritor, Matriz, MatrizEtapaCC, Revista, Tarefa
from nucleo.servicos.matriz import (
    DuplicacaoRecusada,
    diferencas,
    duplicar_matriz,
    impacto,
    revistas_afetadas,
)
from nucleo.servicos.impacto import avisar_perdidos
from nucleo.ui_autosave import erros, form_de_um_campo, proxima_ordem, quer_json, reordenar, responder_campo
from nucleo.ui_bloqueio import com_bloqueio, e_htmx
from nucleo.urls.preview import TIPOS_ITEM, servir

ERROS = "Nada foi gravado: corrija os erros marcados."
EDITAR = (
    "nucleo.change_matrizetapacc", "nucleo.change_descritor", "nucleo.add_descritor",
    "nucleo.change_tarefa", "nucleo.add_tarefa",
)  # fmt: skip


def pode_ver(user):
    return user.has_perm("nucleo.view_matriz") or user.has_perm("nucleo.change_matriz")


def pode_editar(user):
    """O pacote "editar matriz" dos perfis: etapa × CC, descritor e tarefa (admin: inlines)."""
    return user.has_perms(EDITAR)


def _estilo(*forms_):
    """Classes do design system nos widgets e aria-invalid nos campos com erro."""
    for form in forms_:
        erros = form.errors if form.is_bound else {}
        for nome, campo in form.fields.items():
            w = campo.widget
            if isinstance(w, forms.CheckboxInput) or w.is_hidden:
                continue
            if form.is_bound and not isinstance(w, forms.FileInput):  # Cancelar do modal de impacto volta a isto
                w.attrs["data-original"] = campo.prepare_value(form[nome].initial) or ""
            w.attrs["class"] = "textarea" if isinstance(w, forms.Textarea) else "select" if isinstance(w, forms.Select) else "input"
            if nome in erros:
                w.attrs["aria-invalid"] = "true"
    return forms_[0] if len(forms_) == 1 else forms_


def _redirecionar(request, url):
    """PRG: página inteira → 302; HTMX → HX-Redirect (o com_bloqueio libera nos dois)."""
    return HttpResponse(headers={"HX-Redirect": url}) if e_htmx(request) else redirect(url)


def _contexto_ano(ano):
    return {"anos": list(Ano.objects.order_by("-ano")), "ano": ano, "secao": "matrizes"}


# --- Matrizes do ano e matriz (T09) ---------------------------------------------------------


@require_GET
@login_required
def inicio(request):
    ano = ano_da_sessao(request)
    if ano:
        return redirect("ui_matriz", ano.ano)
    if not pode_ver(request.user):
        raise PermissionDenied
    return TemplateResponse(request, "ui/matriz/lista.html", _contexto_ano(None))


@require_GET
@login_required
def matrizes(request, ano):
    if not pode_ver(request.user):
        raise PermissionDenied
    ano = get_object_or_404(Ano, ano=ano)
    lista = (
        Matriz.objects.filter(ano=ano).select_related("duplicada_de__ano")
        .annotate(n_mec=Count("matrizetapacc", distinct=True), n_desc=Count("matrizetapacc__descritor", distinct=True))
        .order_by("nome")
    )  # fmt: skip
    outras = Matriz.objects.exclude(ano=ano).select_related("ano").order_by("-ano__ano", "nome")
    nova = _estilo(NovaMatrizForm(initial={"ano": ano.pk})) if request.user.has_perm("nucleo.add_matriz") else None
    return TemplateResponse(request, "ui/matriz/lista.html", {
        **_contexto_ano(ano), "matrizes": lista, "outras": outras, "vazio_titulo": f"Nenhuma matriz em {ano.ano}",
        "nova": nova,
    })  # fmt: skip


def _matriz(request, pk, permissao=None):
    if not pode_ver(request.user) or (permissao and not request.user.has_perm(permissao)):
        raise PermissionDenied
    return get_object_or_404(Matriz.objects.select_related("ano", "duplicada_de__ano"), pk=pk)


RenomearForm = modelform_factory(Matriz, form=MatrizForm, fields=["nome"], labels={"nome": "Nome"})
NovaMatrizForm = modelform_factory(Matriz, form=MatrizForm, fields=["ano", "nome"], labels={"ano": "Ano", "nome": "Nome"})


def _forms_matriz(m, duplicar=None):
    return {
        "duplicar": _estilo(duplicar or DuplicarForm(initial={"nome": f"{m.nome} (cópia)", "ano": m.ano_id})),
    }


@require_GET
@login_required
def matriz(request, pk):
    m = _matriz(request, pk)
    mecs = (
        MatrizEtapaCC.objects.filter(matriz=m).select_related("etapa", "componente")
        .annotate(n_desc=Count("descritor")).order_by("etapa__ordem", "componente__codigo")
    )  # fmt: skip
    u = request.user
    return TemplateResponse(request, "ui/matriz/matriz.html", {
        **_contexto_ano(m.ano), "matriz": m, "linhas": [(mec, revistas_afetadas(mec)) for mec in mecs],
        "pode_duplicar": u.has_perm("nucleo.add_matriz"), "pode_alterar": u.has_perm("nucleo.change_matriz"),
        **_forms_matriz(m),
    })  # fmt: skip


def _form_em_dialogo(request, m, chave, form, titulo, url, ano=None):
    """Erro: HTMX devolve o form para dentro do modal; sem JS, a página do form. `ano` quando ainda não há matriz."""
    contexto = {**_contexto_ano(ano or m.ano), "matriz": m, "form": _estilo(form), "titulo": titulo, "url": url, "chave": chave}
    if e_htmx(request):
        return TemplateResponse(request, "ui/parciais/matriz_form.html", contexto)
    return TemplateResponse(request, "ui/matriz/form.html", contexto)


@require_http_methods(["GET", "POST"])
@login_required
def duplicar(request, pk):
    origem = _matriz(request, pk, "nucleo.add_matriz")
    form = DuplicarForm(request.POST or None, initial={"nome": f"{origem.nome} (cópia)", "ano": origem.ano_id})
    if request.method == "POST" and form.is_valid():
        try:
            nova = duplicar_matriz(origem, form.cleaned_data["ano"], form.cleaned_data["nome"], request.user)
        except DuplicacaoRecusada as e:
            form.add_error(None, f"Não duplicado: {e}. Escolha outro nome ou ano.")
        else:
            messages.success(request, f"Matriz {nova} criada como cópia de {origem}.")
            return _redirecionar(request, reverse("ui_matriz_detalhe", args=[nova.pk]))
    return _form_em_dialogo(request, origem, "duplicar", form, f"Duplicar {origem}", reverse("ui_matriz_duplicar", args=[pk]))


@require_http_methods(["GET", "POST"])
@login_required
def nova(request, ano):
    """S6: matriz vazia no ano da lista; o arquivo do SAEGO entra no Reimportar (a matriz nasce sem MEC)."""
    if not (pode_ver(request.user) and request.user.has_perm("nucleo.add_matriz")):
        raise PermissionDenied
    ano = get_object_or_404(Ano, ano=ano)
    form = NovaMatrizForm(request.POST or None, initial={"ano": ano.pk})
    if request.method == "POST" and form.is_valid():
        criada = form.save()
        messages.success(request, f"Matriz {criada} criada. Importe o arquivo do SAEGO para trazer os descritores.")
        return _redirecionar(request, reverse("ui_matriz_reimportar", args=[criada.pk]))
    return _form_em_dialogo(request, None, "nova", form, "Nova matriz", reverse("ui_matriz_nova", args=[ano.ano]), ano=ano)


@require_POST
@login_required
def renomear(request, pk):
    """U5: renomear inline no título (componente `nomeInline`), pelo protocolo do autosave (U3).
    O nome da matriz não entra no texto da revista; o impacto é calculado mesmo assim (U2)."""
    m = _matriz(request, pk, "nucleo.change_matriz")
    form = form_de_um_campo(RenomearForm, request.POST.get("campo"), request.POST.get("valor", "").strip(), instance=m)
    revistas = lambda: Revista.objects.filter(projeto__parceiro_ano__matriz=m, arquivada_em__isnull=True)  # noqa: E731
    return responder_campo(request, form=form, gravar=lambda d: {"valor": form.save().nome}, revistas=revistas, titulo="Renomear")


@require_http_methods(["GET", "POST"])
@login_required
def reimportar_view(request, pk):
    m = _matriz(request, pk, "nucleo.change_matriz")
    form = ReimportarForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        sucesso = form.is_valid() and reimportar(m, form)
        if sucesso:
            messages.success(request, sucesso)
            return redirect("ui_matriz_detalhe", m.pk)
        messages.error(request, "Nada foi importado: corrija os erros marcados e escolha o arquivo de novo.")
    existentes = MatrizEtapaCC.objects.filter(matriz=m)
    return TemplateResponse(request, "ui/matriz/reimportar.html", {
        **_contexto_ano(m.ano), "matriz": m, "form": _estilo(form),
        "tem_mec": existentes.exists(),
        "aviso_confirmar": (
            "Etapas × componente que já existem e estiverem no arquivo terão descritores e tarefas recriados. "
            f"Hoje a matriz afeta {revistas_afetadas(*existentes)} revista(s) ativa(s)."
        ),
    })  # fmt: skip


@require_GET
@login_required
def diferencas_view(request, pk):
    m = _matriz(request, pk)
    return TemplateResponse(request, "ui/matriz/diferencas.html", {**_contexto_ano(m.ano), "matriz": m, "linhas": diferencas(m)})


# --- Etapa × CC, descritor e tarefas (T10/T11) ----------------------------------------------


def _mec(request, pk, **kwargs):
    """Alvo do `com_bloqueio`: confere a permissão de ver antes, para não travar a MEC à toa."""
    if not (request.user.has_perm("nucleo.view_matrizetapacc") or request.user.has_perm("nucleo.change_matrizetapacc")):
        raise PermissionDenied
    return get_object_or_404(MatrizEtapaCC.objects.select_related("matriz__ano", "etapa", "componente"), pk=pk)


class IntervaloForm(ImpactoForm):
    modal = True
    passo = forms.IntegerField(
        label="Intervalo mínimo", required=False, min_value=1,
        help_text="Vazio = sem linhas vazias. Os projetos podem sobrescrever.",
    )  # fmt: skip

    class Meta:
        model = MatrizEtapaCC
        fields = ("passo",)


class DescritorUiForm(DescritorForm):
    modal = True
    prerequisitos = LinhasField(label="Pré-requisitos", required=False, help_text="Um por linha.")

    class Meta:
        model = Descritor
        fields = (
            "codigo", "descricao", "prerequisitos", "praticas", "conhecimento",
            "habilidades_relacionadas", "habilidade_correspondente",
        )  # fmt: skip
        labels = {
            "codigo": "Código", "descricao": "Descrição", "praticas": "Práticas de linguagem",
            "conhecimento": "Objetos de conhecimento", "habilidades_relacionadas": "Habilidades relacionadas",
            "habilidade_correspondente": "Habilidade correspondente",
        }  # fmt: skip
        widgets = {  # noqa: RUF012 (Meta do Django)
            "codigo": forms.TextInput(attrs={"autocomplete": "off", "spellcheck": "false"}),
            **{
                c: forms.Textarea(attrs={"rows": 2})
                for c in ("descricao", "praticas", "conhecimento", "habilidades_relacionadas", "habilidade_correspondente")
            },
        }


NovoDescritorForm = modelform_factory(
    Descritor, form=DescritorForm, fields=("codigo", "descricao"),  # U4: ordem = fim da lista (proxima_ordem)
    labels=DescritorUiForm.Meta.labels,
    widgets={"codigo": forms.TextInput(attrs={"autocomplete": "off"}), "descricao": forms.Textarea(attrs={"rows": 3})},
)  # fmt: skip
NovoDescritorForm.modal = True


class ItemUiForm(ItemForm):
    modal = True


def _perdem(mec):
    """Revistas validadas que uma edição da MEC tira do "Validado": as afetadas (D-076) validadas."""
    return [r for r, validada in impacto(mec) if validada]


def _avisar(request, mec, form):
    if form.perdem:
        avisar_perdidos(request, form.perdem, mec.matriz.ano.ano)


class _TarefasFormSet(forms.BaseInlineFormSet):
    def save_new(self, form, commit=True):
        form.instance.ordem = proxima_ordem(Tarefa.objects.filter(descritor=self.instance))  # U4: fim da lista
        return super().save_new(form, commit)


def _tarefas(extra=0):
    return inlineformset_factory(
        Descritor, Tarefa, formset=_TarefasFormSet, fields=("inicio", "fim", "texto"), extra=extra, can_delete=False,
        labels={"inicio": "Início", "fim": "Fim", "texto": "Texto"},
        widgets={"texto": forms.Textarea(attrs={"rows": 2})},
    )  # fmt: skip


def _ordem(descritor):
    return Tarefa.objects.filter(descritor=descritor).order_by("ordem", "pk")


def _formset(descritor, data=None):
    """Tarefas do descritor, sem linha em branco (U4): o "+ Adicionar tarefa" põe a linha nova
    (molde do empty_form) e soma 1 ao TOTAL_FORMS."""
    return _tarefas()(data, instance=descritor, prefix="tarefas", queryset=_ordem(descritor))


def _descritores(mec, q):
    todos = Descritor.objects.filter(matriz_etapa_cc=mec).order_by("ordem", "pk")
    filtro = todos.filter(Q(codigo__icontains=q) | Q(descricao__icontains=q)) if q else todos
    return list(filtro), todos.count()


def _url_descritor(mec, d):
    return reverse("ui_matriz_descritor", args=[mec.pk, d.pk])


def _pagina_mec(request, mec, descritor, form=None, tarefas=None, item_pendente=None):
    """Página inteira, o painel (HTMX, com a lista fora do alvo) ou só a lista (busca)."""
    q = request.GET.get("q", "").strip()
    visiveis, total = _descritores(mec, q)
    contexto = {
        **_contexto_ano(mec.matriz.ano), "mec": mec, "descritor": descritor, "q": q,
        "visiveis": visiveis, "total": total, "pode_gravar": request.pode_gravar,
        "ativo": descritor.pk if descritor else None, "oob": e_htmx(request), "item_pendente": item_pendente,
    }  # fmt: skip
    if e_htmx(request) and request.headers.get("HX-Target") == "lista-descritores":
        d = request.GET.get("d", "")  # a busca manda o descritor aberto no painel
        contexto.update(oob=False, ativo=int(d) if d.isdigit() else None)
        return TemplateResponse(request, "ui/parciais/matriz_lista.html", contexto)
    afetadas = revistas_afetadas(mec)
    if descritor is not None:
        if form is None:
            form = DescritorUiForm(instance=descritor)
        if tarefas is None:
            tarefas = _formset(descritor)
        _estilo(form, *tarefas.forms)
        u = request.user
        contexto.update(
            form=form, tarefas=tarefas, escala=mec.etapa.escala_max, tarefa_nova=_estilo(tarefas.empty_form),
            excluir_descritor=request.pode_gravar and u.has_perm("nucleo.delete_descritor"),
            excluir_tarefa=request.pode_gravar and u.has_perm("nucleo.delete_tarefa"),
        )  # fmt: skip
        if request.pode_gravar:
            salvas = list(_ordem(descritor))
            revistas = impacto(mec) if salvas else []
            perdem = [r for r, v in revistas if v]
            # O modal do item já lista quem perde o "Validado": enviar por ele é a confirmação (U2).
            inicial = {"confirmar_impacto": bool(perdem)}
            contexto["itens"] = [(t, _estilo(ItemUiForm(instance=t, initial=inicial, auto_id=f"item{t.pk}_%s"))) for t in salvas]
            contexto.update(item_impacto=(len(revistas), len(perdem)), item_perdem=perdem)
    if e_htmx(request):
        return TemplateResponse(request, "ui/parciais/matriz_painel.html", contexto)
    contexto.update(
        afetadas=afetadas, perfil_edita=pode_editar(request.user),
        intervalo=_estilo(IntervaloForm(instance=mec)),
        novo=_estilo(NovoDescritorForm(auto_id="novo_%s")),
    )  # fmt: skip
    return TemplateResponse(request, "ui/matriz/mec.html", contexto)


@require_http_methods(["GET", "POST"])
@login_required
@com_bloqueio(_mec, pode_editar)
def mec(request, pk, dpk=None):
    m = _mec(request, pk)
    if dpk is None:
        if request.method == "POST":
            raise PermissionDenied
        return _pagina_mec(request, m, Descritor.objects.filter(matriz_etapa_cc=m).order_by("ordem", "pk").first())
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    if request.method != "POST":
        return _pagina_mec(request, m, d)
    form = DescritorUiForm(request.POST, instance=d)
    tarefas = _formset(d, request.POST)
    if form.is_valid() and tarefas.is_valid():
        mudou = form.has_changed() or tarefas.has_changed()
        if not form.pedir_confirmacao(_perdem(m) if mudou else []):
            form.save()
            tarefas.save()
            messages.success(request, f"Descritor {d.codigo} salvo.")
            _avisar(request, m, form)
            if not e_htmx(request):
                return redirect(_url_descritor(m, d))
            return _pagina_mec(request, m, d)
    else:
        messages.error(request, ERROS)
    return _pagina_mec(request, m, Descritor.objects.get(pk=d.pk), form=form, tarefas=tarefas)


@require_http_methods(["POST"])
@login_required
@com_bloqueio(_mec, pode_editar)
def intervalo(request, pk):
    """Intervalo mínimo. U9: no popover "Configurações" salva sozinho (campoAuto, protocolo do
    autosave, com impacto); o POST da página (HTMX ou sem JS) segue valendo."""
    m = _mec(request, pk)
    if quer_json(request):
        form = form_de_um_campo(IntervaloForm, request.POST.get("campo", ""), request.POST.get("valor", ""), instance=m)

        def gravar(dados):
            atual = MatrizEtapaCC.objects.get(pk=m.pk)
            atual.passo = dados["passo"]
            atual.save(update_fields=["passo"])

        revistas = lambda: [r for r, _ in impacto(m)]  # noqa: E731
        return responder_campo(request, form=form, gravar=gravar, revistas=revistas, titulo="Salvar o intervalo mínimo")
    form = IntervaloForm(request.POST, instance=m)
    if form.is_valid() and not form.pedir_confirmacao(_perdem(m) if form.has_changed() else []):
        form.save()
        messages.success(request, f"Intervalo mínimo de {m.etapa.codigo} {m.componente.codigo} salvo.")
        _avisar(request, m, form)
        form = IntervaloForm(instance=m)
    elif not form.precisa_confirmar:
        messages.error(request, ERROS)
    if not e_htmx(request):
        return redirect("ui_matriz_mec", m.pk)
    contexto = {"mec": m, "intervalo": _estilo(form), "pode_gravar": True, "oob": True}
    return TemplateResponse(request, "ui/parciais/matriz_intervalo.html", contexto)


@require_http_methods(["POST"])
@login_required
@com_bloqueio(_mec, pode_editar)
def novo_descritor(request, pk):
    m = _mec(request, pk)
    ordem = proxima_ordem(Descritor.objects.filter(matriz_etapa_cc=m))
    form = NovoDescritorForm(request.POST, instance=Descritor(matriz_etapa_cc=m, ordem=ordem), auto_id="novo_%s")
    if form.is_valid() and not form.pedir_confirmacao(_perdem(m)):
        d = form.save()
        messages.success(request, f"Descritor {d.codigo} criado.")
        _avisar(request, m, form)
        return _redirecionar(request, _url_descritor(m, d))
    url = reverse("ui_matriz_novo", args=[m.pk])
    return _form_em_dialogo(request, m.matriz, "novo", form, f"Novo descritor em {m.etapa.codigo} {m.componente.codigo}", url)


@require_GET
@login_required
def item_baixar(request, pk, dpk, tpk):
    """Download do arquivo do item (D-180, a mesma regra do GET do admin): sem arquivo, tipo
    desconhecido ou arquivo sumido do storage, 404. Só leitura: não passa pelo bloqueio da MEC."""
    m = _mec(request, pk)
    tarefa = get_object_or_404(Tarefa, pk=tpk, descritor__pk=dpk, descritor__matriz_etapa_cc=m)
    tipo = TIPOS_ITEM.get(PurePosixPath(tarefa.arquivo or "").suffix)
    if tipo is None:
        raise Http404
    try:
        return servir(default_storage.open(tarefa.arquivo), tipo, as_attachment=True)
    except FileNotFoundError:
        raise Http404 from None


@require_http_methods(["POST"])
@login_required
@com_bloqueio(_mec, pode_editar)
def item(request, pk, dpk, tpk):
    """Arquivo do item da tarefa (D-180): envia, troca ou remove. O download é `item_baixar`."""
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    tarefa = get_object_or_404(Tarefa, pk=tpk, descritor=d)
    form = ItemUiForm(request.POST, request.FILES, instance=tarefa)
    remover = "_remover" in request.POST
    if form.is_valid() and form.pedir_confirmacao(_perdem(m) if remover or form.has_changed() else []):
        # Enviado sem a confirmação do modal do item (a lista mudou depois que a página abriu):
        # o modal do item volta aberto com a lista atual. O arquivo escolhido não volta.
        messages.warning(request, f"Nada foi enviado: a tarefa {tarefa.codigo} tira o “Validado” de "
                         f"{len(form.perdem)} revista(s). Confira a lista, escolha o arquivo de novo e envie.")
        if not e_htmx(request):
            return redirect(_url_descritor(m, d))
        return _pagina_mec(request, m, Descritor.objects.get(pk=d.pk), item_pendente=tarefa.pk)
    sucesso, erro = gravar_item(tarefa, form, remover)
    if sucesso:
        messages.success(request, sucesso)
        _avisar(request, m, form)
    else:
        messages.error(request, f"Arquivo do item da tarefa {tarefa.codigo} não salvo: {erro}")
    if not e_htmx(request):
        return redirect(_url_descritor(m, d))
    return _pagina_mec(request, m, Descritor.objects.get(pk=d.pk))


TAREFA = re.compile(r"^tarefas-(\d{1,4})-")


@require_POST
@login_required
@com_bloqueio(_mec, pode_editar)
def campo(request, pk, dpk):
    """Autosave (U3) de um campo do descritor ou de uma tarefa já gravada (a linha inteira vem no
    POST, com o prefixo do formset do painel), sob o bloqueio da MEC. A tarefa nova ainda entra
    pelo botão "Incluir tarefa" (POST do painel, U4)."""
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    nome = request.POST.get("campo", "")
    revistas = lambda: [r for r, _ in impacto(m)]  # noqa: E731 (as afetadas, D-076; a simulação acha as que perdem)
    if t := TAREFA.match(nome):
        prefixo = f"tarefas-{t[1]}"
        pk_tarefa = request.POST.get(f"{prefixo}-id", "")
        if not (pk_tarefa.isascii() and pk_tarefa.isdigit()):
            return erros(["Tarefa nova: preencha a linha e use Incluir tarefa."])
        tarefa = get_object_or_404(Tarefa, pk=pk_tarefa, descritor=d)
        form = _tarefas(0).form(request.POST, instance=tarefa, prefix=prefixo)
        return responder_campo(
            request, form=form, gravar=lambda _: form.save() and None, revistas=revistas, titulo=f"Salvar a tarefa {tarefa.codigo}"
        )
    form = form_de_um_campo(DescritorUiForm, nome, request.POST.get("valor", ""), instance=d)

    def gravar(dados):
        atual = Descritor.objects.get(pk=d.pk)
        setattr(atual, nome, dados[nome])
        atual.save(update_fields=[nome])

    titulo = f"Salvar “{form.fields[nome].label}” de {d.codigo}" if form else "Salvar"
    return responder_campo(request, form=form, gravar=gravar, revistas=revistas, titulo=titulo)


@require_POST
@login_required
@com_bloqueio(_mec, pode_editar)
def reordenar_view(request, pk, dpk=None):
    """U4: ordem dos descritores da MEC (sem `dpk`) ou das tarefas de um descritor, pela alça
    (arrastar ou ↑/↓ com o foco nela, componente `ordenavel`). A ordem entra na revista: impacto."""
    m = _mec(request, pk)
    revistas = lambda: [r for r, _ in impacto(m)]  # noqa: E731
    if dpk is None:
        qs, titulo = Descritor.objects.filter(matriz_etapa_cc=m), "Reordenar os descritores"
    else:
        d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
        qs, titulo = Tarefa.objects.filter(descritor=d), f"Reordenar as tarefas de {d.codigo}"
    return reordenar(request, qs, revistas=revistas, titulo=titulo)


# --- Exclusão com confirmação forte (D-181) -------------------------------------------------


def _excluir(request, mec, obj, rotulo, voltar):
    form = ExcluirForm(request.POST or None, codigo=obj.codigo)
    if request.method == "POST" and form.is_valid():
        messages.success(request, excluir(obj, rotulo))
        return redirect(voltar)
    revistas = impacto(mec)
    _estilo(form)
    return TemplateResponse(request, "ui/matriz/excluir.html", {
        **_contexto_ano(mec.matriz.ano), "mec": mec, "obj": obj, "rotulo": rotulo, "form": form, "voltar": voltar,
        "revistas": revistas, "validadas": sum(v for _, v in revistas), "pode_gravar": request.pode_gravar,
    })  # fmt: skip


@require_http_methods(["GET", "POST"])
@login_required
@permission_required("nucleo.delete_descritor", raise_exception=True)  # sem poder excluir, nem a página (GET 403, como o Reimportar)
@com_bloqueio(_mec, lambda u: u.has_perm("nucleo.delete_descritor"))
def excluir_descritor(request, pk, dpk):
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    return _excluir(request, m, d, "descritor", reverse("ui_matriz_mec", args=[m.pk]))


@require_http_methods(["GET", "POST"])
@login_required
@permission_required("nucleo.delete_tarefa", raise_exception=True)  # sem poder excluir, nem a página (GET 403, como o Reimportar)
@com_bloqueio(_mec, lambda u: u.has_perm("nucleo.delete_tarefa"))
def excluir_tarefa(request, pk, dpk, tpk):
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    tarefa = get_object_or_404(Tarefa.objects.select_related("descritor"), pk=tpk, descritor=d)
    return _excluir(request, m, tarefa, "tarefa", _url_descritor(m, d))


urlpatterns = [
    path("", inicio, name="ui_matriz_inicio"),
    path("<int:ano>/", matrizes, name="ui_matriz"),
    path("<int:ano>/nova/", nova, name="ui_matriz_nova"),
    path("m/<int:pk>/", matriz, name="ui_matriz_detalhe"),
    path("m/<int:pk>/duplicar/", duplicar, name="ui_matriz_duplicar"),
    path("m/<int:pk>/renomear/", renomear, name="ui_matriz_renomear"),
    path("m/<int:pk>/reimportar/", reimportar_view, name="ui_matriz_reimportar"),
    path("m/<int:pk>/diferencas/", diferencas_view, name="ui_matriz_diferencas"),
    path("mec/<int:pk>/", mec, name="ui_matriz_mec"),
    path("mec/<int:pk>/intervalo/", intervalo, name="ui_matriz_intervalo"),
    path("mec/<int:pk>/novo/", novo_descritor, name="ui_matriz_novo"),
    path("mec/<int:pk>/reordenar/", reordenar_view, name="ui_matriz_reordenar"),
    path("mec/<int:pk>/d/<int:dpk>/reordenar/", reordenar_view, name="ui_matriz_reordenar"),
    path("mec/<int:pk>/d/<int:dpk>/", mec, name="ui_matriz_descritor"),
    path("mec/<int:pk>/d/<int:dpk>/campo/", campo, name="ui_matriz_campo"),
    path("mec/<int:pk>/d/<int:dpk>/excluir/", excluir_descritor, name="ui_matriz_excluir_descritor"),
    path("mec/<int:pk>/d/<int:dpk>/tarefa/<int:tpk>/item/", item, name="ui_matriz_item"),
    path("mec/<int:pk>/d/<int:dpk>/tarefa/<int:tpk>/item/baixar/", item_baixar, name="ui_matriz_item_baixar"),
    path("mec/<int:pk>/d/<int:dpk>/tarefa/<int:tpk>/excluir/", excluir_tarefa, name="ui_matriz_excluir_tarefa"),
]
