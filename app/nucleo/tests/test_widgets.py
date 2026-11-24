from django import forms
from django.test import SimpleTestCase

from nucleo.widgets import classe_css


class ClasseDoWidget(SimpleTestCase):
    def test_classe_pelo_tipo(self):
        self.assertEqual(classe_css(forms.Textarea()), "textarea")
        self.assertEqual(classe_css(forms.Select()), "select")
        self.assertEqual(classe_css(forms.SelectMultiple()), "select")
        self.assertEqual(classe_css(forms.TextInput()), "input")
        self.assertEqual(classe_css(forms.NumberInput()), "input")
