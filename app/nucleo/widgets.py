"""Classe do design system (ui.css) no widget de um form do Django, pelo tipo: a regra num lugar só.

Os controles escritos à mão nos templates usam <c-input>, <c-select> e <c-textarea> (templates/cotton/).
"""

from django import forms


def classe_css(widget):
    if isinstance(widget, forms.Textarea):
        return "textarea"
    if isinstance(widget, forms.Select):
        return "select"
    return "input"
