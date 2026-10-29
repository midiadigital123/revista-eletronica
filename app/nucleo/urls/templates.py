"""Preview ao vivo do editor de templates (static/nucleo/template_editor.js; D-123).

POST com CSRF; login e `nucleo.view_template` (sem eles 403 em JSON, como a rota
do bloqueio: o fetch seguiria o redirect do login). Devolve o HTML de
`texto.renderizar` sem valores: toda variável sai como
`<span class="variavel-vazia">{{nome}}</span>`, que o CSS do editor colore.
"""

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from nucleo import texto
from nucleo.models.texto import Fasciculo
from nucleo.texto import TEXTO_MAX


@require_POST
def preview(request):
    if not request.user.has_perm("nucleo.view_template"):  # anônimo também cai aqui
        return JsonResponse({"erro": "sem permissão"}, status=403)
    corpo = request.POST.get("texto", "").replace("\r\n", "\n")
    if len(corpo) > TEXTO_MAX:
        return JsonResponse({"erro": "texto grande demais"}, status=400)
    erros = []
    if request.POST.get("fasciculo") in Fasciculo.values:
        try:
            texto.validar(corpo, request.POST["fasciculo"])
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
    return JsonResponse({"html": html or "<p>Nenhuma seção (## id) ainda.</p>", "erros": erros})


urlpatterns = [path("preview", preview, name="template_preview")]
