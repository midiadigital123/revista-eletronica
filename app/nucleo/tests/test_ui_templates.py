"""Templates B (T12-T14, /ui/templates/): critérios de aceite de docs/telas/fichas/templates.md pelo client."""

import re
from urllib.parse import quote

from django.conf import settings
from django.test import Client
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.management.commands.carregar_templates import AVISO
from nucleo.models import Ano, Bloqueio, Componente, FotoRevista, RevistaFasciculo, RevistaSecao, Template, TemplateVersao
from nucleo.models.revista import Motivo
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import form_para_corpo, secoes_para_form
from nucleo.tests.test_admin_templates import F2_8, F2_NOVO, Base
from nucleo.tests.test_resolver import F1 as F1_NOVO, usuario


class UiBase(Base):
    def setUp(self):
        super().setUp()
        self.editar = reverse("ui_templates_editar", args=[self.tpl.pk])
        self.lista = reverse("ui_templates", args=[2026])

    def sessao(self, cliente=None):
        r = (cliente or self.ped).get(self.editar)
        self.assertEqual(r.status_code, 200)
        return r.wsgi_request.bloqueio["sessao"]

    def post(self, sessao, texto, cliente=None, **extra):
        return (cliente or self.ped).post(self.editar, {"nome": "Padrão", "texto": texto, CAMPO_SESSAO: sessao, **extra})

    def confirmar(self, impacto, **troca):
        self.assertTemplateUsed(impacto, "ui/templates/impacto.html")
        c = impacto.context
        dados = {"nome": c["nome"], "texto": c["texto"], "_impacto": c["assinatura"],
                 CAMPO_SESSAO: impacto.wsgi_request.bloqueio["sessao"], "_confirmar": "1", **troca}  # fmt: skip
        return self.ped.post(self.editar, dados)


class ListaTest(UiBase):
    def test_abas_versao_uso_e_links(self):
        rf = RevistaFasciculo.objects.get(revista=self.pe["LP"], fasciculo="F2")
        RevistaSecao.objects.create(revista_fasciculo=rf, template=self.tpl, secao="passo1", texto="A",
                                    template_versao=TemplateVersao.objects.get(template=self.tpl))  # fmt: skip
        r = self.ped.get(self.lista + "?aba=F2")
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertContains(r, 'aria-current="page">Textos F2')
        self.assertContains(r, f'href="{self.editar}"')
        self.assertContains(r, f'href="/painel/2026/?template={self.tpl.pk}"')
        self.assertContains(r, "usado por 2")
        self.assertContains(r, "(1 com cópia de seção)")
        self.assertContains(r, ">v1<")
        # Auditoria 03/11: as abas são só F1/F2; Matrizes e Variáveis ficam no menu e em Projetos.
        self.assertNotContains(r, 'href="/ui/projeto/ano/2026/variaveis/">Variáveis')
        self.assertContains(r, f'href="{reverse("ui_matriz", args=[2026])}">Matrizes', count=1)  # só a do menu
        self.assertNotContains(self.ped.get(self.lista), f'href="{self.editar}"')  # aba padrão F1
        self.assertRedirects(self.ped.get(reverse("ui_templates_inicio")), self.lista)

    def test_aba_vazia(self):
        Ano.objects.create(ano=2027)  # ano sem templates
        r = self.ped.get(reverse("ui_templates", args=[2027]) + "?aba=F2")
        self.assertContains(r, "Nenhum template F2 neste ano")

    def test_sem_ver_403_e_anonimo_no_login(self):
        sem = Client()
        sem.force_login(usuario("nada"))
        self.assertEqual(sem.get(self.lista).status_code, 403)
        self.assertEqual(sem.get(self.editar).status_code, 403)
        for url in (self.lista, self.editar):
            r = Client().get(url)
            self.assertRedirects(r, f"{reverse('entrar')}?next={url}", fetch_redirect_response=False)
        self.assertEqual(Client().post(reverse("ui_templates_previa", args=[self.tpl.pk]), {"texto": "x"}).status_code, 403)


