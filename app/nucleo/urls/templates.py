"""Preview ao vivo do editor de templates do admin (static/nucleo/template_editor.js; D-123).

POST com CSRF; login e `nucleo.view_template` (sem eles 403 em JSON, como a rota
do bloqueio: o fetch seguiria o redirect do login). Devolve o HTML de
`templates_texto.previa` (variáveis sem valor, coloridas pelo CSS do editor).
"""

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_POST

from nucleo.templates_texto import previa
from nucleo.texto import TEXTO_MAX


@require_POST
def preview(request):
    if not request.user.has_perm("nucleo.view_template"):  # anônimo também cai aqui
        return JsonResponse({"erro": "sem permissão"}, status=403)
    corpo = request.POST.get("texto", "")
    if len(corpo.replace("\r\n", "\n")) > TEXTO_MAX:
        return JsonResponse({"erro": "texto grande demais"}, status=400)
    html, erros = previa(corpo, request.POST.get("fasciculo"), so_corpo=bool(request.POST.get("corpo")))
    return JsonResponse({"html": html or "<p>Nenhuma seção (## id) ainda.</p>", "erros": erros})


urlpatterns = [path("preview", preview, name="template_preview")]
