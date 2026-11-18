"""Catraca dos componentes de template (D-271).

Componente já migrado para django-cotton (`templates/cotton/`) não volta a ser escrito à mão nas telas B.
A cada leva da migração, a marcação crua do componente entra em MIGRADOS; o que precisa ficar cru entra em
EXCECOES, com o motivo.
"""

from pathlib import Path

from django.template import Context, Template
from django.test import SimpleTestCase
from django_cotton.compiler_regex import CottonCompiler

UI = Path(__file__).resolve().parent.parent / "templates" / "ui"

# marcação crua → componente que a substitui
MIGRADOS: dict[str, str] = {
    'class="pagina-cab': "<c-pagina-cab>",
}

# (arquivo relativo a templates/ui, marcação crua) → motivo de ficar cru
EXCECOES: dict[tuple[str, str], str] = {}


class CatracaDosComponentes(SimpleTestCase):
    def test_tela_nao_escreve_a_mao_componente_migrado(self):
        achados = []
        for arquivo in sorted(UI.rglob("*.html")):
            relativo = arquivo.relative_to(UI).as_posix()
            for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
                for cru, componente in MIGRADOS.items():
                    if cru in linha and (relativo, cru) not in EXCECOES:
                        achados.append(f"{relativo}:{n}: {cru!r} escrito à mão; use {componente}")
        self.assertEqual(achados, [], "\n" + "\n".join(achados))

    def test_excecao_ainda_existe(self):
        """Exceção que não casa com mais nada é lixo: apague a linha."""
        sobrando = [
            f"{relativo}: {cru!r}"
            for relativo, cru in EXCECOES
            if cru not in (UI / relativo).read_text(encoding="utf-8")
        ]
        self.assertEqual(sobrando, [])


def renderizar(fonte, **contexto):
    return Template(CottonCompiler().process(fonte)).render(Context(contexto))


class SaidaDosComponentes(SimpleTestCase):
    """O HTML de cada componente, travado. Um formatador que quebre as tags {% … %} do arquivo cai aqui."""

    perigoso = "A & B <i>"

    def test_pagina_cab(self):
        html = renderizar(
            '<c-pagina-cab titulo="Ano {{ x }}"><p>{{ x }}</p><c-slot name="acoes"><b>ok</b></c-slot></c-pagina-cab>',
            x=self.perigoso,
        )
        self.assertInHTML(
            '<header class="pagina-cab"><div><h1>Ano A &amp; B &lt;i&gt;</h1><p>A &amp; B &lt;i&gt;</p></div>'
            '<div class="acoes"><b>ok</b></div></header>',
            html,
        )
        sem_acoes = renderizar('<c-pagina-cab titulo="Anos" />')
        self.assertNotIn("acoes", sem_acoes)
        proprio_h1 = renderizar("<c-pagina-cab><form><h1>x</h1></form></c-pagina-cab>")
        self.assertEqual(proprio_h1.count("<h1>"), 1)

    def test_badge(self):
        self.assertEqual(
            renderizar('<c-badge variante="alerta" title="{{ x }}">{{ x }}</c-badge>', x=self.perigoso),
            '<span class="badge badge-alerta" title="A &amp; B &lt;i&gt;">A &amp; B &lt;i&gt;</span>',
        )
        self.assertEqual(renderizar("<c-badge>3</c-badge>"), '<span class="badge">3</span>')

    def test_botao(self):
        self.assertEqual(
            renderizar('<c-botao :href="u" variante="outline" tamanho="sm">ok</c-botao>', u="/a?b=1&c=2"),
            '<a class="btn btn-outline btn-sm" href="/a?b=1&amp;c=2">ok</a>',
        )
        self.assertEqual(
            renderizar('<c-botao type="submit" variante="destrutivo" name="a" x-on:click="abrir" disabled>ok</c-botao>'),
            '<button type="submit" class="btn btn-destrutivo" name="a" x-on:click="abrir" disabled>ok</button>',
        )
        self.assertEqual(renderizar("<c-botao>ok</c-botao>"), '<button type="button" class="btn">ok</button>')

    def test_abas(self):
        html = renderizar(
            '<c-abas rotulo="Partes"><c-aba href="?aba=a" atual="{% if x %}1{% endif %}">A</c-aba>'
            '<c-aba href="?aba=b" atual="">B</c-aba></c-abas>',
            x=1,
        )
        self.assertInHTML(
            '<nav class="abas" aria-label="Partes"><a href="?aba=a" aria-current="page">A</a><a href="?aba=b">B</a></nav>',
            html,
        )

    def test_campo(self):
        html = renderizar(
            '<c-campo rotulo="Nome" para="id_nome" :erros="erros"><input id="id_nome">'
            '<c-slot name="ajuda">Até 200.</c-slot></c-campo>',
            erros=["Obrigatório."],
        )
        self.assertInHTML(
            '<div class="campo"><label for="id_nome">Nome</label><input id="id_nome">'
            '<p class="ajuda">Até 200.</p><p class="erro">Obrigatório.</p></div>',
            html,
        )

    def test_card(self):
        html = renderizar(
            '<c-card titulo="Nome" titulo_id="nome-titulo" id="nome" class="pj-secao" oculto="1"><p>x</p></c-card>'
        )
        self.assertIn('<section class="card pj-secao" id="nome" aria-labelledby="nome-titulo" hidden>', html)
        self.assertInHTML('<h2 class="secao-titulo" id="nome-titulo">Nome</h2>', html)
        com_lateral = renderizar(
            '<c-card titulo="Cores" titulo_id="t"><c-slot name="lateral"><a class="link" href="/x">Editar</a></c-slot></c-card>'
        )
        self.assertIn('<div class="card-cab">', com_lateral)
