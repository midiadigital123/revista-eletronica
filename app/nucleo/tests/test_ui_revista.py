"""Revistas e revista fora do admin (/ui/revista/<ano>/, T20/T21): critérios de aceite de
docs/telas/fichas/revista.md, pelo client. A regra é a de nucleo/revista.py (testada também pelo admin)."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import (
    Ano,
    Bloqueio,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.servicos import bloqueio
from nucleo.servicos.resolver import carregar, hash_validado
from nucleo.tests.test_admin_projeto import ARQUIVADO, SVG_SEM_BOTAO, Base, mensagens
from nucleo.tests.test_painel import completar
from nucleo.tests.test_preview import SVG
from nucleo.tests.test_resolver import F1

INTRO = "secao__F1__introducao"
HTMX = {"HTTP_HX_REQUEST": "true"}


class RevistaUiTest(Base):
    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        self.url = reverse("ui_revista_editar", args=[2026, self.rev.pk])
        self.rf = RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F1")

    def abrir(self, **get):
        Bloqueio.objects.all().delete()  # o pagehide da carga anterior
        r = self.client.get(self.url, get)
        self.assertEqual(r.status_code, 200)
        return r

    def sessao(self, aberta):
        return aberta.wsgi_request.bloqueio["sessao"]

    def secao(self, aberta=None, valor=None, secao="introducao", **extra):
        """POST de uma seção como o form da página manda (HTMX), a partir da página `aberta`."""
        aberta = aberta or self.abrir()
        c = aberta.context
        b = next(b for b in c["blocos"] if b.rf.fasciculo == "F1")
        s = next(s for s in b.secoes if s.id == secao)
        campo = f"secao__F1__{secao}"
        dados = {
            "acao": "secao", "chave": f"F1:{secao}", "versao__F1": b.versao.pk, CAMPO_SESSAO: self.sessao(aberta),
            campo: s.corpo if valor is None else valor, f"initial-{campo}": s.corpo, **extra,
        }  # fmt: skip
        return self.client.post(self.url, dados, **HTMX)

    def nova_versao(self, texto):
        atual = TemplateVersao.objects.filter(template=self.rf.template).order_by("-numero").first()
        return TemplateVersao.objects.create(template=self.rf.template, numero=atual.numero + 1, texto=texto)

    # --- 1. GET com permissão -------------------------------------------------------------

    def test_lista_e_pagina_com_permissao(self):
        lista = self.client.get(reverse("ui_revista", args=[2026]))
        self.assertEqual(lista.status_code, 200)
        self.assertTemplateUsed(lista, "ui/base.html")
        self.assertContains(lista, f'href="{self.url}"')
        self.assertContains(lista, f'href="{reverse("preview", args=[self.rev.pk])}" target="_blank"')
        self.assertContains(lista, reverse("ui_revista_zip", args=[2026, self.rev.pk]))
        self.assertRedirects(self.client.get(reverse("ui_revista_inicio")), reverse("ui_revista", args=[2026]))

        r = self.abrir()
        for texto in ("Salvar seção", "Salvar templates", "Salvar arquivos", "Não validado", 'id="bloqueio-sessao"'):
            self.assertContains(r, texto)
        self.assertContains(r, f'href="{reverse("preview", args=[self.rev.pk])}" target="_blank"')
        self.assertContains(r, f'{reverse("ui_impresso", args=[2026])}?revista={self.rev.pk}')
        self.assertTrue(bloqueio.quem_bloqueia(self.projeto_go))  # abrir trava o projeto (D-140)
        self.assertEqual(self.client.get(reverse("ui_revista_editar", args=[2025, self.rev.pk])).status_code, 404)

    def test_htmx_troca_so_a_secao(self):
        r = self.client.get(self.url, {"secao": "F1:fechamento"}, **HTMX)
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertContains(r, 'name="secao__F1__fechamento"')
        self.assertContains(r, 'id="secoes" aria-label="Seções" hx-swap-oob="true"')
        self.assertContains(r, 'aria-current="true"', count=1)

    # --- 2. só leitura -----------------------------------------------------------------------

    def test_impresso_so_leitura_e_post_403(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Só leitura: seu perfil vê a revista")
        self.assertContains(r, " readonly>")
        for texto in ("Salvar seção", "Salvar templates", "Salvar arquivos", 'id="botao-validado"', 'id="bloqueio-sessao"'):
            self.assertNotContains(r, texto)
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))
        for acao in ("secao", "templates", "arquivos", "validar"):
            self.assertEqual(self.client.post(self.url, {"acao": acao, INTRO: "x"}).status_code, 403)
        self.assertFalse(RevistaSecao.objects.exists())
        self.client.force_login(get_user_model().objects.create(username="sem", is_staff=True))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse("ui_revista", args=[2026])).status_code, 403)

    def test_arquivada_mostra_a_foto_sem_bloqueio(self):
        Revista.objects.filter(pk=self.rev.pk).update(arquivada_em=ARQUIVADO)
        r = self.client.get(self.url)
        self.assertContains(r, "Só leitura: revista arquivada")
        self.assertContains(r, "Análise de GO")  # título já resolvido da foto
        self.assertNotContains(r, "Salvar")
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))
        self.assertEqual(self.client.post(self.url, {"acao": "arquivos", "arquivo_svg": SimpleUploadedFile("f2.svg", SVG)}).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).svg_f2)

    # --- 3/4. textos pela regra do admin -------------------------------------------------------

    def test_salvar_secao_cria_copia_e_atualiza_validado(self):
        antes = hash_validado(carregar(self.rev.pk))
        r = self.secao(valor="Meu **texto**.")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Textos do F1 salvos: introducao.")
        self.assertContains(r, 'id="validado"')  # a página volta inteira; o hx-select-oob troca o card
        copia = RevistaSecao.objects.get()
        self.assertEqual((copia.revista_fasciculo, copia.secao, copia.texto), (self.rf, "introducao", "Meu **texto**."))
        self.assertNotEqual(hash_validado(carregar(self.rev.pk)), antes)
        self.assertContains(r, "cópia desta revista")
        self.assertTrue(bloqueio.quem_bloqueia(self.projeto_go))  # 200: a aba segue com o bloqueio

    def test_igual_ao_template_nao_cria_e_invalido_mostra_erro(self):
        r = self.secao()
        self.assertContains(r, "Nada a salvar: o texto está igual ao que abriu.")
        self.secao(valor="Texto **{{nome_projeto}}**.\r\n")
        self.assertFalse(RevistaSecao.objects.exists())
        r = self.secao(valor="Oi {{x}}.\n\n# Título")
        self.assertContains(r, "Nada foi gravado: corrija os erros marcados.")
        self.assertContains(r, 'aria-invalid="true"')
        self.assertContains(r, "{{x}}")
        self.assertContains(r, "Oi {{x}}.")  # o texto digitado volta no campo
        self.assertFalse(RevistaSecao.objects.exists())

    def test_desatualizada_diff_manter_descartar(self):
        self.secao(valor="Meu texto.")
        self.nova_versao(F1.replace("Texto **{{nome_projeto}}**.", "Texto novo."))
        aberta = self.abrir()
        self.assertContains(aberta, "O template mudou nesta seção")
        self.assertContains(aberta, "Template novo")
        self.assertContains(aberta, 'name="manter__F1__introducao"')

        r = self.secao(aberta, valor="Outro.", descartar__F1__introducao="on")
        self.assertContains(r, "escolha um dos dois")
        self.assertEqual(RevistaSecao.objects.get().texto, "Meu texto.")

        self.secao(self.abrir(), manter__F1__introducao="on")
        self.assertEqual(RevistaSecao.objects.get().template_versao.numero, 2)
        self.assertNotContains(self.abrir(), "O template mudou nesta seção")

        self.secao(self.abrir(), descartar__F1__introducao="on")
        self.assertFalse(RevistaSecao.objects.exists())

    # --- 5. template por fascículo --------------------------------------------------------------

    def postar_templates(self, aberta, **troca):
        dados = {"acao": "templates", CAMPO_SESSAO: self.sessao(aberta)}
        for rf in RevistaFasciculo.objects.filter(revista=self.rev):
            dados[f"{rf.fasciculo}-template"] = rf.template_id
        return self.client.post(self.url, {**dados, **troca}, **HTMX)

    def test_trocar_template_com_copias_pede_a_frase(self):
        self.secao(valor="Meu texto.")
        outro = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Outro")
        TemplateVersao.objects.create(template=outro, numero=1, texto=F1.replace("Fim.", "Outro fim."))
        aberta = self.abrir()
        self.assertContains(aberta, "<code>descartar 1 cópia</code>")
        self.assertContains(aberta, f'<option value="{outro.pk}">Outro (F1)</option>')

        r = self.postar_templates(aberta, **{"F1-template": outro.pk})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "digite “descartar 1 cópia”")
        self.assertContains(r, "Nada foi gravado")
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, self.templates["LP", "F1"])

        r = self.postar_templates(aberta, **{"F1-template": outro.pk, "F1-confirmacao": "descartar 1 cópia"})
        self.assertEqual(r["HX-Redirect"], self.url)
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, outro)
        self.assertFalse(RevistaSecao.objects.exists())
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))  # HX-Redirect libera
        r = self.client.get(self.url)
        self.assertIn("Template do F1 trocado: 1 cópia de seção descartada.", mensagens(r))
        self.assertIn("Templates salvos.", mensagens(r))

    # --- 6. arquivos ------------------------------------------------------------------------------

    def arquivos(self, aberta, **arquivos):
        return self.client.post(self.url, {"acao": "arquivos", CAMPO_SESSAO: self.sessao(aberta), **arquivos}, follow=True)

    def test_svg_com_id_faltando_grava_e_avisa(self):
        r = self.arquivos(self.abrir(), arquivo_svg=SimpleUploadedFile("f2.svg", SVG_SEM_BOTAO))
        self.assertRedirects(r, self.url)
        aviso = next(m for m in mensagens(r) if "Ids que faltam" in m)
        self.assertIn("<strong>btn-action-p2</strong>", aviso)
        self.assertIn("Arquivos salvos.", mensagens(r))
        self.assertEqual(Revista.objects.get(pk=self.rev.pk).svg_ids, ["fundo", "passo1", "passo2", "outro"])
        self.assertContains(r, "Ids que faltam no SVG: <strong>btn-action-p2</strong>")
        self.assertContains(r, reverse("admin:nucleo_revista_gabarito_ids", args=[self.rev.pk]))

    def test_arquivo_invalido_mostra_erro_e_nao_grava(self):
        r = self.arquivos(
            self.abrir(), arquivo_svg=SimpleUploadedFile("f2.svg", b"<html/>"), arquivo_capa=SimpleUploadedFile("c.png", b"GIF89a")
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "O arquivo não é um SVG.")
        self.assertContains(r, "Capa precisa ser PNG, JPG ou WebP.")
        self.assertContains(r, "Nada foi gravado")
        rev = Revista.objects.get(pk=self.rev.pk)
        self.assertIsNone(rev.svg_f2)
        self.assertIsNone(rev.capa)

    # --- 7. Validado ---------------------------------------------------------------------------

    def test_validado_com_o_hash_da_pagina(self):
        completar(self.rev)
        aberta = self.abrir()
        hash_ = aberta.context["validacao"]["hash"]
        self.assertContains(aberta, 'id="botao-validado"')
        dados = {"acao": "validar", "hash_visto": "x" * 64, CAMPO_SESSAO: self.sessao(aberta)}
        r = self.client.post(self.url, dados, follow=True)
        self.assertIn("Não validada: a revista mudou depois que a página abriu; confira de novo.", mensagens(r))
        aberta = self.abrir()
        dados.update({"hash_visto": aberta.context["validacao"]["hash"], CAMPO_SESSAO: self.sessao(aberta)})
        self.assertEqual(dados["hash_visto"], hash_)
        r = self.client.post(self.url, dados, **HTMX)
        self.assertEqual(r["HX-Redirect"], self.url)
        self.assertEqual(Revista.objects.get(pk=self.rev.pk).hash_validado, hash_)
        r = self.client.get(self.url)
        self.assertIn("Revista validada.", mensagens(r))
        self.assertContains(r, "Por ped em")
        self.assertNotContains(r, 'id="botao-validado"')

    def test_validado_desabilitado_com_pendencias(self):
        r = self.abrir()
        self.assertContains(r, 'id="botao-validado" disabled')
        self.assertContains(r, "Pendências que impedem")

    # --- 9. bloqueio -------------------------------------------------------------------------

    def test_outro_com_o_projeto_aberto(self):
        self.travar(self.projeto_go)
        r = self.client.get(self.url)
        self.assertNotContains(r, "Salvar seção")
        self.assertNotContains(r, 'id="bloqueio-sessao"')
        self.assertContains(r, " readonly>")
        dados = {"acao": "secao", "chave": "F1:introducao", CAMPO_SESSAO: "chute", INTRO: "Meu.", f"initial-{INTRO}": "x"}
        r = self.client.post(self.url, dados, follow=True)
        self.assertTrue(any(m.startswith("Não salvo: você perdeu o bloqueio") for m in mensagens(r)))
        self.assertFalse(RevistaSecao.objects.exists())

    # --- 10. anônimo e zip -----------------------------------------------------------------------

    def test_anonimo_vai_para_o_login(self):
        self.client.logout()
        for url in (self.url, reverse("ui_revista", args=[2026])):
            self.assertRedirects(self.client.get(url), f"{reverse('admin:login')}?next={url}", fetch_redirect_response=False)

    def test_zip_com_pendencias_volta_com_a_mensagem(self):
        r = self.client.get(reverse("ui_revista_zip", args=[2026, self.rev.pk]) + "?voltar=lista", follow=True)
        self.assertRedirects(r, reverse("ui_revista", args=[2026]))
        self.assertTrue(any(m.startswith("Zip recusado. Pendências:") for m in mensagens(r)))

    def test_ano_sem_revistas(self):
        Ano.objects.create(ano=2027)
        r = self.client.get(reverse("ui_revista", args=[2027]))
        self.assertContains(r, "Nenhuma revista neste ano")
