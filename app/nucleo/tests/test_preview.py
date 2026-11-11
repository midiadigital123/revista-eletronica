import io
import json
import os
import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from nucleo.management.commands import criar_demo
from nucleo.models import (
    FotoRevista,
    Revista,
    RevistaFasciculo,
    RevistaInfografico,
    RevistaInfograficoEtapa,
    RevistaInfograficoItem,
    Tarefa,
    TemplateVersao,
)
from nucleo.servicos.arquivos import receber_capa
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.html import contexto_pagina, css_das_cores, link_zip, paginas, template
from nucleo.servicos.pendencias import pendencias
from nucleo.models.revista import Motivo
from nucleo.servicos.resolver import resolver
from nucleo.tests.test_resolver import MediaTemporaria, Mundo

# Páginas que o Playwright pagina.spec.ts abre (gabarito). Regerar: REGERAR_FIXTURES=1.
GABARITO = Path(__file__).resolve().parents[2] / "e2e" / "fixtures" / "pagina"
DOCX = criar_demo.DOCX
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
F2 = (
    "## abertura\nAvaliação & Currículo\n\nSiga o tour.\n\nSegundo parágrafo.\n\n"
    "## passo-descritor\nDescritor\n\nO descritor.\n\n## passo-habilidades\nHabilidades\n\nAs habilidades.\n\n"
    "## passo-progressao\nProgressão\n\nA progressão.\n\n## passo-tarefas\nTarefas\n\nAs tarefas.\n\n"
    "## dlg-descritor\nSobre o descritor\n\nDetalhe do descritor.\n\n## dlg-tarefas\nTarefas por nível\n\nOs itens.\n\n"
    "## tarefas-fechamento\nFechamento das tarefas\n\nCompare os itens.\n\n## fechamento\nAgora é com você\n\nUse o template.\n"
)


def dois_infograficos(revista):
    """Alfa (criado aqui: o Mundo não tem 2EF) e Outras com os dados do docx de LP 2026 (D-248).

    Os dois têm os mesmos dados; só a habilidade do Alfa leva "(alfa)", para os testes provarem que
    cada página mostra o seu. Nada depende do pk: os gabaritos ficam determinísticos.
    """
    RevistaInfografico.objects.get_or_create(
        revista=revista, tipo="alfa", defaults={"componente_id": revista.componente_id, "ano_id": revista.ano_id}
    )
    criar_demo.preencher_infograficos(revista, "infograficos/{tipo}-{p}.png")
    RevistaInfografico.objects.filter(revista=revista, tipo="alfa", arquivado_em__isnull=True).update(
        habilidade=DOCX["habilidade"] + " (alfa)"
    )
    gravar_imagens(revista)


def gravar_imagens(revista):
    """Grava o PNG do criar_demo no caminho exato de cada item com imagem da revista."""
    for caminho in RevistaInfograficoItem.objects.filter(infografico__revista=revista).exclude(imagem=None).values_list("imagem", flat=True):
        default_storage.delete(caminho)
        default_storage.save(caminho, ContentFile(criar_demo.PNG))


def foto_antiga(revista):
    """Reescreve a foto de arquivamento no formato de antes da D-237: f2 com o SVG e sem `infograficos`."""
    foto = FotoRevista.objects.filter(revista=revista, motivo=Motivo.ARQUIVAMENTO).latest("criada_em", "pk")
    foto.conteudo["f2"] = {"secoes": foto.conteudo["f2"]["secoes"], "svg_sha256": "a" * 64, "svg_ids": []}
    FotoRevista.objects.filter(pk=foto.pk).update(conteudo=foto.conteudo)