class EditarTest(UiBase):
    def test_get_com_permissao_editor_e_previa(self):
        r = self.ped.get(self.editar)
        self.assertContains(r, 'name="secao-0-corpo"')
        self.assertContains(r, 'data-acao="variavel"')
        self.assertContains(r, 'hx-trigger="input delay:400ms"')
        self.assertContains(r, 'x-data="editorSecoes"')
        self.assertContains(r, "ui/componentes/editor-secoes.js")
        self.assertContains(r, "nucleo/bloqueio.js")
        self.assertContains(r, '<span class="variavel-vazia">{{adjetivo_patrio_plural_masculino}}</span>')
        self.assertContains(r, "Texto válido para o fascículo.")

    def test_previa_htmx_mostra_erros(self):
        url = reverse("ui_templates_previa", args=[self.tpl.pk])
        r = self.ped.post(url, {"texto": "## abertura\nOi\n\nPara {{ano}}.\n"}, HTTP_HX_REQUEST="true")
        self.assertContains(r, '<span class="variavel-vazia">{{ano}}</span>')
        self.assertContains(r, "Seções obrigatórias faltando: passo-descritor,")
        self.assertNotContains(r, "<html")  # fragmento

    def test_impresso_so_le(self):
        imp = Client()
        imp.force_login(usuario("imp", "Impresso"))
        r = imp.get(self.editar)
        self.assertContains(r, "Só leitura")
        self.assertContains(r, "readonly")
        self.assertNotContains(r, "hx-post")
        self.assertNotContains(r, ">Salvar<")
        self.assertFalse(Bloqueio.objects.exists())
        self.assertEqual(self.post("x", F2_NOVO, imp).status_code, 403)
        self.assertEqual(self.post("x", F2_NOVO, imp, _confirmar="1").status_code, 403)
        self.assertEqual(self.versoes(), 1)

    def test_impacto_e_confirmar_cria_versao(self):
        FotoRevista.objects.create(revista=self.pe["LP"], motivo=Motivo.IMPRESSO, conteudo={}, hash="b" * 64, criada_por=self.usuario)
        sessao = self.sessao()
        r = self.post(sessao, F2_NOVO)
        self.assertTemplateUsed(r, "ui/templates/impacto.html")
        self.assertContains(r, "Confirmar e criar versão 2")
        self.assertNotContains(r, "SVG incompleto")
        self.assertContains(r, "Já tem foto do impresso")
        self.assertContains(r, f'value="{sessao}"')
        self.assertEqual(self.versoes(), 1)  # nada gravado
        r = self.confirmar(r, texto=F2_NOVO.replace("\n", "\r\n"))
        self.assertRedirects(r, self.editar, fetch_redirect_response=False)
        atual = versao_atual(self.tpl.pk)
        self.assertEqual((atual.numero, atual.texto, atual.criada_por.username), (2, F2_NOVO, "ped"))
        self.assertFalse(Bloqueio.objects.exists())  # salvou e liberou
        self.assertContains(self.ped.get(self.editar), "Versão 2 criada.")

    def test_assinatura_que_nao_bate_reabre_o_impacto(self):
        impacto = self.post(self.sessao(), F2_NOVO)
        for troca in ({"_impacto": "adulterada"}, {"texto": F2_NOVO.replace("Novo", "Outro")}):
            with self.subTest(troca):
                r = self.confirmar(impacto, **troca)
                self.assertTemplateUsed(r, "ui/templates/impacto.html")
                self.assertContains(r, "mudou desde a tela de impacto")
        self.assertEqual(self.versoes(), 1)

    def test_voltar_nao_grava_e_mantem_o_texto(self):
        r = self.post(self.sessao(), F2_NOVO, _voltar="1")
        self.assertTemplateUsed(r, "ui/templates/editar.html")
        self.assertContains(r, "Novo {{ano}}")
        self.assertContains(r, "nada foi gravado")
        self.assertEqual(self.versoes(), 1)

    def test_texto_invalido_mostra_erro(self):
        r = self.post(self.sessao(), F2_8.replace("Fim.", "Oi {{x}}."))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/templates/editar.html")
        self.assertContains(r, "Nada foi gravado: corrija os erros marcados.")
        self.assertContains(r, "{{x}}")
        self.assertContains(r, 'aria-invalid="true"')
        self.assertEqual(self.versoes(), 1)

    def test_texto_igual_salva_so_o_nome(self):
        r = self.ped.post(self.editar, {"nome": "Outro", "texto": versao_atual(self.tpl.pk).texto, CAMPO_SESSAO: self.sessao()})
        self.assertRedirects(r, self.editar, fetch_redirect_response=False)
        self.tpl.refresh_from_db()
        self.assertEqual(self.tpl.nome, "Outro")
        self.assertEqual(self.versoes(), 1)

    def test_bloqueio_de_outro_usuario(self):
        mid = Client()
        mid.force_login(usuario("mid", "Mídias Digitais"))
        sessao_mid = self.sessao(mid)
        r = self.ped.get(self.editar)
        self.assertContains(r, "Somente leitura")
        self.assertContains(r, "readonly")
        self.assertNotContains(r, "hx-post")
        r = self.post(sessao_mid, F2_NOVO, _confirmar="1")
        self.assertRedirects(r, self.editar, fetch_redirect_response=False)
        self.assertContains(self.ped.get(self.editar), "perdeu o bloqueio")
        self.assertEqual(self.versoes(), 1)


