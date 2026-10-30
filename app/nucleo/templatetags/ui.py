"""Tags das páginas próprias (opção B)."""

from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def rota_b(nome, *args):
    """URL da rota `nome` com `args` (vazios ignorados) ou, se não casar, sem args; "" se a rota
    não existe. A navegação cai no link do admin equivalente enquanto a tela B não entrou:
    `{% rota_b "ui_matriz" as u %}<a href="{% if u %}{{ u }}{% else %}…admin…{% endif %}">`."""
    args = [a for a in args if a not in (None, "")]
    for tentativa in (args, []) if args else ([],):
        try:
            return reverse(nome, args=tentativa)
        except NoReverseMatch:
            pass
    return ""