class PaginaTest(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.rev = cls.go["LP"]
        cls.usuario.user_permissions.add(Permission.objects.get(codename="view_revista"))
        TemplateVersao.objects.create(template=cls.templates["LP", "F2"], numero=2, texto=F2)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.usuario)

    def get(self, revista, pagina="index"):
        if pagina == "index":
            return self.client.get(reverse("preview", args=[revista.pk]))
        if pagina == "f1":
            return self.client.get(reverse("preview_f1", args=[revista.pk]))
        return self.client.get(reverse("preview_f2", args=[revista.pk, pagina]))

    def test_login_obrigatorio(self):
        self.client.logout()
        for pagina in ("index", "f1", "outras"):
            r = self.get(self.rev, pagina)
            self.assertEqual(r.status_code, 302)
            self.assertIn("/conta/entrar/", r["Location"])
        r = self.imagem(self.rev, "alfa-1.png")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/conta/entrar/", r["Location"])

    def test_sem_view_revista_403(self):
        staff = get_user_model().objects.create(username="staff", is_staff=True)  # sem grupo
        self.client.force_login(staff)
        for pagina in ("index", "f1", "outras"):
            self.assertEqual(self.get(self.rev, pagina).status_code, 403)
        self.assertEqual(self.client.get(reverse("preview_capa", args=[self.rev.pk])).status_code, 403)
        dois_infograficos(self.rev)
        self.assertEqual(self.imagem(self.rev, "alfa-1.png").status_code, 403)

    def test_capa_sumida_404(self):
        receber_capa(self.rev, SimpleUploadedFile("capa.png", PNG))
        self.rev.refresh_from_db()
        default_storage.delete(self.rev.capa)
        self.assertEqual(self.get(self.rev).status_code, 200)  # a página abre; só a capa falha
        self.assertEqual(self.client.get(reverse("preview_capa", args=[self.rev.pk])).status_code, 404)

    def test_sumario_lista_as_paginas(self):
        dois_infograficos(self.rev)
        html = self.get(self.rev).content.decode()
        sumario = re.search(r'<nav[^>]*aria-label="Sumário"[^>]*>(.*?)</nav>', html, re.S).group(1)
        self.assertEqual(
            re.findall(r'href="([^"]+)"', sumario),
            [reverse("preview_f1", args=[self.rev.pk]), reverse("preview_f2", args=[self.rev.pk, "alfa"]),
             reverse("preview_f2", args=[self.rev.pk, "outras"])],
        )  # fmt: skip
        self.assertIn("Avaliação e Currículo – Alfa", sumario)
        self.assertNotIn('id="dados-revista"', html)
        self.assertNotIn("Voltar ao sumário", html)

    def test_f2_tipo_inexistente_404(self):
        self.assertEqual(self.get(self.rev, "outras").status_code, 200)
        self.assertEqual(self.get(self.rev, "alfa").status_code, 404)  # o Mundo não tem 2EF
        self.assertEqual(self.get(self.rev, "beta").status_code, 404)
        self.assertEqual(self.get(self.rev, "f1").status_code, 200)
        self.assertEqual(self.client.get(f"{reverse('preview', args=[self.rev.pk])}f2/f1/").status_code, 404)

    def test_f1_inline(self):
        r = self.get(self.rev, "f1")
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('id="dados-revista"', html)
        self.assertIn("<p>Texto <strong>Projeto GO</strong>.</p>", html)  # introdução, sem reescapar
        self.assertIn(f'href="{reverse("preview", args=[self.rev.pk])}"', html)  # voltar ao sumário
        self.assertIn("/static/revista/f1/script.js", html)
        self.assertNotIn("svg-tour.js", html)
        self.assertNotIn("dados-tour", html)
        self.assertNotIn("faixa-vermelha", html.split("<body>")[1])
        self.assertNotIn("fetch(", html)

    def test_f2_svg_gerado_tour_e_modais(self):
        dois_infograficos(self.rev)
        r = self.get(self.rev, "outras")
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('<h1 id="f2-titulo">Avaliação e Currículo – Outras Etapas</h1>', html)
        self.assertIn("<p>Siga o tour.</p>", html)  # a abertura em texto corrido
        self.assertIn('<div id="revista"><svg', html)
        self.assertIn('id="f2-descritor"', html)
        self.assertIn('<dialog id="dlg-descritor" aria-labelledby="dlgTitle-descritor">', html)
        self.assertIn('<h3 id="dlgTitle-tarefa-1">', html)
        self.assertIn("Agora é com você", html)  # o fechamento do F2
        self.assertIn(f'class="f2-hab">{DOCX["habilidade"]}</div>', html)
        self.assertNotIn("(alfa)", html)
        self.assertIn("/static/revista/f2/f2-init.js", html)
        self.assertNotIn("f1/script.js", html)
        self.assertNotIn("dados-revista", html)
        self.assertNotIn("faixa-vermelha", html.split("<body>")[1])
        self.assertNotIn("fetch(", html)
        self.assertNotIn("Fechamento das tarefas", html)  # a seção vai sem título (D-258)
        # A ordem do f2.html: título, abertura, SVG, fechamento das tarefas, modais, fechamento, scripts.
        ordem = ['id="f2-titulo"', "Siga o tour.", '<div id="revista">', '<div class="f2-abertura f2-tarefas-fechamento"><p>Compare os itens.</p>',
                 '<dialog id="dlg-descritor"', "Agora é com você", 'id="dados-tour"', "f2/svg-tour.js"]  # fmt: skip
        self.assertEqual([html.index(t) for t in ordem], sorted(html.index(t) for t in ordem))
        # Imagem do item: <base_imagens><nome>, sem "infograficos/" duplicado (D-244).
        base = f"{reverse('preview', args=[self.rev.pk])}arquivos/infograficos/"
        self.assertIn(f'<img src="{base}outras-1.png" alt="{DOCX["itens"][0]["texto_alternativo"]}">', html)
        self.assertNotIn("infograficos/infograficos/", html)
        tour = json.loads(re.search(r'id="dados-tour" type="application/json">(.*?)</script>', html).group(1))
        # Texto puro (textContent); o cartão vai só com o título: a abertura já está na página (D-258).
        self.assertEqual(tour["intro"], {"title": "Avaliação & Currículo", "text": ""})
        self.assertEqual([s["target"] for s in tour["steps"]], ["f2-descritor", "f2-habilidades", "f2-progressao", "f2-tarefas"])
        self.assertEqual(set(tour), {"label", "intro", "steps", "modais"})
        # O modal ❶ é o template + só o 4º parágrafo do docx: o texto genérico não se repete (D-258).
        self.assertNotIn("O desenvolvimento das habilidades previstas", html)
        self.assertEqual(html.count("Como exemplo dessa trajetória"), 1)

    def test_fechamento_das_tarefas_some_com_o_passo_desligado(self):
        dois_infograficos(self.rev)
        RevistaInfografico.objects.filter(revista=self.rev, tipo="outras").update(passos_desligados=["tarefas"])
        html = self.get(self.rev, "outras").content.decode()
        self.assertNotIn("Compare os itens.", html)
        self.assertIn("Agora é com você", html)

    def test_titulo_e_h1_por_pagina(self):
        """Acessibilidade: cada página tem o próprio <title> e um h1."""
        dois_infograficos(self.rev)
        esperado = {
            "index": "Análise de GO",
            "f1": "Escalas de proficiência – Análise de GO",
            "outras": "Avaliação e Currículo – Outras Etapas – Análise de GO",
        }
        for pagina, titulo in esperado.items():
            html = self.get(self.rev, pagina).content.decode()
            self.assertIn(f"<title>{titulo}</title>", html)
            self.assertEqual(html.count("<h1"), 1, pagina)

    def test_faixa_vermelha_sem_template(self):
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F1").update(template=None)
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F2").update(template=None)
        self.assertIn("Falta escolher o template do F1.", self.get(self.rev, "f1").content.decode())
        html = self.get(self.rev, "outras").content.decode()
        self.assertIn("Falta escolher o template do F2.", html)
        self.assertNotIn("Falta o SVG do F2.", html)

    def test_faixa_vermelha_sem_matriz(self):
        """Item 21 (D-190): sem matriz o F1 sai sem descritores; a faixa diz o que falta. Ela fica
        fora do resolvido (senão o hash de toda revista muda e todas perdem o "Validado")."""
        self.assertNotIn("Falta escolher a matriz", self.get(self.rev, "f1").content.decode())
        pa = self.rev.projeto.parceiro_ano
        pa.matriz = None
        pa.save(update_fields=["matriz"])
        html = self.get(self.rev, "f1").content.decode()
        self.assertIn("Falta escolher a matriz (5EF, 9EF).", html)
        self.assertNotIn("Falta escolher a matriz", json.dumps(resolver(Revista.objects.get(pk=self.rev.pk)), ensure_ascii=False))

    def test_arquivada_mostra_a_foto(self):
        mt = self.go["MT"]
        # Tira a MT dos cortes: a cascata arquiva e fotografa (D-117); depois o template muda.
        gravar_cortes(
            self.rev.projeto.parceiro_ano,
            [(self.e5, self.lp, [100, 200, 250, 300]), (self.e9, self.lp, [100, 200, 250, 300])],
            self.usuario,
        )
        TemplateVersao.objects.create(
            template=self.templates["MT", "F1"], numero=2,
            texto="## introducao\nNovo título\n\nTexto novo.\n\n## fechamento\nFim\n\nFim.\n",
        )  # fmt: skip
        self.assertIsNotNone(Revista.objects.get(pk=mt.pk).arquivada_em)
        for pagina in ("index", "f1"):
            html = self.get(mt, pagina).content.decode()
            self.assertIn("Análise de GO", html)
            self.assertNotIn("Texto novo.", html)

    def test_arquivada_mostra_o_infografico_da_foto(self):
        mt = self.go["MT"]
        RevistaInfografico.objects.filter(revista=mt).update(habilidade="Habilidade da foto.")
        gravar_cortes(  # tira a MT dos cortes: a cascata arquiva e fotografa (D-117)
            self.rev.projeto.parceiro_ano,
            [(self.e5, self.lp, [100, 200, 250, 300]), (self.e9, self.lp, [100, 200, 250, 300])],
            self.usuario,
        )
        RevistaInfografico.objects.filter(revista=mt).update(habilidade="Habilidade do banco.")
        mt = Revista.objects.get(pk=mt.pk)
        self.assertIsNotNone(mt.arquivada_em)
        html = self.get(mt, "outras").content.decode()
        self.assertIn("Habilidade da foto.", html)
        self.assertNotIn("Habilidade do banco.", html)

    def test_foto_antiga_sem_paginas_do_f2(self):
        """Foto de antes da D-237 (sem `infograficos`): sumário e F1 abrem, o F2 não existe."""
        mt = self.go["MT"]
        gravar_cortes(
            self.rev.projeto.parceiro_ano,
            [(self.e5, self.lp, [100, 200, 250, 300]), (self.e9, self.lp, [100, 200, 250, 300])],
            self.usuario,
        )
        mt = Revista.objects.get(pk=mt.pk)
        self.assertEqual(self.get(mt, "outras").status_code, 200)  # a foto nova tem o infográfico
        foto_antiga(mt)
        r = self.get(mt)
        self.assertEqual(r.status_code, 200)
        sumario = re.search(r'<nav[^>]*aria-label="Sumário"[^>]*>(.*?)</nav>', r.content.decode(), re.S).group(1)
        self.assertEqual(re.findall(r'href="([^"]+)"', sumario), [reverse("preview_f1", args=[mt.pk])])
        self.assertEqual(self.get(mt, "f1").status_code, 200)
        for tipo in ("alfa", "outras"):
            self.assertEqual(self.get(mt, tipo).status_code, 404)

    def test_item_da_tarefa_pelo_caminho_relativo_do_f1(self):
        """O JS do F1 abre `arquivos/itens/<nome>` relativo à página: `<id>/f1/` também serve o item."""
        nome = "item1.png"
        caminho = default_storage.save(f"itens/{nome}", ContentFile(PNG))
        Tarefa.objects.filter(pk=self.tarefa.pk).update(arquivo=caminho)
        r = self.client.get(f"{reverse('preview_f1', args=[self.rev.pk])}arquivos/itens/{nome}")
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/png"))

    def imagem(self, revista, nome):
        return self.client.get(f"{reverse('preview', args=[revista.pk])}arquivos/infograficos/{nome}")

    def test_imagem_do_item_tipo_fixo_e_nosniff(self):
        dois_infograficos(self.rev)
        self.assertIn(f'src="{reverse("preview", args=[self.rev.pk])}arquivos/infograficos/alfa-1.png"',
                      self.get(self.rev, "alfa").content.decode())  # fmt: skip
        r = self.imagem(self.rev, "alfa-1.png")
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/png"))
        self.assertEqual(b"".join(r.streaming_content), criar_demo.PNG)
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r["Content-Security-Policy"], "default-src 'none'; sandbox")

    def test_imagem_de_outra_revista_404(self):
        dois_infograficos(self.rev)
        self.assertEqual(self.imagem(self.go["MT"], "alfa-1.png").status_code, 404)

    def test_imagem_sumida_404_e_pagina_abre(self):
        dois_infograficos(self.rev)
        default_storage.delete("infograficos/alfa-1.png")
        self.assertEqual(self.get(self.rev, "alfa").status_code, 200)
        self.assertEqual(self.imagem(self.rev, "alfa-1.png").status_code, 404)

    def test_imagem_nome_parcial_e_nul_404(self):
        """O nome casa inteiro (lfa-1.png não serve alfa-1.png); NUL no nome é 404, não 500 do PostgreSQL."""
        dois_infograficos(self.rev)
        self.assertEqual(self.imagem(self.rev, "lfa-1.png").status_code, 404)
        self.assertEqual(self.imagem(self.rev, "a%00.png").status_code, 404)
        self.assertEqual(self.client.get(f"{reverse('preview', args=[self.rev.pk])}arquivos/itens/a%00.png").status_code, 404)

    def test_imagem_de_tipo_nao_imagem_404(self):
        dois_infograficos(self.rev)
        RevistaInfograficoItem.objects.filter(infografico__revista=self.rev, posicao=1).update(imagem="infograficos/x.svg")
        default_storage.save("infograficos/x.svg", ContentFile(b'<svg xmlns="http://www.w3.org/2000/svg"/>'))
        self.assertEqual(self.imagem(self.rev, "x.svg").status_code, 404)

    def test_capa_com_tipo_fixo_e_nosniff(self):
        receber_capa(self.rev, SimpleUploadedFile("capa.jpg", PNG))
        self.assertIn(reverse("preview_capa", args=[self.rev.pk]), self.get(self.rev).content.decode())
        r = self.client.get(reverse("preview_capa", args=[self.rev.pk]))
        self.assertEqual((r.status_code, r["Content-Type"]), (200, "image/png"))
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r["Cache-Control"], "private, no-store")
        self.assertEqual(r["Content-Security-Policy"], "default-src 'none'; sandbox")

    def test_gabarito_do_playwright(self):
        """Modo zip (S15): caminhos relativos e sem faixas; o Playwright abre estas páginas."""
        dois_infograficos(self.rev)
        rev = Revista.objects.get(pk=self.rev.pk)
        slugs = [slug for slug, _ in paginas(resolver(rev))]
        self.assertEqual(slugs, ["index", "f1", "f2-alfa", "f2-outras-etapas"])
        for slug in slugs:
            ctx = contexto_pagina(rev, slug, preview=False, estaticos="revista/", capa="arquivos/capa.png",
                                  link=link_zip, base_imagens="arquivos/infograficos/")  # fmt: skip
            html = render_to_string(template(slug), ctx)
            arquivo = GABARITO / link_zip(slug)
            if os.environ.get("REGERAR_FIXTURES"):
                GABARITO.mkdir(exist_ok=True)
                arquivo.write_text(html, encoding="utf-8")
            self.assertEqual(arquivo.read_text(encoding="utf-8"), html, slug)

    def test_script_no_dado_nao_fecha_o_script(self):
        ctx = contexto_pagina(self.rev, "f1", preview=False, estaticos="revista/", capa=None,
                              link=link_zip, base_imagens="arquivos/infograficos/")  # fmt: skip
        ctx["dados"] = {"x": "</script><!--&\u2028"}
        html = render_to_string("revista/f1.html", ctx)
        # O primeiro </script> depois da abertura é o fechamento real: o dado veio escapado.
        corpo = re.search(r'id="dados-revista" type="application/json">(.*?)</script>', html).group(1)
        self.assertEqual(json.loads(corpo), ctx["dados"])