def form_secoes(secoes, **extra):
    """POST do editor por seção (U9b): secao-N-id/titulo/corpo na ordem da lista."""
    dados = {"nome": "Padrão", **extra}
    for n, (id_, titulo, corpo) in enumerate(secoes):
        dados.update({f"secao-{n}-id": id_, f"secao-{n}-titulo": titulo, f"secao-{n}-corpo": corpo})
    return dados


F2_SECOES = [(x["id"], x["titulo"], x["corpo"]) for x in secoes_para_form(F2_8)]


def erros_da_secao(html, id_):
    return re.search(rf'<div class="tpl-secao-erros" id="erros-{id_}"[^>]*>(.*?)</div>', html, re.S)[1]


class EditorSecoesTest(UiBase):
    """U9b: o editor é por seção; o id é estrutura (hidden), nunca campo editável."""

    def test_ida_e_volta_preserva_seeds(self):
        seeds = sorted((settings.BASE_DIR / "templates_seed" / "2026").glob("*.hbs"))
        self.assertEqual(len(seeds), 4)
        for arquivo in seeds:
            with self.subTest(arquivo.name):
                t = AVISO.sub("", arquivo.read_text(encoding="utf-8-sig"))
                self.assertEqual(form_para_corpo(secoes_para_form(t)), t)

    def test_id_fora_do_permitido_422(self):
        sessao = self.sessao()
        previa = reverse("ui_templates_previa", args=[self.tpl.pk])
        for ruim in ("## passo1", "passo1", "dlg-p2", "introducao", "x y"):
            with self.subTest(ruim):
                secoes = [*F2_SECOES[:2], (ruim, "T", "C.")]
                self.assertEqual(self.ped.post(self.editar, form_secoes(secoes, **{CAMPO_SESSAO: sessao})).status_code, 422)
                self.assertEqual(self.ped.post(previa, form_secoes(secoes)).status_code, 422)
        self.assertEqual(self.versoes(), 1)

    def test_id_nao_aparece_como_campo_editavel(self):
        r = self.ped.get(self.editar)
        html = r.content.decode()
        self.assertNotIn('name="texto"', html)
        editaveis = re.findall(r"<textarea[^>]*>(.*?)</textarea>", html, re.S)
        editaveis += re.findall(r'<input(?![^>]*type="hidden")[^>]*value="([^"]*)"', html)
        self.assertTrue(editaveis)
        self.assertFalse([v for v in editaveis if "## " in v or v.strip() in ("abertura", "passo-descritor", "dlg-descritor")])
        self.assertInHTML('<input type="hidden" name="secao-0-id" value="abertura" data-campo="id">', html)
        self.assertContains(r, "Diálogo do descritor")
        self.assertContains(r, 'name="secao-1-titulo"')
        self.assertNotContains(r, "## passo-descritor")  # nem na prévia

    def test_f2_nao_tem_secao_repetivel(self):
        r = self.ped.get(self.editar)
        self.assertNotContains(r, "Adicionar passo")
        secoes = [*F2_SECOES, ("passo2", "Passo dois", "Novo.")]
        r = self.ped.post(self.editar, form_secoes(secoes, **{CAMPO_SESSAO: self.sessao()}))
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.versoes(), 1)

    def test_texto_igual_pelas_secoes_salva_so_o_nome(self):
        r = self.ped.post(self.editar, form_secoes(F2_SECOES, nome="Outro", **{CAMPO_SESSAO: self.sessao()}))
        self.assertRedirects(r, self.editar, fetch_redirect_response=False)
        self.assertEqual(self.versoes(), 1)

    def test_erro_de_validacao_aparece_na_secao_certa(self):
        secoes = [("abertura", "", "Bem-vindo."), ("passo-descritor", "Descritor", ""), ("dlg-descritor", "Descritor", "Oi {{x}}.")]
        r = self.ped.post(self.editar, form_secoes(secoes, **{CAMPO_SESSAO: self.sessao()}))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/templates/editar.html")
        self.assertContains(r, "Nada foi gravado")
        html = r.content.decode()
        self.assertIn("falta o título", erros_da_secao(html, "abertura"))
        self.assertNotIn("corpo vazio", erros_da_secao(html, "abertura"))  # o corpo não subiu para o título
        self.assertIn("corpo vazio", erros_da_secao(html, "passo-descritor"))
        self.assertIn("{{x}}", erros_da_secao(html, "dlg-descritor"))
        self.assertNotIn("{{x}}", erros_da_secao(html, "passo-descritor"))
        self.assertRegex(html, r'<input[^>]*id="titulo-abertura"[^>]*aria-invalid="true"')
        self.assertRegex(html, r'<textarea[^>]*id="corpo-passo-descritor"[^>]*aria-invalid="true"')
        self.assertNotRegex(html, r'<textarea[^>]*id="corpo-abertura"[^>]*aria-invalid')
        self.assertRegex(html, r'<textarea[^>]*id="corpo-abertura"[^>]*>\s*Bem-vindo.</textarea>')
        self.assertRegex(html, r'(?s)href="#secao-passo-descritor".*?1 erro')  # índice lateral
        self.assertEqual(self.versoes(), 1)

    def test_linha_de_secao_no_texto_nao_parte_a_secao(self):
        secoes = [F2_SECOES[0], ("passo-descritor", "Descritor", "Oi.\n## passo9\nT\n\nC."), *F2_SECOES[2:]]
        r = self.ped.post(self.editar, form_secoes(secoes, **{CAMPO_SESSAO: self.sessao()}))
        self.assertTemplateUsed(r, "ui/templates/editar.html")
        self.assertIn("partiria a seção", erros_da_secao(r.content.decode(), "passo-descritor"))
        self.assertEqual(self.versoes(), 1)

    def test_uma_secao_ativa_por_vez(self):
        """Item 5: só a 1ª seção aparece; as outras ficam `hidden`, mas no form (o Salvar manda tudo)."""
        r = self.ped.get(self.editar)
        html = r.content.decode()
        self.assertRegex(html, r'<section class="tpl-secao" id="secao-abertura"(?![^>]*hidden)[^>]*>')
        for n, id_ in ((1, "passo-descritor"), (5, "dlg-descritor")):
            self.assertRegex(html, rf'<section class="tpl-secao" id="secao-{id_}"[^>]*hidden')
            self.assertContains(r, f'name="secao-{n}-corpo"')
        self.assertRegex(html, r'<a href="#secao-abertura"[^>]*aria-current="true"')
        self.assertNotRegex(html, r'<a href="#secao-passo-descritor"[^>]*aria-current')
        self.assertRegex(html, r'<section class="secao" data-previa="abertura">')  # a prévia filtra pela ativa

    def test_erro_abre_a_primeira_secao_com_erro(self):
        secoes = [F2_SECOES[0], ("passo-descritor", "Descritor", ""), ("dlg-descritor", "Descritor", "Oi {{x}}.")]
        r = self.ped.post(self.editar, form_secoes(secoes, **{CAMPO_SESSAO: self.sessao()}))
        html = r.content.decode()
        self.assertRegex(html, r'<section class="tpl-secao" id="secao-passo-descritor"(?![^>]*hidden)[^>]*>')
        self.assertRegex(html, r'<section class="tpl-secao" id="secao-abertura"[^>]*hidden')
        self.assertRegex(html, r'<section class="tpl-secao" id="secao-dlg-descritor"[^>]*hidden')
        self.assertRegex(html, r'(?s)<a href="#secao-passo-descritor"[^>]*aria-current="true".*?1 erro')  # o índice segue com o status
        self.assertRegex(html, r'(?s)<a href="#secao-dlg-descritor"[^>]*>.*?1 erro')

    def test_previa_por_secoes_tem_indice_e_erros_oob(self):
        url = reverse("ui_templates_previa", args=[self.tpl.pk])
        r = self.ped.post(url, form_secoes([F2_SECOES[0], ("passo-descritor", "Descritor", "")]), HTTP_HX_REQUEST="true")
        self.assertContains(r, 'id="tpl-indice" hx-swap-oob="true"')
        self.assertContains(r, 'id="erros-passo-descritor" hx-swap-oob="true"')
        self.assertContains(r, "corpo vazio")
        self.assertNotContains(r, "## ")


