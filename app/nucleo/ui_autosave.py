"""Autosave por campo das telas B (U3): o protocolo JSON único. Referência: docs/telas/design-system.md.

O cliente (`static/ui/componentes/autosave.js`, componente `campoAuto`) manda um campo por vez:
`campo`, `valor`, `original` (valor que a tela tinha), `confirmar_impacto` e a sessão de bloqueio.
Respostas:

- 200 `{"ok": true, "salvo_em": "10:15"}` (+ extras da rota: `valor` normalizado, `id` da linha nova…)
- 200 `{"ok": false, "impacto": {"titulo", "perdem": [str], "afetadas": int, "html"}}`: NÃO gravou.
  `html` é o modal de impacto do U2 (`_componentes/impacto.html`) pronto para inserir na tela.
- 422 `{"ok": false, "erros": [str]}`
- 409 `{"ok": false, "conflito": str}`: bloqueio perdido (`ui_bloqueio`), ou o `original` difere
  do banco (+ `atual`: o valor gravado agora, para a tela mostrar e o próximo envio sobrescrever).
- 403: sem permissão, como nas outras rotas.
"""

from collections.abc import Callable, Iterable

from django import forms
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.forms.utils import pretty_name
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

from nucleo.models import Revista
from nucleo.servicos.impacto import perdem_validado

CONFIRMAR = "confirmar_impacto"


class Conflito(Exception):
    """`gravar` recusou por estado concorrente: vira 409. `atual` (opcional) vai na resposta."""

    def __init__(self, texto, atual=None):
        super().__init__(texto)
        self.texto, self.atual = texto, atual


def quer_json(request):
    return "application/json" in request.headers.get("Accept", "")


def conflito(texto, atual=None):
    corpo = {"ok": False, "conflito": texto}
    if atual is not None:
        corpo["atual"] = atual
    return JsonResponse(corpo, status=409)


def erros(lista):
    return JsonResponse({"ok": False, "erros": list(lista)}, status=422)


def erros_do_form(form):
    """"Rótulo: erro" (rótulo vazio no campo: só o erro, que já diz onde; ex.: a célula de Cortes)."""
    saida = []
    for nome, lista in form.errors.items():
        campo = form.fields.get(nome)
        rotulo = None if campo is None else pretty_name(nome) if campo.label is None else campo.label
        saida += [f"{rotulo}: {e}" if rotulo else str(e) for e in lista]
    return saida


def form_de_um_campo(Form, campo, valor, *, instance, prefix=None, **kwargs):
    """O form inteiro com os valores gravados e só `campo` trocado por `valor`: reaproveita toda a
    validação do form (inclusive a do modelo) sem o cliente mandar o resto. None: o campo não é
    deste form ou é só leitura (código, escala travada…)."""
    vazio = Form(instance=instance, prefix=prefix, **kwargs)
    if campo not in vazio.fields or vazio.fields[campo].disabled or campo == CONFIRMAR:
        return None
    dados = {vazio.add_prefix(n): vazio[n].value() for n in vazio.fields if n != CONFIRMAR}
    dados = {k: ("" if v is None else v) for k, v in dados.items()}
    dados[vazio.add_prefix(campo)] = valor
    return Form(dados, instance=instance, prefix=prefix, **kwargs)


def responder_campo(
    request, *, form, gravar: Callable[[dict], dict | None], revistas: Callable[[], Iterable[Revista]], titulo="Salvar",
    simular: Callable[[dict], object] | None = None, modal: dict | None = None,
) -> JsonResponse:
    """Valida o `form` (um campo ou uma linha), simula `gravar` para achar quem perde o "Validado"
    (U2) e grava, ou devolve o impacto sem gravar. `gravar(cleaned_data)` pode devolver extras da
    resposta 200 e levantar `Conflito` (409). `simular`: o que roda na simulação, se não for o
    próprio `gravar` (ex.: só o sha256 de um arquivo). `modal`: contexto extra do modal, que passa a
    ser obrigatório mesmo sem revista perdendo o "Validado" (ex.: a frase "descartar N cópia(s)")."""
    if form is None:
        return erros(["Este campo não pode ser alterado aqui. Recarregue a página."])
    if not form.is_valid():
        return erros(erros_do_form(form))
    try:
        candidatas = list(revistas())
        perdem = perdem_validado(lambda: (simular or gravar)(form.cleaned_data), candidatas)
        if (perdem or modal) and not request.POST.get(CONFIRMAR):
            html = render_to_string(
                "ui/_componentes/impacto.html",
                {"form_id": request.POST.get("form_id") or "autosave", "acao": titulo, "perdem": perdem, **(modal or {})},
                request=request,
            )
            impacto = {"titulo": titulo, "perdem": [str(r) for r in perdem], "afetadas": len(candidatas), "html": html}
            return JsonResponse({"ok": False, "impacto": impacto})
        with transaction.atomic():  # savepoint: o erro do banco não estraga a transação do bloqueio
            extra = gravar(form.cleaned_data) or {}
    except Conflito as e:
        return conflito(e.texto, e.atual)
    except IntegrityError:  # o UNIQUE que o form não vê (ex.: o mesmo padrão em duas linhas)
        return erros(["Já existe um registro igual a este (mesmo padrão, código ou etapa × componente). Confira e mude o valor."])
    corpo = {"ok": True, "salvo_em": timezone.localtime().strftime("%H:%M"), **extra}
    if perdem:
        corpo["perderam"] = len(perdem)
    return JsonResponse(corpo)


# --- Linha nova e reordenar (U4) -------------------------------------------------------------


def proxima_ordem(qs) -> int:
    """Ordem de uma linha nova: depois da última (1 quando vazio). O usuário não digita ordem."""
    return (qs.aggregate(m=Max("ordem"))["m"] or 0) + 1


def reordenar(request, qs, *, revistas: Callable[[], Iterable[Revista]], titulo="Reordenar") -> JsonResponse:
    """POST `ids=[pk,…]` (componente `ordenavel`): grava a ordem 1…N, pelo mesmo protocolo do
    autosave (impacto no "Validado", 409 do bloqueio). 422 se a lista não for exatamente `qs`."""
    ids = request.POST.getlist("ids")
    atuais = set(qs.values_list("pk", flat=True))
    if not all(i.isascii() and i.isdigit() for i in ids) or len(set(ids)) != len(ids) or {int(i) for i in ids} != atuais:
        return erros(["A lista mudou depois que a página abriu (linha criada ou excluída). Recarregue a página e reordene de novo."])
    posicao = {int(pk): n for n, pk in enumerate(ids, 1)}

    def gravar(_):
        for obj in qs.model.objects.filter(pk__in=posicao):
            if obj.ordem != posicao[obj.pk]:
                obj.ordem = posicao[obj.pk]
                obj.save(update_fields=["ordem"])  # save, não update(): o histórico registra

    return responder_campo(request, form=forms.Form({}), gravar=gravar, revistas=revistas, titulo=titulo)