class PaginasTest(SimpleTestCase):
    """Sumário: index, f1 e um infográfico por página, na ordem do resolvido."""

    def test_0_1_e_2_infograficos(self):
        base = [("index", "Sumário"), ("f1", "Escalas de proficiência")]
        alfa = {"tipo": "alfa", "titulo": "Alfa"}
        outras = {"tipo": "outras", "titulo": "Outras"}
        self.assertEqual(paginas({"f2": {"secoes": None, "infograficos": []}}), base)
        self.assertEqual(paginas({"f2": {"infograficos": [outras]}}), [*base, ("f2-outras-etapas", "Outras")])
        self.assertEqual(
            paginas({"f2": {"infograficos": [alfa, outras]}}),
            [*base, ("f2-alfa", "Alfa"), ("f2-outras-etapas", "Outras")],
        )

    def test_foto_antiga_so_index_e_f1(self):
        """Ponto de revisão 2: foto sem a chave `infograficos` (com svg_sha256)."""
        foto = {"f2": {"secoes": [], "svg_sha256": "a" * 64}}
        self.assertEqual([s for s, _ in paginas(foto)], ["index", "f1"])


class HtmlTest(TestCase):
    def test_css_das_cores_n_padroes(self):
        css = css_das_cores({"padrao-2": "#FF8D43", "padrao-1": "#F72628"})
        self.assertEqual(
            css,
            ":root{--color-padrao-1:#F72628;--color-padrao-1-bg:rgba(247, 38, 40, 0.1);"
            "--color-padrao-2:#FF8D43;--color-padrao-2-bg:rgba(255, 141, 67, 0.1);}",
        )
        self.assertEqual(css_das_cores({}), "")
        with self.assertRaises(ValueError):
            css_das_cores({"padrao-1": "red;}body{x:y"})
        with self.assertRaises(ValueError):
            css_das_cores({"padrao-١": "#FFFFFF"})  # dígito árabe: \d aceitaria