class ExcluirLinkTest(UiBase):
    """E4 (D-207): "Excluir template…" na lista e no editor leva ao ui_excluir, voltando para a lista; o Impresso não vê."""

    def setUp(self):
        super().setUp()
        self.href = f'href="{reverse("ui_excluir", args=["template", self.tpl.pk])}?voltar={quote(self.lista + "?aba=F2")}"'

    def test_pedagogica_midias_e_admin_veem_o_link(self):
        for papel in ("Pedagógica", "Mídias Digitais", "Admin"):
            with self.subTest(papel):
                c = Client()
                c.force_login(usuario(f"u-{papel}", papel))
                self.assertContains(c.get(self.lista + "?aba=F2"), self.href, count=1)
                r = c.get(self.editar)
                self.assertContains(r, self.href, count=1)
                self.assertContains(r, "Excluir template…")
                Bloqueio.objects.all().delete()  # o próximo papel abre o editor sem a trava deste

    def test_impresso_nao_ve_o_link(self):
        imp = Client()
        imp.force_login(usuario("imp", "Impresso"))
        for url in (self.lista + "?aba=F2", self.editar):
            r = imp.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, "/ui/excluir/")
            self.assertNotContains(r, "Excluir template")

    def test_o_link_exclui_o_livre_e_volta_para_a_aba(self):
        livre = Template.objects.create(ano=self.tpl.ano, componente=self.tpl.componente, fasciculo="F2", nome="E2E livre")
        TemplateVersao.objects.create(template=livre, numero=1, texto=F2_NOVO, criada_por=usuario("autor"))
        lista = self.ped.get(self.lista + "?aba=F2").content.decode()
        href = re.search(rf'href="(/ui/excluir/template/{livre.pk}/[^"]+)"', lista)[1]
        r = self.ped.post(href, {"confirmacao": "E2E livre"})
        self.assertRedirects(r, self.lista + "?aba=F2", fetch_redirect_response=False)
        self.assertFalse(Template.objects.filter(pk=livre.pk).exists())
        self.assertFalse(TemplateVersao.objects.filter(template_id=livre.pk).exists())


