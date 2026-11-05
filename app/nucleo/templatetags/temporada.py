"""Ano da temporada (o maior `Ano`) para o topo do admin e o módulo "Temporada" do índice."""

from django import template

from nucleo.models import Ano

register = template.Library()


@register.simple_tag
def ano_temporada():
    return Ano.objects.order_by("-ano").first()
