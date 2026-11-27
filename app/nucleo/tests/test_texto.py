import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase

from nucleo.management.commands.carregar_templates import AVISO
from nucleo.models import Ano, Componente, Template, TemplateVersao
from nucleo.texto import SECOES_F2, html_para_texto, partes, renderizar, renderizar_texto_puro, secoes, validar, variaveis_usadas

F1 = "## introducao\nTítulo\n\nCorpo da {{nome_parceiro}}.\n\n- um\n- dois\n"
F2_NOVO = "".join(f"## {i}\n{'F' if i.startswith('fechamento') else 'T'}\n\nx\n\n" for i in SECOES_F2).rstrip("\n") + "\n"
ORIGINAL = Path.read_text
SEED = settings.BASE_DIR / "templates_seed" / "2026"


class ValidarTest(SimpleTestCase):
    def erros(self, texto, fasciculo="F1"):
        with self.assertRaises(ValidationError) as cm:
            validar(texto, fasciculo)
        return " ".join(cm.exception.messages)

    def test_valido(self):
        validar(F1, "F1")
        validar(F2_NOVO, "F2")

    def test_secoes_titulo_e_corpo(self):
        self.assertEqual(secoes(F1)["introducao"], ("Título", "Corpo da {{nome_parceiro}}.\n\n- um\n- dois"))
        self.assertEqual(variaveis_usadas(F1), {"nome_parceiro"})

    def test_secao_faltando(self):
        self.assertIn("Seções obrigatórias faltando: introducao.", self.erros("## fechamento\nT\n\nx\n"))
        self.assertIn("Seções não previstas no F1: fechamento.", self.erros("## introducao\nT\n\nx\n\n## fechamento\nF\n\ny\n"))
        sem = F2_NOVO.replace("## fechamento-alfa\nF\n\nx\n\n", "")
        self.assertIn("Seções obrigatórias faltando: fechamento-alfa.", self.erros(sem, "F2"))

    def test_f2_recusa_ids_antigos(self):
        antigo = F2_NOVO + "\n## passo1\nP\n\nx\n"
        self.assertIn("Seções não previstas no F2: passo1.", self.erros(antigo, "F2"))

    def test_secao_estranha_repetida_e_texto_solto(self):
        e = self.erros("solto\n" + F1 + "## extra\nT\n\nx\n## extra\nT\n\ny\n")
        self.assertIn("antes da primeira", e)
        self.assertIn("repetida: extra", e)
        self.assertIn("não previstas no F1: extra", e)

    def test_variavel_inexistente(self):
        self.assertIn("{{inexistente}}", self.erros(F1 + "{{inexistente}} {{ nome_parceiro }} {{x"))

    def test_gentilico_saiu_da_lista(self):  # virou adjetivo_patrio_* (lista oficial)
        self.assertIn("{{gentilico_masc_sing}}", self.erros(F1 + "{{gentilico_masc_sing}}"))
        self.assertIn("{{parceiro}}", self.erros(F1 + "{{parceiro}}"))  # virou nome_parceiro
        validar(F1 + "{{adjetivo_patrio_singular_masculino}} {{issn}} {{no_na_em_nome_parceiro}}", "F1")

    def test_recusa_recursos_fora_do_formato(self):
        for trecho, nome in [
            ("# Título", "título"),
            ("Sub\n---", "título"),
            ("[a](http://x)", "link"),
            ("<http://x>", "link"),
            ("![i](x.png)", "imagem"),
            ("<script>alert(1)</script>", "HTML"),
            ("texto <b>x</b>", "HTML"),
            ("`código`", "code_inline"),
            ("> citação", "blockquote"),
        ]:
            with self.subTest(trecho):
                self.assertIn(nome, self.erros(F1.replace("- dois", f"- dois\n\n{trecho}")))

    def test_link_so_https_ou_pendente(self):  # D-307
        validar(F1 + "\n[**Acesse** o template](https://caed.example/t?a=1&b=2) e [atividades](#pendente).", "F1")
        for href in ("http://x", "#outro", "/local", "mailto:a@b.c"):
            with self.subTest(href):
                self.assertIn(f"link só com https://… ou #pendente; tem {href}", self.erros(F1 + f"\n[a]({href})"))
        self.assertIn("título é texto puro", self.erros(F1.replace("Título", "[T](https://x.y)")))

    def test_chaves_soltas_controle_bidi_e_referencia(self):
        self.assertIn("chaves soltas", self.erros(F1 + "{{{nome_parceiro}}}"))
        self.assertIn("bidi", self.erros(F1 + "a\u202eb"))
        self.assertIn("controle", self.erros(F1 + "a\x07b"))
        self.assertIn("referência de link", self.erros(F1 + "\n[x]: http://mal\n"))

    def test_bom_e_variaveis_usadas_so_da_lista(self):
        validar("\ufeff" + F1, "F1")
        self.assertEqual(variaveis_usadas(F1 + "{{inexistente}}"), {"nome_parceiro"})

    def test_chaves_sem_redos(self):
        inicio = time.monotonic()
        self.assertIn("chaves soltas", self.erros(F1 + "{{" * 40000))
        self.assertLess(time.monotonic() - inicio, 1)

    def test_titulo_e_texto_puro(self):
        self.assertIn("título é texto puro", self.erros(F1.replace("Título", "**Título**")))

    def test_seeds_validos(self):
        for nome in ["f1-lp", "f1-mt", "f2-lp", "f2-mt"]:
            with self.subTest(nome):
                texto = AVISO.sub("", (SEED / f"{nome}.hbs").read_text())
                validar(texto, nome[:2].upper())
                for _, corpo in secoes(texto).values():  # nenhum ** desbalanceado
                    self.assertNotIn("*", renderizar(corpo, {}))