class NovoTest(UiBase):
    """S7: "Novo template" pela tela B (add_template + add_templateversao), sem passar pelo admin."""

    def setUp(self):
        super().setUp()
        self.novo = reverse("ui_templates_novo", args=[2026])
        self.lp = self.tpl.componente
        self.imp = Client()
        self.imp.force_login(usuario("imp", "Impresso"))

    def dados(self, **troca):
        return {"componente": self.lp.pk, "fasciculo": "F1", "nome": "Novo F1", "texto": F1_NOVO, **troca}

    def test_pedagogica_cria_e_o_editor_mostra_a_versao_1(self):
        r = self.ped.get(self.novo + "?aba=F1")
        self.assertContains(r, 'value="F1" selected')
        self.assertContains(r, "## introducao")  # esqueleto válido do fascículo da aba
        r = self.ped.post(self.novo, self.dados())
        tpl = Template.objects.get(nome="Novo F1")
        self.assertRedirects(r, reverse("ui_templates_editar", args=[tpl.pk]), fetch_redirect_response=False)
        self.assertEqual((tpl.ano.ano, tpl.fasciculo, tpl.componente), (2026, "F1", self.lp))
        self.assertEqual(versao_atual(tpl.pk).numero, 1)
        self.assertEqual(versao_atual(tpl.pk).criada_por.username, "ped")
        self.assertContains(self.ped.get(r.url), "Versão atual: 1")

    def test_esqueleto_da_aba_f2_cria_sem_editar(self):
        esqueleto = self.ped.get(self.novo + "?aba=F2").context["form"]["texto"].value()
        self.assertTrue(esqueleto.startswith("## abertura"))
        r = self.ped.post(self.novo, self.dados(fasciculo="F2", nome="Do esqueleto", texto=esqueleto))
        self.assertRedirects(
            r, reverse("ui_templates_editar", args=[Template.objects.get(nome="Do esqueleto").pk]), fetch_redirect_response=False
        )

    def test_secao_fora_do_fasciculo_da_erro_de_campo_e_nao_grava(self):
        antes = (Template.objects.count(), TemplateVersao.objects.count())
        r = self.ped.post(self.novo, self.dados(texto=F1_NOVO + "\n## passo1\nT\n\nX.\n"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("passo1", str(r.context["form"].errors["texto"]))
        self.assertContains(r, 'id="texto-erro"')
        self.assertEqual((Template.objects.count(), TemplateVersao.objects.count()), antes)

    def test_nome_repetido_da_erro_e_nao_500(self):
        r = self.ped.post(self.novo, self.dados(fasciculo="F2", nome=self.tpl.nome, texto=F2_NOVO))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "já existe")
        self.assertEqual(Template.objects.filter(nome=self.tpl.nome, fasciculo="F2", componente=self.lp).count(), 1)

    def test_componente_de_outro_ano_e_o_ano_do_post_sao_ignorados(self):
        a27 = Ano.objects.create(ano=2027)
        outro = Componente.objects.create(ano=a27, codigo="XX", nome="Outro")
        r = self.ped.post(self.novo, self.dados(componente=outro.pk))
        self.assertIn("componente", r.context["form"].errors)
        self.assertEqual(Template.objects.filter(nome="Novo F1").count(), 0)
        self.ped.post(self.novo, self.dados(ano=a27.pk))
        self.assertEqual(Template.objects.get(nome="Novo F1").ano.ano, 2026)

    def test_impresso_nao_ve_o_botao_e_recebe_403(self):
        self.assertContains(self.ped.get(self.lista), f'href="{self.novo}?aba=F1"')
        self.assertNotContains(self.imp.get(self.lista), "Novo template")
        self.assertEqual(self.imp.get(self.novo).status_code, 403)
        self.assertEqual(self.imp.post(self.novo, self.dados()).status_code, 403)
        self.assertFalse(Template.objects.filter(nome="Novo F1").exists())

    def test_anonimo_vai_ao_login_e_ano_inexistente_404(self):
        self.assertEqual(Client().get(self.novo).status_code, 302)
        self.assertEqual(self.ped.get(reverse("ui_templates_novo", args=[1999])).status_code, 404)
