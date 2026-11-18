"""Catraca dos componentes de template (D-271).

Componente já migrado para django-cotton (`templates/cotton/`) não volta a ser escrito à mão nas telas B.
A cada leva da migração, a marcação crua do componente entra em MIGRADOS; o que precisa ficar cru entra em
EXCECOES, com o motivo.
"""

import re
from pathlib import Path

from django.template import Context, Template
from django.test import SimpleTestCase
from django_cotton.compiler_regex import CottonCompiler

UI = Path(__file__).resolve().parent.parent / "templates" / "ui"

# marcação crua → componente que a substitui
MIGRADOS: dict[str, str] = {
    'class="pagina-cab': "<c-pagina-cab>",
    'class="campo': "<c-campo>",
    'class="badge': "<c-badge>",
    'class="aviso': "<c-aviso>",
    'class="card': "<c-card>",
    'class="btn': "<c-botao>",
    "<svg": "<c-icone>",
    '<dialog class="dialogo': "<c-modal>",
    'class="btn-icone': "<c-botao-icone>",
}

# (arquivo relativo a templates/ui, marcação crua) → motivo de ficar cru
EXCECOES: dict[tuple[str, str], str] = {
    ("_componentes/matriz_campo.html", 'class="campo'): "já é o campo dos forms do Django (16 usos); label com classe condicional",
    ("parciais/revista_secao.html", 'class="campo'): "atributos condicionais na caixa e inputs ocultos antes do label",
    ("parciais/templates_secao.html", 'class="campo'): "o label vive dentro da barra de ferramentas",
    ("_componentes/mensagens.html", 'class="aviso'): "o aviso é o <li> da lista de mensagens do Django",
    ("_componentes/selo_sobrescrita.html", 'class="badge'): "x-cloak condicional no span; já é o selo dos 3 usos",
    ("parciais/matriz_tarefa.html", 'class="badge'): "o selo é um link (<a>) para baixar o arquivo",
    ("anos/anos.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("excluir.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("matriz/reimportar.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("parciais/revista_secao.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("templates/novo.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("usuarios/form.html", 'class="card'): "a caixa do card é o próprio <form>",
    ("_componentes/anos.html", 'class="btn'): "aria-current condicional no botão",
    ("_componentes/impacto.html", 'class="btn'): "autofocus condicional no botão",
    ("_componentes/nome_inline.html", 'class="btn'): ":aria-label do Alpine junto do aria-label fixo",
    ("_componentes/vazio.html", 'class="btn'): "abre <button> ou <a> conforme o ramo do if, com um fechamento só",
    ("anos/ano.html", 'class="btn'): "o botão é o <summary> do details",
    ("base.html", 'class="btn'): "aria-current condicional no link",
    ("entrar.html", 'class="btn'): "<input type=submit> da tela de entrada",
    ("parciais/revista_secao_estado.html", 'class="btn'): "hx-vals com aspas simples e JSON dentro",
    ("parciais/revista_situacao.html", 'class="btn'): "abre o botão com ou sem disabled conforme o ramo do if",
    ("parciais/validar_cartao.html", 'class="btn'): "atributos do HTMX em várias linhas",
    ("projeto/lista.html", 'class="btn'): "disabled e title condicionais no botão",
    ("senha_definir.html", 'class="btn'): "<input type=submit> da tela de senha",
    ("_componentes/girando.html", "<svg"): "o spinner tem classe e id condicional; já é um include",
    ("_componentes/ordem.html", "<svg"): "a alça de arrastar é preenchida (fill), não de traço",
    ("parciais/matriz_painel.html", '<dialog class="dialogo'): "atributos condicionais na tag (impacto do item da tarefa)",
    ("parciais/matriz_tarefa.html", 'class="btn-icone'): "é o <c-botao variante=ghost> quadrado da tarefa, com a classe só para o tamanho",
    ("projeto/projeto.html", 'class="campo'): "a caixa do campo é o próprio <form> do autosave da matriz",
}


def tem_cru(cru, texto):
    """A classe do componente como palavra inteira: `class="card` não casa com `class="card-estreito`."""
    return re.search(re.escape(cru) + r'(?=[ "{])', texto) is not None


class CatracaDosComponentes(SimpleTestCase):
    def test_tela_nao_escreve_a_mao_componente_migrado(self):
        achados = []
        for arquivo in sorted(UI.rglob("*.html")):
            relativo = arquivo.relative_to(UI).as_posix()
            for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
                for cru, componente in MIGRADOS.items():
                    if tem_cru(cru, linha) and (relativo, cru) not in EXCECOES:
                        achados.append(f"{relativo}:{n}: {cru!r} escrito à mão; use {componente}")
        self.assertEqual(achados, [], "\n" + "\n".join(achados))

    def test_excecao_ainda_existe(self):
        """Exceção que não casa com mais nada é lixo: apague a linha."""
        sobrando = [
            f"{relativo}: {cru!r}"
            for relativo, cru in EXCECOES
            if not tem_cru(cru, (UI / relativo).read_text(encoding="utf-8"))
        ]
        self.assertEqual(sobrando, [])


def renderizar(fonte, **contexto):
    return Template(CottonCompiler().process(fonte)).render(Context(contexto))


class NomesDosIcones(SimpleTestCase):
    def test_todo_icone_usado_existe(self):
        """Nome errado renderiza um svg vazio, sem erro: o teste pega."""
        modelos = UI.parent
        existentes = set(re.findall(r'nome == "([\w-]+)"', (modelos / "cotton" / "icone.html").read_text(encoding="utf-8")))
        usados = {
            (arquivo.relative_to(modelos).as_posix(), nome)
            for arquivo in modelos.rglob("*.html")
            for nome in re.findall(r'<c-(?:icone[^>]*[^:]\bnome|botao-icone[^>]*\bicone)="([^"]*)"', arquivo.read_text(encoding="utf-8"))
        }
        self.assertTrue(usados)
        self.assertEqual(sorted(u for u in usados if u[1] not in existentes), [])


    def test_todo_botao_de_icone_tem_rotulo(self):
        """Botão sem texto e sem aria-label não existe para leitor de tela."""
        sem = [
            f"{arquivo.relative_to(UI).as_posix()}: {tag[:80]}"
            for arquivo in UI.rglob("*.html")
            for tag in re.findall(r"<c-botao-icone\b[^>]*>", arquivo.read_text(encoding="utf-8"))
            if not re.search(r'\brotulo="[^"]+"', tag)
        ]
        self.assertEqual(sem, [])


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
        self.assertEqual(
            renderizar('<c-badge variante="secundario" class="tpl-chip">x</c-badge>'),
            '<span class="badge badge-secundario tpl-chip">x</span>',
        )

    def test_aviso(self):
        self.assertEqual(
            renderizar('<c-aviso tag="p" variante="erro" role="alert">{{ x }}</c-aviso>', x=self.perigoso),
            '<p class="aviso aviso-erro" role="alert">A &amp; B &lt;i&gt;</p>',
        )
        self.assertEqual(renderizar('<c-aviso role="status"><p>x</p></c-aviso>'), '<div class="aviso" role="status"><p>x</p></div>')

    def test_botao_icone(self):
        svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        self.assertEqual(
            renderizar('<c-botao-icone icone="fechar" href="/x" target="_blank" rotulo="Excluir {{ n }}" dica="Excluir" />', n="A & B"),
            '<a class="btn-icone" href="/x" target="_blank" aria-label="Excluir A &amp; B" data-dica="Excluir">'
            + svg + '<path d="M18 6 6 18M6 6l12 12"/></svg></a>',
        )
        self.assertEqual(
            renderizar('<c-botao-icone icone="fechar" type="submit" class="tpl-excluir" name="acao" value="ativar" rotulo="Ativar" />'),
            '<button class="btn-icone tpl-excluir" type="submit" name="acao" value="ativar" aria-label="Ativar">'
            + svg + '<path d="M18 6 6 18M6 6l12 12"/></svg></button>',
        )

    def test_modal(self):
        html = renderizar(
            '<c-modal id="dlg-x" titulo="Atribuir" class="impacto" x-data="impacto"><c-slot name="descricao"><p class="mudo">d</p></c-slot>'
            '<p>corpo</p><c-slot name="rodape"><button>ok</button></c-slot></c-modal>'
        )
        self.assertInHTML(
            '<dialog class="dialogo impacto" id="dlg-x" aria-labelledby="dlg-x-titulo" x-data="impacto">'
            '<header><h2 id="dlg-x-titulo">Atribuir</h2><p class="mudo">d</p></header><p>corpo</p>'
            "<footer><button>ok</button></footer></dialog>",
            html,
        )
        casca = renderizar('<c-modal id="dlg-nova"><form>f</form></c-modal>')
        self.assertInHTML('<dialog class="dialogo" id="dlg-nova" aria-labelledby="dlg-nova-titulo"><form>f</form></dialog>', casca)
        self.assertNotIn("<header>", casca)
        self.assertNotIn("<footer>", casca)
        outro_id = renderizar('<c-modal titulo="Sair" titulo_id="sair-titulo"></c-modal>')
        self.assertIn('<dialog class="dialogo" aria-labelledby="sair-titulo">', outro_id)
        self.assertIn('<h2 id="sair-titulo">Sair</h2>', outro_id)

    def test_icone(self):
        svg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"{}>'
        self.assertEqual(renderizar('<c-icone nome="check" />'), svg.format("2", "") + '<path d="M20 6 9 17l-5-5"/></svg>')
        self.assertEqual(
            renderizar('<c-icone nome="mais" espessura="2.5" width="16" />'),
            svg.format("2.5", ' width="16"') + '<path d="M5 12h14"/><path d="M12 5v14"/></svg>',
        )
        self.assertEqual(renderizar('<c-botao><c-icone nome="fechar" />Fechar</c-botao>').count("<svg"), 1)

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
        self.assertEqual(
            renderizar('<c-botao variante="ghost" class="btn-icone x" ::disabled="ocupado" @click="salvar">ok</c-botao>'),
            '<button type="button" class="btn btn-ghost btn-icone x" :disabled="ocupado" @click="salvar">ok</button>',
        )

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
        self.assertEqual(
            renderizar('<c-card tag="main" class="entrar-card"><p>x</p></c-card>').replace("\n", "").replace("  ", ""),
            '<main class="card entrar-card"><p>x</p></main>',
        )