class RenderizarTest(SimpleTestCase):
    def test_script_vira_texto(self):
        html = renderizar("<script>alert(1)</script>", {})
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_valor_nao_vira_formatacao(self):
        html = renderizar("Oi {{nome_parceiro}}", {"nome_parceiro": "_a_ *b* **c** <i>d</i>"})
        self.assertEqual(html, "<p>Oi _a_ *b* **c** &lt;i&gt;d&lt;/i&gt;</p>\n")

    def test_negrito_com_valor_escapado(self):
        html = renderizar("**{{nome_parceiro}}** e _{{ano}}_", {"nome_parceiro": "A<B", "ano": 2026})
        self.assertEqual(html, "<p><strong>A&lt;B</strong> e <em>2026</em></p>\n")

    def test_sem_escape_duplo(self):
        html = renderizar("P & Q: {{nome_parceiro}}", {"nome_parceiro": "Pais & Filhos"})
        self.assertEqual(html, "<p>P &amp; Q: Pais &amp; Filhos</p>\n")
        self.assertNotIn("&amp;amp;", html)

    def test_marcador_do_usuario_nao_colide(self):
        html = renderizar("x0 {{nome_parceiro}}", {"nome_parceiro": "GO"})
        self.assertEqual(html, "<p>x0 GO</p>\n")

    def test_entidade_nao_forja_marcador(self):
        html = renderizar("&#xE000;99&#xE001;", {})  # antes: IndexError
        self.assertIn("99", html)
        html = renderizar("x &#xE000;0&#xE001; {{nome_parceiro}}", {"nome_parceiro": "GO"})
        self.assertEqual(html.count("GO"), 1)  # antes: "x GO GO"

    def test_valor_so_com_espacos_e_vazio(self):
        self.assertIn("variavel-vazia", renderizar("{{nome_parceiro}}", {"nome_parceiro": "  "}))

    def test_lista_e_variavel_vazia(self):
        html = renderizar("- {{nome_parceiro}}\n- b", {})
        self.assertIn('<li><span class="variavel-vazia">{{nome_parceiro}}</span></li>', html)

    def test_link_https_abre_em_outra_aba_e_pendente_sai_como_variavel_vazia(self):  # D-307
        html = renderizar("[**Acesse** já](https://a.b/c?d=1&e=2) [o modelo](#pendente)", {})
        self.assertEqual(
            html,
            '<p><a href="https://a.b/c?d=1&amp;e=2" target="_blank" rel="noopener"><strong>Acesse</strong> já</a> '
            '<span class="variavel-vazia">o modelo</span></p>\n',
        )
        self.assertEqual(html_para_texto(html), "[**Acesse** já](https://a.b/c?d=1&e=2) o modelo")

    def test_link_fora_da_regra_nao_vira_link(self):  # escapou da validação
        self.assertEqual(renderizar("[a](http://x)", {}), "<p><span>a</span></p>\n")
        self.assertNotIn("<a", renderizar("[a](javascript:alert(1))", {}))

    def test_titulo_texto_puro(self):
        self.assertEqual(renderizar_texto_puro("**R&D** {{nome_parceiro}}", {"nome_parceiro": "<GO>"}), "**R&amp;D** &lt;GO&gt;")