class CriarDemoTest(MediaTemporaria, TestCase):
    def test_recusa_sem_debug(self):
        with self.assertRaisesMessage(CommandError, "DEBUG"):
            call_command("criar_demo")

    @override_settings(DEBUG=True)
    def test_nao_troca_senha_de_usuario_alheio(self):
        get_user_model().objects.create(username="demo-preview", password="x")
        with self.assertRaisesMessage(CommandError, "não foi criado por este comando"):
            call_command("criar_demo")
        self.assertEqual(get_user_model().objects.get(username="demo-preview").password, "x")

    @override_settings(DEBUG=True)
    def test_infograficos_da_demo_sem_pendencia_e_idempotente(self):
        call_command("criar_demo", stdout=io.StringIO())
        revista = Revista.objects.get(projeto__parceiro_ano__parceiro__nome=criar_demo.PARCEIRO)
        self.assertEqual([p for p in pendencias(revista) if p.codigo == "infografico"], [])

        def contar():
            return (
                RevistaInfograficoEtapa.objects.filter(infografico__revista=revista).count(),
                RevistaInfograficoItem.objects.filter(infografico__revista=revista).count(),
                len(default_storage.listdir("infograficos")[1]),
            )

        antes = contar()
        self.assertEqual(antes[1:], (4, 4))  # só Outras: a demo não tem 2EF
        call_command("criar_demo", stdout=io.StringIO())
        self.assertEqual(contar(), antes)
