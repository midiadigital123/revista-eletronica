"""Matrizes e descritores B (T09-T11): /ui/matriz/<ano>/, rota ui_matriz. Convenções: docs/telas/design-system.md.

Mesma regra do admin (`admin/matriz.py`, `nucleo/matriz.py`, `servicos/matriz.py`): formulários,
impacto (D-076), duplicar (D-101, D-113, D-124), reimportar (D-071, D-141, D-146), arquivo do
item (D-180) e exclusão com confirmação forte (D-181). Escrita na etapa × CC (MEC) só com o
bloqueio dela (`ui_bloqueio.com_bloqueio`, alvo = MEC, D-081). Ficha: docs/telas/fichas/matriz.md.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max, Q
from django.forms import inlineformset_factory, modelform_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET, require_http_methods

from nucleo.matriz import (
    DescritorForm,
    DuplicarForm,
    ExcluirForm,
    ImpactoForm,
    ItemForm,
    LinhasField,
    MatrizForm,
    ReimportarForm,
    com_afetadas,
    excluir,
    gravar_item,
    reimportar,
)  # fmt: skip
from nucleo.models import Ano, Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos.matriz import (
    DuplicacaoRecusada,
    diferencas,
    duplicar_matriz,
    impacto,
    revistas_afetadas,
)
from nucleo.ui_bloqueio import com_bloqueio, e_htmx

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
@login_required(login_url="admin:login")
def inicio(request):
    ano = Ano.objects.order_by("-ano").first()
    if ano:
        return redirect("ui_matriz", ano.ano)
    if not pode_ver(request.user):
        raise PermissionDenied
    return TemplateResponse(request, "ui/matriz/lista.html", _contexto_ano(None))


@require_GET
@login_required(login_url="admin:login")
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
    return TemplateResponse(request, "ui/matriz/lista.html", {
        **_contexto_ano(ano), "matrizes": lista, "outras": outras, "vazio_titulo": f"Nenhuma matriz em {ano.ano}",
    })


def _matriz(request, pk, permissao=None):
    if not pode_ver(request.user) or (permissao and not request.user.has_perm(permissao)):
        raise PermissionDenied
    return get_object_or_404(Matriz.objects.select_related("ano", "duplicada_de__ano"), pk=pk)


RenomearForm = modelform_factory(Matriz, form=MatrizForm, fields=["nome"], labels={"nome": "Nome"})


def _forms_matriz(m, duplicar=None, renomear=None):
    return {
        "duplicar": _estilo(duplicar or DuplicarForm(initial={"nome": f"{m.nome} (cópia)", "ano": m.ano_id})),
        "renomear": _estilo(renomear or RenomearForm(instance=m)),
    }


@require_GET
@login_required(login_url="admin:login")
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


def _form_em_dialogo(request, m, chave, form, titulo, url):
    """Erro: HTMX devolve o form para dentro do modal; sem JS, a página do form."""
    contexto = {**_contexto_ano(m.ano), "matriz": m, "form": _estilo(form), "titulo": titulo, "url": url, "chave": chave}
    if e_htmx(request):
        return TemplateResponse(request, "ui/parciais/matriz_form.html", contexto)
    return TemplateResponse(request, "ui/matriz/form.html", contexto)


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
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
@login_required(login_url="admin:login")
def renomear(request, pk):
    m = _matriz(request, pk, "nucleo.change_matriz")
    form = RenomearForm(request.POST or None, instance=m)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Matriz renomeada para {m.nome}.")
        return _redirecionar(request, reverse("ui_matriz_detalhe", args=[m.pk]))
    return _form_em_dialogo(request, m, "renomear", form, f"Renomear {m}", reverse("ui_matriz_renomear", args=[pk]))


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
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
@login_required(login_url="admin:login")
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
    passo = forms.IntegerField(
        label="Intervalo mínimo", required=False, min_value=1,
        help_text="Vazio = sem linhas vazias. Os projetos podem sobrescrever.",
    )  # fmt: skip

    class Meta:
        model = MatrizEtapaCC
        fields = ("passo",)


class DescritorUiForm(DescritorForm):
    prerequisitos = LinhasField(label="Pré-requisitos", required=False, help_text="Um por linha.")

    class Meta:
        model = Descritor
        fields = (
            "codigo", "ordem", "descricao", "prerequisitos", "praticas", "conhecimento",
            "habilidades_relacionadas", "habilidade_correspondente",
        )  # fmt: skip
        labels = {
            "codigo": "Código", "ordem": "Ordem", "descricao": "Descrição", "praticas": "Práticas de linguagem",
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
    Descritor, form=DescritorForm, fields=("codigo", "descricao", "ordem"),
    labels=DescritorUiForm.Meta.labels,
    widgets={"codigo": forms.TextInput(attrs={"autocomplete": "off"}), "descricao": forms.Textarea(attrs={"rows": 3})},
)  # fmt: skip


def _tarefas(extra):
    return inlineformset_factory(
        Descritor, Tarefa, fields=("inicio", "fim", "texto", "ordem"), extra=extra, can_delete=False,
        labels={"inicio": "Início", "fim": "Fim", "texto": "Texto", "ordem": "Ordem"},
        widgets={"texto": forms.Textarea(attrs={"rows": 2})},
    )  # fmt: skip


def _ordem(descritor):
    return Tarefa.objects.filter(descritor=descritor).order_by("ordem", "pk")


def _formset(descritor, extra, data=None):
    """Tarefas do descritor + `extra` linha(s) em branco com a próxima ordem. GET e POST usam o
    mesmo initial; sem ele, a ordem da linha em branco conta como alteração e a linha é validada."""
    n = Tarefa.objects.filter(descritor=descritor).count()
    return _tarefas(extra)(data, instance=descritor, prefix="tarefas", initial=[{"ordem": n + 1}], queryset=_ordem(descritor))


def _descritores(mec, q):
    todos = Descritor.objects.filter(matriz_etapa_cc=mec).order_by("ordem", "pk")
    filtro = todos.filter(Q(codigo__icontains=q) | Q(descricao__icontains=q)) if q else todos
    return list(filtro), todos.count()


def _url_descritor(mec, d):
    return reverse("ui_matriz_descritor", args=[mec.pk, d.pk])


def _pagina_mec(request, mec, descritor, form=None, tarefas=None):
    """Página inteira, o painel (HTMX, com a lista fora do alvo) ou só a lista (busca)."""
    q = request.GET.get("q", "").strip()
    visiveis, total = _descritores(mec, q)
    contexto = {
        **_contexto_ano(mec.matriz.ano), "mec": mec, "descritor": descritor, "q": q,
        "visiveis": visiveis, "total": total, "pode_gravar": request.pode_gravar,
        "ativo": descritor.pk if descritor else None, "oob": e_htmx(request),
    }  # fmt: skip
    if e_htmx(request) and request.headers.get("HX-Target") == "lista-descritores":
        d = request.GET.get("d", "")  # a busca manda o descritor aberto no painel
        contexto.update(oob=False, ativo=int(d) if d.isdigit() else None)
        return TemplateResponse(request, "ui/parciais/matriz_lista.html", contexto)
    afetadas = revistas_afetadas(mec)
    if descritor is not None:
        if form is None:
            form = com_afetadas(DescritorUiForm, afetadas)(instance=descritor)
        if tarefas is None:
            tarefas = _formset(descritor, 1 if request.pode_gravar else 0)
        _estilo(form, *tarefas.forms)
        u = request.user
        contexto.update(
            form=form, tarefas=tarefas, escala=mec.etapa.escala_max,
            excluir_descritor=request.pode_gravar and u.has_perm("nucleo.delete_descritor"),
            excluir_tarefa=request.pode_gravar and u.has_perm("nucleo.delete_tarefa"),
        )  # fmt: skip
        if request.pode_gravar:
            salvas = list(_ordem(descritor))
            revistas = impacto(mec) if salvas else []
            item_form = com_afetadas(ItemForm, len(revistas))
            contexto["itens"] = [(t, _estilo(item_form(instance=t, auto_id=f"item{t.pk}_%s"))) for t in salvas]
            contexto["item_impacto"] = (len(revistas), sum(v for _, v in revistas))
    if e_htmx(request):
        return TemplateResponse(request, "ui/parciais/matriz_painel.html", contexto)
    contexto.update(
        afetadas=afetadas, perfil_edita=pode_editar(request.user),
        intervalo=_estilo(com_afetadas(IntervaloForm, afetadas)(instance=mec)),
        novo=_estilo(com_afetadas(NovoDescritorForm, afetadas)(initial={"ordem": total + 1}, auto_id="novo_%s")),
    )  # fmt: skip
    return TemplateResponse(request, "ui/matriz/mec.html", contexto)


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
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
    afetadas = revistas_afetadas(m)
    form = com_afetadas(DescritorUiForm, afetadas)(request.POST, instance=d)
    tarefas = _formset(d, 1, request.POST)
    if form.is_valid() and tarefas.is_valid():
        form.save()
        tarefas.save()
        messages.success(request, f"Descritor {d.codigo} salvo.")
        if not e_htmx(request):
            return redirect(_url_descritor(m, d))
        return _pagina_mec(request, m, d)
    messages.error(request, ERROS)
    return _pagina_mec(request, m, Descritor.objects.get(pk=d.pk), form=form, tarefas=tarefas)


@require_http_methods(["POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_mec, pode_editar)
def intervalo(request, pk):
    m = _mec(request, pk)
    form = com_afetadas(IntervaloForm, revistas_afetadas(m))(request.POST, instance=m)
    if form.is_valid():
        form.save()
        messages.success(request, f"Intervalo mínimo de {m.etapa.codigo} {m.componente.codigo} salvo.")
        form = com_afetadas(IntervaloForm, form.afetadas)(instance=m)
    else:
        messages.error(request, ERROS)
    if not e_htmx(request):
        return redirect("ui_matriz_mec", m.pk)
    contexto = {"mec": m, "intervalo": _estilo(form), "pode_gravar": True, "oob": True}
    return TemplateResponse(request, "ui/parciais/matriz_intervalo.html", contexto)


@require_http_methods(["POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_mec, pode_editar)
def novo_descritor(request, pk):
    m = _mec(request, pk)
    ordem = (Descritor.objects.filter(matriz_etapa_cc=m).aggregate(o=Max("ordem"))["o"] or 0) + 1
    form = com_afetadas(NovoDescritorForm, revistas_afetadas(m))(
        request.POST, instance=Descritor(matriz_etapa_cc=m), initial={"ordem": ordem}, auto_id="novo_%s"
    )
    if form.is_valid():
        d = form.save()
        messages.success(request, f"Descritor {d.codigo} criado.")
        return _redirecionar(request, _url_descritor(m, d))
    url = reverse("ui_matriz_novo", args=[m.pk])
    return _form_em_dialogo(request, m.matriz, "novo", form, f"Novo descritor em {m.etapa.codigo} {m.componente.codigo}", url)


@require_http_methods(["POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_mec, pode_editar)
def item(request, pk, dpk, tpk):
    """Arquivo do item da tarefa (D-180): envia, troca ou remove. O download é o do admin."""
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    tarefa = get_object_or_404(Tarefa, pk=tpk, descritor=d)
    form = com_afetadas(ItemForm, revistas_afetadas(m))(request.POST, request.FILES, instance=tarefa)
    sucesso, erro = gravar_item(tarefa, form, "_remover" in request.POST)
    if sucesso:
        messages.success(request, sucesso)
    else:
        messages.error(request, f"Arquivo do item da tarefa {tarefa.codigo} não salvo: {erro}")
    if not e_htmx(request):
        return redirect(_url_descritor(m, d))
    return _pagina_mec(request, m, Descritor.objects.get(pk=d.pk))


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
@login_required(login_url="admin:login")
@com_bloqueio(_mec, lambda u: u.has_perm("nucleo.delete_descritor"))
def excluir_descritor(request, pk, dpk):
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    return _excluir(request, m, d, "descritor", reverse("ui_matriz_mec", args=[m.pk]))


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_mec, lambda u: u.has_perm("nucleo.delete_tarefa"))
def excluir_tarefa(request, pk, dpk, tpk):
    m = _mec(request, pk)
    d = get_object_or_404(Descritor, pk=dpk, matriz_etapa_cc=m)
    tarefa = get_object_or_404(Tarefa.objects.select_related("descritor"), pk=tpk, descritor=d)
    return _excluir(request, m, tarefa, "tarefa", _url_descritor(m, d))


urlpatterns = [
    path("", inicio, name="ui_matriz_inicio"),
    path("<int:ano>/", matrizes, name="ui_matriz"),
    path("m/<int:pk>/", matriz, name="ui_matriz_detalhe"),
    path("m/<int:pk>/duplicar/", duplicar, name="ui_matriz_duplicar"),
    path("m/<int:pk>/renomear/", renomear, name="ui_matriz_renomear"),
    path("m/<int:pk>/reimportar/", reimportar_view, name="ui_matriz_reimportar"),
    path("m/<int:pk>/diferencas/", diferencas_view, name="ui_matriz_diferencas"),
    path("mec/<int:pk>/", mec, name="ui_matriz_mec"),
    path("mec/<int:pk>/intervalo/", intervalo, name="ui_matriz_intervalo"),
    path("mec/<int:pk>/novo/", novo_descritor, name="ui_matriz_novo"),
    path("mec/<int:pk>/d/<int:dpk>/", mec, name="ui_matriz_descritor"),
    path("mec/<int:pk>/d/<int:dpk>/excluir/", excluir_descritor, name="ui_matriz_excluir_descritor"),
    path("mec/<int:pk>/d/<int:dpk>/tarefa/<int:tpk>/item/", item, name="ui_matriz_item"),
    path("mec/<int:pk>/d/<int:dpk>/tarefa/<int:tpk>/excluir/", excluir_tarefa, name="ui_matriz_excluir_tarefa"),
]
