"""Aba Variáveis (D-100, D-107, D-119): projetos do ano × variáveis, editável como planilha.

Página própria (rota em ProjetoAdmin.get_urls), não `list_editable`: o ProjetoAdmin usa o
BloqueioAdminMixin. Cada projeto alterado é gravado com o bloqueio dele; travado é pulado.
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.validators import MaxLengthValidator
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from nucleo import texto
from nucleo.admin.lote import avisar_pulados, contexto, escolher_ano, escrever_travado, filtro
from nucleo.models import CorPadrao, Projeto, TemplateVersao
from nucleo.variaveis import TAMANHO_MAX, VARIAVEIS

EDITAVEIS = [v.nome for v in VARIAVEIS if not v.automatica]


def vazio(valor):
    return valor is None or not str(valor).strip()  # mesmo critério de texto._valor


def templates_por_variavel(ano):
    """{variável: ["LP F1 Padrão", ...]}: templates do ano cuja última versão usa a variável."""
    usos = {v.nome: [] for v in VARIAVEIS}
    ultimas = (
        TemplateVersao.objects.filter(template__ano=ano)
        .select_related("template__componente")
        .order_by("template_id", "-numero")
        .distinct("template_id")  # DISTINCT ON: a maior versão de cada template
    )
    for versao in ultimas:
        t = versao.template
        for nome in texto.variaveis_usadas(versao.texto):
            usos[nome].append(f"{t.componente.codigo} {t.fasciculo} {t.nome}")
    return {nome: sorted(lista) for nome, lista in usos.items()}


def anterior_de(projeto):
    """Projeto do mesmo parceiro no ano imediatamente anterior (o mais recente, mesmo arquivado)."""
    return (
        Projeto.objects.filter(
            parceiro_ano__parceiro_id=projeto.parceiro_ano.parceiro_id, ano__ano=projeto.ano.ano - 1
        )
        .order_by("-pk")
        .first()
    )


def copiar_do_ano_anterior(projeto):
    """Preenche só as variáveis vazias com os valores do ano anterior; não salva.

    Devolve (anterior, nomes copiados); anterior None = não há projeto no ano anterior.
    """
    anterior = anterior_de(projeto)
    if anterior is None:
        return None, []
    copiadas = [n for n in EDITAVEIS if vazio(getattr(projeto, n)) and not vazio(getattr(anterior, n))]
    for n in copiadas:
        setattr(projeto, n, getattr(anterior, n))
    return anterior, copiadas


def limitar(form, limites):
    """Tamanho máximo no form (validador + maxlength): sem isso o CHECK do banco vira 500."""
    for nome, limite in limites.items():
        campo = form.fields.get(nome)  # ausente quando só leitura
        if campo is not None:
            campo.validators.append(MaxLengthValidator(limite))
            campo.widget.attrs["maxlength"] = limite


def mostrar_nome_do_ano(form, ano_id):
    """Placeholder dos `pdNN`: o nome do padrão no ano, que vale quando o campo fica vazio (D-175)."""
    for k, nome in CorPadrao.objects.filter(ano_id=ano_id).exclude(nome="").values_list("padrao", "nome"):
        campo = form.fields.get(f"pd{k:02d}")  # ausente quando só leitura
        if campo is not None:
            campo.widget.attrs["placeholder"] = f"padrão do ano: {nome}"


class VariaveisForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = EDITAVEIS
        widgets = dict.fromkeys(EDITAVEIS, forms.TextInput(attrs={"size": 16}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limitar(self, dict.fromkeys(EDITAVEIS, TAMANHO_MAX))
        # ponytail: 1 SELECT por linha da planilha; passar os nomes por form_kwargs se pesar.
        mostrar_nome_do_ano(self, self.instance.ano_id)
        for campo in self.fields.values():
            # Valor da carga da página no POST: `changed_data` = só o que este usuário mexeu,
            # e não sobrescreve o que outro gravou depois em outra coluna.
            campo.show_hidden_initial = True


def _gravar_alterados(form):
    campos = [n for n in form.changed_data if n in EDITAVEIS]

    def gravar():
        projeto = Projeto.objects.get(pk=form.instance.pk)  # relido dentro do bloqueio
        for nome in campos:
            setattr(projeto, nome, form.cleaned_data[nome])
        projeto.save(update_fields=campos)

    return gravar


def _copiar(request, pk):
    projeto = Projeto.objects.select_related("parceiro_ano", "ano").filter(pk=pk, arquivado_em__isnull=True).first()
    if projeto is None:
        messages.error(request, "Projeto não encontrado ou arquivado.")
        return
    resultado = {}

    def gravar():
        atual = Projeto.objects.select_related("parceiro_ano", "ano").get(pk=pk)
        resultado["anterior"], resultado["copiadas"] = copiar_do_ano_anterior(atual)
        if resultado["copiadas"]:
            atual.save(update_fields=resultado["copiadas"])

    if motivo := escrever_travado(projeto, request.user, gravar):
        messages.warning(request, f"{projeto}: não copiado ({motivo}).")
    elif resultado["anterior"] is None:
        messages.warning(request, f"{projeto}: não há projeto do parceiro em {projeto.ano.ano - 1}; nada mudou.")
    elif not resultado["copiadas"]:
        messages.info(request, f"{projeto}: nada a copiar (as variáveis vazias também estão vazias em {projeto.ano.ano - 1}).")
    else:
        messages.success(request, f"{projeto}: copiado de {projeto.ano.ano - 1}: {', '.join(resultado['copiadas'])}.")


def variaveis(model_admin, request):
    if not model_admin.has_view_permission(request):
        raise PermissionDenied
    pode_editar = request.user.has_perm("nucleo.change_projeto")
    anos, ano = escolher_ano(request)
    # Arquivado é só leitura (D-093): fica fora da planilha.
    projetos = (
        Projeto.objects.filter(ano=ano, arquivado_em__isnull=True)
        .select_related("parceiro_ano__parceiro", "ano")
        .order_by("parceiro_ano__parceiro__nome")
    )
    FormSet = modelformset_factory(Projeto, form=VariaveisForm, extra=0)

    if request.method == "POST":
        if not pode_editar:
            raise PermissionDenied
        if "copiar" in request.POST:
            pk = request.POST["copiar"]
            _copiar(request, int(pk) if pk.isascii() and pk.isdigit() and len(pk) < 19 else 0)
            return HttpResponseRedirect(request.get_full_path())
        formset = FormSet(request.POST, queryset=projetos)
        if formset.is_valid():
            salvos, pulados = 0, []
            for form in formset.forms:
                if not form.changed_data:
                    continue
                if motivo := escrever_travado(form.instance, request.user, _gravar_alterados(form)):
                    pulados.append(f"{form.instance} ({motivo})")
                else:
                    salvos += 1
            messages.success(request, f"Variáveis salvas em {salvos} projeto(s).")
            avisar_pulados(request, pulados)
            return HttpResponseRedirect(request.get_full_path())
    else:
        formset = FormSet(queryset=projetos)
    if not pode_editar:
        for form in formset.forms:
            for campo in form.fields.values():
                campo.disabled = True

    usos = templates_por_variavel(ano) if ano else {}
    escala = ["escala do F1 (nome do padrão)"]  # pdNN também é o rótulo do padrão (D-173, D-175)
    legenda = [(v, (escala if v.nome.startswith("pd") else []) + usos.get(v.nome, [])) for v in VARIAVEIS]
    ctx = contexto(
        model_admin, request, "Variáveis dos projetos",
        formset=formset, legenda=legenda, pode_editar=pode_editar,
        colunas=[v for v in VARIAVEIS if not v.automatica],
        filtros=[filtro("Ano", [(a, a.ano) for a in anos], ano, "ano")],
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/variaveis.html", ctx)