class PartesTest(SimpleTestCase):
    def test_diff_por_palavra_com_o_espaco_que_a_segue(self):
        self.assertEqual(
            partes("o gato comeu tudo", "o cão comeu tudo hoje"),
            [("igual", "o "), ("del", "gato "), ("ins", "cão "), ("igual", "comeu tudo "), ("ins", "hoje")],
        )

    def test_acrescimo_no_fim_nao_marca_a_ultima_palavra(self):
        self.assertEqual(partes("em um texto.", "em um texto. TESTE"), [("igual", "em um texto. "), ("ins", "TESTE")])

    def test_corte_no_fim_nao_marca_a_palavra_que_ficou(self):
        self.assertEqual(partes("em um texto. TESTE", "em um texto."), [("igual", "em um texto. "), ("del", "TESTE")])


class CarregarTemplatesTest(TestCase):
    def carregar(self):
        saida = StringIO()
        call_command("carregar_templates", "--ano", "2026", stdout=saida)
        return saida.getvalue()

    def test_erro_claro_sem_cadastro(self):
        with self.assertRaisesMessage(CommandError, "Ano 2026 não cadastrado"):
            self.carregar()
        ano = Ano.objects.create(ano=2026)
        Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        with self.assertRaisesMessage(CommandError, "Componente MT não cadastrado"):
            self.carregar()
        self.assertFalse(Template.objects.exists())  # tudo ou nada

    def test_idempotente_e_nunca_sobrescreve(self):
        ano = Ano.objects.create(ano=2026)
        for cc in ["LP", "MT"]:
            Componente.objects.create(ano=ano, codigo=cc, nome=cc)
        self.carregar()
        self.assertEqual(Template.objects.count(), 4)
        self.assertEqual(TemplateVersao.objects.filter(numero=1).count(), 4)
        t = Template.objects.get(componente__codigo="MT", fasciculo="F2")
        self.assertEqual(t.origem, "templates_seed/2026/f2-mt.hbs")
        v1 = TemplateVersao.objects.get(template=t)
        self.assertNotIn("<!--", v1.texto)
        self.assertIsNone(v1.criada_por)

        TemplateVersao.objects.create(template=t, numero=2, texto=v1.texto + "\nEditado.")
        self.assertNotIn("aviso", self.carregar())
        # seed editado no arquivo depois da carga: avisa e não grava
        with patch("pathlib.Path.read_text", autospec=True, side_effect=lambda p, **k: ORIGINAL(p, **k) + "\nNovo."):
            self.assertIn("f2-mt.hbs difere da versão 1", self.carregar())
        self.assertEqual(TemplateVersao.objects.count(), 5)
        self.assertEqual(Template.objects.count(), 4)
        self.assertEqual(TemplateVersao.objects.count(), 5)
