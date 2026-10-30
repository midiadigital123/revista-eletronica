"""Planilha de variáveis (T17; D-100, D-107, D-119, D-121): projetos do ano × variáveis.

Regra comum às duas telas: a do admin (`admin/variaveis.py`, rota em ProjetoAdmin.get_urls) e a
página própria (`urls/ui_variaveis.py`, opção B). Cada projeto alterado é gravado com o bloqueio
dele (`escrever_travado`); travado ou arquivado é pulado e listado. Arquivado fica fora (D-093).
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory

from nucleo import texto
from nucleo.admin.lote import avisar_pulados, escrever_travado
from nucleo.models import Projeto, TemplateVersao
from nucleo.projeto import limitar, mostrar_nome_do_ano
from nucleo.variaveis import EDITAVEIS, TAMANHO_MAX, VARIAVEIS


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


def copiar(request, pk):
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


def pode_ver(user):
    return user.has_perm("nucleo.view_projeto") or user.has_perm("nucleo.change_projeto")


def pode_gravar(user):
    return user.has_perm("nucleo.change_projeto")


def projetos_do_ano(ano):
    return (
        Projeto.objects.filter(ano=ano, arquivado_em__isnull=True)
        .select_related("parceiro_ano__parceiro", "ano")
        .order_by("parceiro_ano__parceiro__nome")
    )


def pk_do_post(texto):
    return int(texto) if texto.isascii() and texto.isdigit() and len(texto) < 19 else 0


def planilha(request, ano):
    """Monta a planilha do ano e, no POST, grava. Devolve (contexto, gravou).

    `gravou` verdadeiro: o chamador redireciona (as mensagens já foram postas).
    POST sem `change_projeto`: PermissionDenied. Formset inválido: contexto com os erros.
    """
    pode_editar = pode_gravar(request.user)
    projetos = projetos_do_ano(ano)
    FormSet = modelformset_factory(Projeto, form=VariaveisForm, extra=0)

    if request.method == "POST":
        if not pode_editar:
            raise PermissionDenied
        if "copiar" in request.POST:
            copiar(request, pk_do_post(request.POST["copiar"]))
            return None, True
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
            return None, True
    else:
        formset = FormSet(queryset=projetos)
    if not pode_editar:
        for form in formset.forms:
            for campo in form.fields.values():
                campo.disabled = True

    usos = templates_por_variavel(ano) if ano else {}
    escala = ["escala do F1 (nome do padrão)"]  # pdNN também é o rótulo do padrão (D-173, D-175)
    legenda = [(v, (escala if v.nome.startswith("pd") else []) + usos.get(v.nome, [])) for v in VARIAVEIS]
    contexto = {
        "formset": formset, "legenda": legenda, "pode_editar": pode_editar,
        "colunas": [v for v in VARIAVEIS if not v.automatica],
    }  # fmt: skip
    return contexto, False
