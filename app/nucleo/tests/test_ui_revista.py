"""Revistas e revista fora do admin (/ui/revista/<ano>/, T20/T21): critérios de aceite de
docs/telas/fichas/revista.md, pelo client. A regra é a de nucleo/revista.py (testada também pelo admin)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import (
    Ano,
    Bloqueio,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaFasciculo,
    RevistaInfografico,
    RevistaInfograficoEtapa,
    RevistaInfograficoItem,
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.servicos import bloqueio
from nucleo.servicos.resolver import carregar, hash_validado
from nucleo.tests.test_admin_projeto import ARQUIVADO, Base, mensagens
from nucleo.tests.test_painel import completar
from nucleo.tests.test_resolver import F1, usuario

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63f8ff9f0100050001fe0b2d0bc20000000049454e44ae426082"
)

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
        lista = self.client.get(reverse("ui_projeto_lista", args=[2026]))  # U7a: a lista de revistas virou a de Projetos
        self.assertEqual(lista.status_code, 200)
        self.assertTemplateUsed(lista, "ui/base.html")
        self.assertContains(lista, f'href="{self.url}"')
        self.assertContains(lista, f'href="{reverse("preview", args=[self.rev.pk])}" target="_blank"')
        self.assertContains(lista, reverse("ui_revista_zip", args=[2026, self.rev.pk]))
        self.assertRedirects(self.client.get(reverse("ui_revista_inicio")), reverse("ui_projeto_lista", args=[2026]))

        r = self.abrir()
        for texto in ("acao=texto", 'x-data="campoAuto"', 'x-data="arquivoSoltar"', "Validar revista", 'id="bloqueio-sessao"'):
            self.assertContains(r, texto)
        self.assertNotContains(r, "Salvar seção")  # o texto da seção salva sozinho
        for texto in ("Salvar templates", "Salvar arquivos", "Trocar SVG do F2"):  # U8b: salva ao escolher
            self.assertNotContains(r, texto)
        self.assertContains(r, f'href="{reverse("preview", args=[self.rev.pk])}" target="_blank"')
        self.assertContains(r, f'class="link revista-impresso" href="{reverse("ui_impresso", args=[2026])}?revista={self.rev.pk}"')
        self.assertTrue(bloqueio.quem_bloqueia(self.projeto_go))  # abrir trava o projeto (D-140)
        self.assertEqual(self.client.get(reverse("ui_revista_editar", args=[2025, self.rev.pk])).status_code, 404)

    def test_sem_matriz_leva_a_ficha_do_projeto(self):
        """Item 21 (D-190); U8b: na lista da coluna Situação, sem faixa vermelha."""
        self.assertNotContains(self.abrir(), "Falta escolher a matriz")
        ParceiroAno.objects.filter(pk=self.projeto_go.parceiro_ano_id).update(matriz=None)
        r = self.abrir()
        self.assertContains(r, "Falta escolher a matriz do parceiro no ano.", count=1)
        self.assertContains(r, f'href="{reverse("ui_projeto", args=[self.projeto_go.pk])}?aba=matriz"')
        self.assertNotContains(r, "faixa-vermelha")

    def test_nome_se_edita_so_no_projeto(self):
        """U5: o "Editar nome" sai da revista; fica o link para o projeto. `acao=nome` é 400."""
        r = self.abrir()
        self.assertNotContains(r, "Editar nome")
        self.assertContains(r, "Editar o nome do projeto")
        self.assertContains(r, f'href="{reverse("ui_projeto", args=[self.projeto_go.pk])}#nome"')
        dados = {"acao": "nome", "nome": "Projeto Goiás", CAMPO_SESSAO: self.sessao(r)}
        self.assertEqual(self.client.post(self.url, dados).status_code, 400)
        self.assertNotEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto Goiás")

    def test_editar_no_projeto_sem_permissao(self):
        self.client.force_login(usuario("imp-nome", "Impresso"))
        self.assertNotContains(self.client.get(self.url), "Editar o nome do projeto")
        self.assertEqual(self.client.post(self.url, {"acao": "nome", "nome": "X"}).status_code, 403)

    def test_titulo_e_secoes_com_rotulo_humano(self):
        """Projeto primeiro: h1 "<projeto> · <componente>", o parceiro e o ano em pares rótulo/valor, a
        trilha Projetos de <ano> › <projeto> com links; as seções com o rótulo do editor de template, não o id."""
        Projeto.objects.filter(pk=self.projeto_go.pk).update(nome="SAEGO 2")
        r = self.abrir()
        self.assertContains(r, f"<h1>SAEGO 2 · {self.rev.componente.nome}</h1>", html=True)
        self.assertContains(r, f"<title>SAEGO 2 · {self.rev.componente.nome}", count=1)
        self.assertContains(r, "<div><dt>Parceiro</dt><dd>GO</dd></div>", html=True)
        self.assertContains(r, "<div><dt>Ano</dt><dd>2026</dd></div>", html=True)
        lista, projeto = reverse("ui_projeto_lista", args=[2026]), reverse("ui_projeto", args=[self.projeto_go.pk])
        self.assertContains(r, f'<nav class="mudo voltar pj-trilha" aria-label="Trilha"><span aria-hidden="true">‹ </span><a href="{lista}">Projetos de 2026</a> '
                               f'<span aria-hidden="true">›</span> <a href="{projeto}?aba=revistas">SAEGO 2</a></nav>', html=True)
        self.assertContains(r, '<span class="revista-secao-id">Introdução</span>', html=True)
        self.assertNotContains(r, '<span class="revista-secao-id">introducao</span>', html=True)

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
        for texto in ("acao=texto", 'x-data="campoAuto"', 'x-data="arquivoSoltar"', 'id="botao-validado"', 'id="bloqueio-sessao"', "Descartar cópia"):
            self.assertNotContains(r, texto)
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))
        for acao in ("secao", "templates", "arquivos", "validar"):
            self.assertEqual(self.client.post(self.url, {"acao": acao, INTRO: "x"}).status_code, 403)
        r = self.client.post(f"{self.url}?acao=texto", {"campo": INTRO, "valor": "x"}, HTTP_ACCEPT="application/json")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(RevistaSecao.objects.exists())
        self.client.force_login(get_user_model().objects.create(username="sem", is_staff=True))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse("ui_projeto_lista", args=[2026])).status_code, 403)

    def test_arquivada_mostra_a_foto_sem_bloqueio(self):
        Revista.objects.filter(pk=self.rev.pk).update(arquivada_em=ARQUIVADO)
        r = self.client.get(self.url)
        self.assertContains(r, "Só leitura: revista arquivada")
        self.assertContains(r, "Análise de GO")  # título já resolvido da foto
        self.assertNotContains(r, "Salvar")
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))
        self.assertEqual(self.client.post(self.url, {"acao": "arquivos", "arquivo_capa": SimpleUploadedFile("c.png", PNG)}).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).capa)

    # --- 3/4. textos pela regra do admin -------------------------------------------------------

    def test_salvar_secao_cria_copia_e_atualiza_validado(self):
        antes = hash_validado(carregar(self.rev.pk))
        r = self.secao(valor="Meu **texto**.")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Textos do F1 salvos: introducao.")
        self.assertContains(r, 'id="situacao"')  # a página volta inteira; o hx-select-oob troca a Situação
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
        self.assertContains(aberta, "manter__F1__introducao")
        self.assertContains(aberta, "Manter meu texto")
        self.assertContains(aberta, "Descartar cópia")

        self.secao(self.abrir(), manter__F1__introducao="on")
        self.assertEqual(RevistaSecao.objects.get().template_versao.numero, 2)
        self.assertNotContains(self.abrir(), "O template mudou nesta seção")

        # "Descartar cópia" é um botão: o texto da tela (mesmo mudado) não conta.
        self.secao(self.abrir(), valor="Outro.", descartar__F1__introducao="on")
        self.assertFalse(RevistaSecao.objects.exists())
        self.assertNotContains(self.abrir(), "Descartar cópia")  # sem cópia, sem botão

    # --- 4b. texto da seção salva sozinho (autosave, auditoria 03/11) ------------------------------

    def texto(self, valor, aberta=None, secao="introducao", **extra):
        aberta = aberta or self.abrir()
        b = next(b for b in aberta.context["blocos"] if b.rf.fasciculo == "F1")
        s = next(s for s in b.secoes if s.id == secao)
        dados = {CAMPO_SESSAO: self.sessao(aberta), "form_id": "secao-form", "campo": f"secao__F1__{secao}",
                 "valor": valor, "original": s.corpo, "versao__F1": b.versao.pk, **extra}  # fmt: skip
        return self.client.post(f"{self.url}?acao=texto&secao=F1:{secao}", dados, HTTP_ACCEPT="application/json")

    def test_texto_salva_sozinho_e_cria_copia(self):
        aberta = self.abrir()
        self.assertContains(aberta, "data-manter-ao-cancelar")
        r = self.texto("Meu **texto**.", aberta)
        corpo = r.json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(RevistaSecao.objects.get().texto, "Meu **texto**.")
        self.assertEqual(set(corpo["trocar"]), {"secoes", "situacao", "secao-estado-F1-introducao"})
        self.assertIn("cópia desta revista", corpo["trocar"]["secao-estado-F1-introducao"])
        self.assertIn("Descartar cópia", corpo["trocar"]["secao-estado-F1-introducao"])
        self.assertNotIn("Textos do F1 salvos", str(mensagens(self.abrir())))  # o status do autosave já disse
        self.assertTrue(bloqueio.quem_bloqueia(self.projeto_go))
        # Segunda mudança: `original` é o texto já salvo; atualiza a mesma cópia.
        aberta = self.abrir()
        self.assertContains(aberta, "Meu **texto**.")
        self.assertTrue(self.texto("Mais.", aberta).json()["ok"])
        self.assertEqual(RevistaSecao.objects.get().texto, "Mais.")

    def test_texto_invalido_422_e_campo_estranho(self):
        r = self.texto("Oi {{x}}.\n\n# Título")
        self.assertEqual(r.status_code, 422)
        self.assertIn("título (#)", " ".join(r.json()["erros"]))
        r = self.client.post(f"{self.url}?acao=texto", {CAMPO_SESSAO: self.sessao(self.abrir()), "campo": "secao__F1__nada", "valor": "x"},
                             HTTP_ACCEPT="application/json")  # fmt: skip
        self.assertEqual(r.status_code, 422)
        self.assertFalse(RevistaSecao.objects.exists())

    def test_texto_de_validada_pede_modal(self):
        completar(self.rev)
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(carregar(self.rev.pk)))
        aberta = self.abrir()
        corpo = self.texto("Mudou.", aberta).json()
        self.assertFalse(corpo["ok"])
        self.assertEqual(corpo["impacto"]["perdem"], [str(self.rev)])
        self.assertIn('data-form="secao-form"', corpo["impacto"]["html"])
        self.assertFalse(RevistaSecao.objects.exists())
        self.assertTrue(self.texto("Mudou.", aberta, confirmar_impacto="on").json()["ok"])
        self.assertEqual(RevistaSecao.objects.get().texto, "Mudou.")

    # --- 5. template por fascículo (U8b: autosave + modal) --------------------------------------

    def campo(self, acao, aberta=None, files=None, **dados):
        """POST do autosave (protocolo do U3) da página `aberta`, na rota da revista com `?acao=`."""
        aberta = aberta or self.abrir()
        dados = {CAMPO_SESSAO: self.sessao(aberta), "form_id": "revista-form", **dados}
        return self.client.post(f"{self.url}?acao={acao}", {**dados, **(files or {})}, HTTP_ACCEPT="application/json")

    def outro_template(self):
        outro = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Outro")
        TemplateVersao.objects.create(template=outro, numero=1, texto=F1.replace("Fim.", "Outro fim."))
        return outro

    def test_trocar_template_salva_sozinho_e_troca_textos_e_situacao(self):
        outro = self.outro_template()
        aberta = self.abrir()
        self.assertContains(aberta, f'<option value="{outro.pk}">Outro (F1)</option>')
        r = self.campo("templates", aberta, campo="F1-template", valor=outro.pk, original=self.rf.template_id)
        corpo = r.json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(set(corpo["trocar"]), {"textos", "situacao"})
        self.assertIn('id="situacao"', corpo["trocar"]["situacao"])
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, outro)
        self.assertTrue(bloqueio.quem_bloqueia(self.projeto_go))  # o autosave segue com o bloqueio da aba

    def test_trocar_template_com_copias_pede_modal(self):
        self.secao(valor="Meu texto.")
        outro = self.outro_template()
        aberta = self.abrir()
        self.assertNotContains(aberta, "descartar 1 cópia")  # a frase só aparece no modal
        corpo = self.campo("templates", aberta, campo="F1-template", valor=outro.pk).json()
        self.assertFalse(corpo["ok"])
        html = corpo["impacto"]["html"]
        self.assertIn("apaga 1 cópia(s) de seção", html)
        self.assertIn("<code>descartar 1 cópia</code>", html)
        self.assertIn('name="confirmacao"', html)
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, self.templates["LP", "F1"])

        r = self.campo("templates", aberta, campo="F1-template", valor=outro.pk, confirmar_impacto="on", confirmacao="errado")
        self.assertEqual(r.status_code, 422)
        self.assertIn("descartar 1 cópia", r.json()["erros"][0])
        self.assertTrue(RevistaSecao.objects.exists())

        r = self.campo("templates", aberta, campo="F1-template", valor=outro.pk, confirmar_impacto="on", confirmacao="descartar 1 cópia")
        self.assertTrue(r.json()["ok"])
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, outro)
        self.assertFalse(RevistaSecao.objects.exists())

    def test_trocar_template_de_validada_pede_modal(self):
        completar(self.rev)
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(carregar(self.rev.pk)))
        outro = self.outro_template()
        corpo = self.campo("templates", campo="F1-template", valor=outro.pk).json()
        self.assertEqual(corpo["impacto"]["perdem"], [str(self.rev)])
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, self.templates["LP", "F1"])

    def test_template_de_outro_lugar_ou_campo_estranho_422(self):
        for campo, valor in (("F1-template", self.templates["LP", "F2"].pk), ("F9-template", ""), ("acao", "x")):
            r = self.campo("templates", campo=campo, valor=valor)
            self.assertEqual(r.status_code, 422, campo)
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, self.templates["LP", "F1"])

    # --- 6. arquivos (U8b: arquivoSoltar, envio ao escolher) --------------------------------------

    def arquivo(self, campo, nome, dados, aberta=None, **extra):
        return self.campo("arquivos", aberta, files={"valor": SimpleUploadedFile(nome, dados)}, campo=campo, **extra)

    def test_capa_grava_e_mostra_a_miniatura(self):
        corpo = self.arquivo("arquivo_capa", "c.png", PNG).json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(set(corpo["trocar"]), {"arquivos", "situacao"})
        self.assertIn(reverse("preview_capa", args=[self.rev.pk]), corpo["trocar"]["arquivos"])
        self.assertTrue(Revista.objects.get(pk=self.rev.pk).capa)

    def test_arquivo_invalido_422_e_nao_grava(self):
        r = self.arquivo("arquivo_capa", "c.png", b"GIF89a")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["erros"], ["Capa precisa ser PNG, JPG ou WebP."])
        for campo in ("arquivo_svg", "svg_f2"):  # só a capa; o SVG enviado saiu (fase 4 do F2)
            r = self.arquivo(campo, "f2.svg", b"<svg/>")
            self.assertEqual(r.status_code, 422, campo)
            self.assertEqual(r.json()["erros"], ["Escolha o arquivo da capa e envie de novo."])
        self.assertFalse(Revista.objects.get(pk=self.rev.pk).capa)

    def test_capa_nova_em_validada_pede_modal(self):
        completar(self.rev)
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(carregar(self.rev.pk)))
        aberta = self.abrir()
        corpo = self.arquivo("arquivo_capa", "c.png", PNG, aberta).json()
        self.assertEqual(corpo["impacto"]["perdem"], [str(self.rev)])
        self.assertEqual(Revista.objects.get(pk=self.rev.pk).capa, "capas/x.png")
        corpo = self.arquivo("arquivo_capa", "c.png", PNG, aberta, confirmar_impacto="on").json()
        self.assertTrue(corpo["ok"])
        self.assertNotEqual(Revista.objects.get(pk=self.rev.pk).capa, "capas/x.png")

    # --- 6b. infográficos (fase 3 do F2: passo próprio, autosave por campo) ------------------------

    def outras(self):
        return RevistaInfografico.objects.get(revista=self.rev, tipo="outras")

    def inf(self, campo, valor="", aberta=None, files=None, **extra):
        return self.campo("infografico", aberta, files=files, campo=f"inf-{self.outras().pk}-{campo}", valor=valor, **extra)

    def test_infograficos_um_cartao_por_ativo_com_12_etapas_e_4_itens(self):
        inf = self.outras()
        RevistaInfografico.objects.create(
            revista=self.rev, componente=self.lp, ano=self.ano, tipo="alfa", arquivado_em=ARQUIVADO, habilidade="Velha."
        )
        RevistaInfograficoEtapa.objects.create(infografico=inf, ano=self.ano, etapa="5EF", marca="A", codigo="EF15LP18")
        r = self.abrir()
        self.assertContains(r, 'id="infograficos"', count=1)
        self.assertContains(r, 'class="card inf-card"', count=1)  # o alfa arquivado não aparece
        self.assertNotContains(r, "Velha.")
        self.assertContains(r, f'href="{reverse("preview_f2", args=[self.rev.pk, "outras"])}" target="_blank"')
        self.assertContains(r, f'name="inf-{inf.pk}-habilidade"')
        for passo in ("habilidades", "progressao", "tarefas"):
            self.assertContains(r, f'name="inf-{inf.pk}-passo-{passo}" checked')
        self.assertContains(r, f'name="inf-{inf.pk}-etapa-', count=36)  # 12 etapas × marca, código, texto
        self.assertContains(r, f'name="inf-{inf.pk}-etapa-1EF-marca" aria-label="Marca: 1º ano do Ensino Fundamental"')
        self.assertContains(r, '<option value="A" selected>Aprofundar</option>', count=1)
        self.assertContains(r, 'value="EF15LP18"')
        self.assertContains(r, f'name="inf-{inf.pk}-item-', count=20)  # 4 itens × etapa, descritor, imagem, alt, análise
        self.assertContains(r, 'href="#infograficos"')  # a pendência leva ao passo
        self.assertNotContains(r, "arquivo-svg")
        self.assertNotContains(r, "arquivo_svg")
        self.assertNotContains(r, "gabarito-ids")

    def template_f2(self):
        """Versão nova do template F2 da revista com as 9 seções do test_preview."""
        from nucleo.tests.test_preview import F2

        rf = RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F2")
        if rf.template is None:
            rf.template = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F2", nome="F2 teste")
            rf.save(update_fields=["template"])
        numero = TemplateVersao.objects.filter(template=rf.template).count() + 1
        TemplateVersao.objects.create(template=rf.template, numero=numero, texto=F2)
        return rf

    def test_infografico_ordem_numeros_e_linhas(self):
        """D-258: ❷ habilidades, a grade logo depois, ❸ progressão; caixas com rows="4" (o field-sizing fora do foco só se vê no navegador)."""
        html = self.abrir().content.decode()
        pk = self.outras().pk
        ordem = [f'id="inf-{pk}-texto_descritor"', "Texto do clique ❷ (habilidades)", f'id="inf-{pk}-texto_habilidades"',
                 "Referencial por etapa", "Texto do clique ❸ (progressão)", f'id="inf-{pk}-texto_progressao"',
                 f'id="inf-{pk}-item-1-analise"']  # fmt: skip
        self.assertEqual([html.index(t) for t in ordem], sorted(html.index(t) for t in ordem))
        for campo in ("texto_descritor", "texto_habilidades", "texto_progressao", "item-1-analise"):
            self.assertIn(f'id="inf-{pk}-{campo}" name="inf-{pk}-{campo}" rows="4"', html)

    def test_infografico_mostra_os_textos_do_template(self):
        rf = self.template_f2()
        r = self.abrir()
        self.assertContains(r, "Do template: Passo: descritor, Diálogo do descritor")
        self.assertContains(r, "Detalhe do descritor.")
        self.assertContains(r, 'href="?secao=F2%3Adlg-descritor#secao"')
        self.assertContains(r, "Do template: Passo: tarefas, Diálogo das tarefas, Fechamento das tarefas")
        self.assertContains(r, "Compare os itens.")
        # Com cópia na revista, o cartão mostra o texto da cópia.
        versao = TemplateVersao.objects.filter(template=rf.template).order_by("-numero").first()
        RevistaSecao.objects.create(
            revista_fasciculo=rf, template=rf.template, template_versao=versao, secao="dlg-descritor", texto="Meu descritor."
        )
        r = self.abrir()
        self.assertContains(r, "Meu descritor.")
        self.assertNotContains(r, "Detalhe do descritor.")
        # O badge aparece na lista de seções e no "Do template" do cartão.
        self.assertContains(r, '<span class="badge badge-secundario">cópia</span>', count=2)
        # Markdown cru com autoescape: HTML na seção sai como texto.
        RevistaSecao.objects.filter(secao="dlg-descritor").update(texto="<script>alert(1)</script>")
        r = self.abrir()
        self.assertContains(r, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(r, "<script>alert(1)</script>")

    def test_infografico_sem_template_f2_sem_textos_do_template(self):
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F2").update(template=None)
        self.assertNotContains(self.abrir(), "Do template:")

    def test_infografico_salva_e_troca_a_situacao(self):
        aberta = self.abrir()
        corpo = self.inf("habilidade", "Inferir informação.", aberta).json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(set(corpo["trocar"]), {"situacao"})  # o cartão não é trocado: o foco segue no campo seguinte
        self.assertNotIn("falta a habilidade destacada", corpo["trocar"]["situacao"])
        self.assertEqual(self.outras().habilidade, "Inferir informação.")
        self.assertTrue(self.inf("passo-progressao", "", aberta).json()["ok"])
        self.assertTrue(self.inf("etapa-9EF-marca", "C", aberta).json()["ok"])
        self.assertEqual(self.outras().passos_desligados, ["progressao"])
        self.assertEqual(RevistaInfograficoEtapa.objects.get(infografico=self.outras(), etapa="9EF").marca, "C")
        r = self.abrir()
        self.assertContains(r, f'name="inf-{self.outras().pk}-passo-progressao">')  # desligado: sem checked
        self.assertContains(r, 'value="Inferir informação."')

    def test_infografico_de_validada_pede_modal(self):
        completar(self.rev)
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(carregar(self.rev.pk)))
        aberta = self.abrir()
        corpo = self.inf("habilidade", "Outra.", aberta).json()
        self.assertEqual(corpo["impacto"]["perdem"], [str(self.rev)])
        self.assertEqual(self.outras().habilidade, "Inferir informação.")
        self.assertTrue(self.inf("habilidade", "Outra.", aberta, confirmar_impacto="on").json()["ok"])
        self.assertEqual(self.outras().habilidade, "Outra.")

    def validada(self):
        completar(self.rev)
        Revista.objects.filter(pk=self.rev.pk).update(hash_validado=hash_validado(carregar(self.rev.pk)))
        return self.abrir()

    def test_infografico_de_validada_passo_so_grava_confirmado(self):
        aberta = self.validada()
        self.assertIn("impacto", self.inf("passo-tarefas", "", aberta).json())
        self.assertNotIn("tarefas", self.outras().passos_desligados)
        self.assertTrue(self.inf("passo-tarefas", "", aberta, confirmar_impacto="on").json()["ok"])
        self.assertIn("tarefas", self.outras().passos_desligados)

    def test_infografico_de_validada_linha_nova_so_nasce_confirmada(self):
        aberta = self.validada()
        RevistaInfograficoEtapa.objects.filter(infografico=self.outras(), etapa="1EF").delete()
        self.assertIn("impacto", self.inf("etapa-1EF-codigo", "EF01LP01", aberta).json())
        self.assertFalse(RevistaInfograficoEtapa.objects.filter(infografico=self.outras(), etapa="1EF").exists())
        self.assertTrue(self.inf("etapa-1EF-codigo", "EF01LP01", aberta, confirmar_impacto="on").json()["ok"])
        self.assertEqual(RevistaInfograficoEtapa.objects.get(infografico=self.outras(), etapa="1EF").codigo, "EF01LP01")

    def test_infografico_de_validada_imagem_sem_confirmar_nao_grava(self):
        aberta = self.validada()
        antes = RevistaInfograficoItem.objects.get(infografico=self.outras(), posicao=2).imagem
        corpo = self.inf("item-2-imagem", aberta=aberta, files={"valor": SimpleUploadedFile("i.png", PNG)}).json()
        self.assertIn("impacto", corpo)
        self.assertEqual(RevistaInfograficoItem.objects.get(infografico=self.outras(), posicao=2).imagem, antes)
        self.assertFalse(default_storage.exists("infograficos") and default_storage.listdir("infograficos")[1])

    def test_imagem_do_item_grava_e_mostra_a_miniatura(self):
        corpo = self.inf("item-2-imagem", files={"valor": SimpleUploadedFile("i.png", PNG)}).json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(set(corpo["trocar"]), {"infograficos", "situacao"})
        item = RevistaInfograficoItem.objects.get(infografico=self.outras(), posicao=2)
        self.assertTrue(item.imagem.startswith("infograficos/"))
        nome_ = item.imagem.removeprefix("infograficos/")
        self.assertIn(reverse("preview_imagem_infografico", args=[self.rev.pk, nome_]), corpo["trocar"]["infograficos"])

    def test_infografico_invalido_422(self):
        self.assertEqual(self.campo("infografico", campo="inf-999999-habilidade", valor="x").status_code, 422)
        r = self.inf("habilidade", "x" * 501)
        self.assertEqual(r.status_code, 422)
        self.assertIn("500", r.json()["erros"][0])
        r = self.inf("item-1-imagem", files={"valor": SimpleUploadedFile("i.gif", b"GIF89a")})
        self.assertEqual(r.json()["erros"], ["A imagem precisa ser PNG, JPG ou WebP."])
        self.assertEqual(self.outras().habilidade, "")
        self.assertFalse(RevistaInfograficoItem.objects.exists())

    def test_infografico_sem_permissao_403_e_campos_desligados(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertContains(r, f'name="inf-{self.outras().pk}-habilidade" maxlength="500" value="" disabled>')
        self.assertEqual(self.client.post(f"{self.url}?acao=infografico", {"campo": "x"}, HTTP_ACCEPT="application/json").status_code, 403)
        parcial = usuario("parcial")
        perms = ("view_revista", "change_revista", "change_revistainfografico")
        parcial.user_permissions.set(Permission.objects.filter(content_type__app_label="nucleo", codename__in=perms))
        self.client.force_login(parcial)
        self.assertEqual(self.inf("etapa-5EF-marca", "A").status_code, 403)  # sem add/change da etapa
        self.assertEqual(self.inf("item-1-descritor", "D05").status_code, 403)
        self.assertTrue(self.inf("habilidade", "Pode.").json()["ok"])
        self.assertFalse(RevistaInfograficoEtapa.objects.exists() or RevistaInfograficoItem.objects.exists())

    def test_infografico_de_arquivada_403(self):
        Revista.objects.filter(pk=self.rev.pk).update(arquivada_em=ARQUIVADO)
        r = self.client.get(self.url)
        self.assertContains(r, f'name="inf-{self.outras().pk}-habilidade" maxlength="500" value="" disabled>')
        dados = {"campo": f"inf-{self.outras().pk}-habilidade", "valor": "x"}
        self.assertEqual(self.client.post(f"{self.url}?acao=infografico", dados, HTTP_ACCEPT="application/json").status_code, 403)
        self.assertEqual(self.outras().habilidade, "")

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
        self.assertContains(r, "Validada por ped em")
        self.assertNotContains(r, 'id="botao-validado"')

    def test_validar_desabilitado_com_motivo(self):
        r = self.abrir()
        self.assertContains(r, 'id="botao-validado" disabled aria-describedby="validar-motivo"')
        self.assertContains(r, 'id="validar-motivo">Resolva as pendências acima para validar.')
        completar(self.rev)
        r = self.abrir()
        self.assertContains(r, '<button class="btn" type="submit" id="botao-validado">')
        self.assertNotContains(r, "validar-motivo")

    def test_pendencias_aparecem_uma_vez(self):
        """U8b: uma lista só, na coluna Situação (antes: caixa rosa + faixas + selects)."""
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F2").update(template=None)
        r = self.abrir()
        pendencias = r.context["validacao"]["pendencias"]
        self.assertGreaterEqual(len(pendencias), 3)  # template do F2, infográfico, capa
        for p in pendencias:
            self.assertContains(r, p.mensagem, count=1)
        self.assertContains(r, "<span>Infográficos<span class=\"sr-only\">: pendente")  # o passo da Situação (antes "SVG do F2")
        self.assertContains(r, "Avaliação e Currículo – Outras Etapas: falta a habilidade destacada.")
        self.assertContains(r, 'href="#templates"')
        self.assertContains(r, 'href="#arquivos"')  # a capa
        self.assertContains(r, 'href="#infograficos"')
        for texto in ("faixa-vermelha", "caixa-erro", "Pendências que impedem", "não salvo não entra"):
            self.assertNotContains(r, texto)

    def test_textos_sem_template_mostra_estado_vazio(self):
        RevistaFasciculo.objects.filter(revista=self.rev, fasciculo="F2").update(template=None)
        r = self.abrir()
        self.assertContains(r, "Escolha os templates acima")
        self.assertNotContains(r, f'<a class="btn btn-outline" href="{self.url}">')  # o `url` da página não vaza para o vazio
        self.assertNotContains(r, "faixa-vermelha")
        self.assertNotContains(r, 'name="secao__F1__')

    # --- 9. bloqueio -------------------------------------------------------------------------

    def test_outro_com_o_projeto_aberto(self):
        self.travar(self.projeto_go)
        r = self.client.get(self.url)
        self.assertNotContains(r, "acao=texto")
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
            self.assertRedirects(self.client.get(url), f"{reverse('entrar')}?next={url}", fetch_redirect_response=False)

    def test_planilhas_pela_tela_b_sem_gabarito_de_ids(self):
        """S8: as planilhas, pela rota do impresso; o gabarito de ids saiu com o SVG enviado (fase 4 do F2)."""
        pagina = self.client.get(self.url)
        self.assertContains(pagina, reverse("impresso_planilhas", args=[self.rev.pk]))
        self.assertNotContains(pagina, "/admin/nucleo/revista/")
        plan = self.client.get(reverse("impresso_planilhas", args=[self.rev.pk]))
        self.assertEqual((plan.status_code, plan["Content-Type"]), (200, "application/zip"))
        self.assertTrue(plan["Content-Disposition"].startswith("attachment"))
        self.assertEqual(self.client.get(f"/ui/revista/2026/{self.rev.pk}/gabarito-ids/").status_code, 404)

    def test_impresso_ve_os_downloads(self):
        self.client.force_login(usuario("imp-dl", "Impresso"))
        pagina = self.client.get(self.url)
        self.assertContains(pagina, reverse("impresso_planilhas", args=[self.rev.pk]))

    def test_zip_com_pendencias_volta_com_a_mensagem(self):
        r = self.client.get(reverse("ui_revista_zip", args=[2026, self.rev.pk]) + "?voltar=lista", follow=True)
        self.assertRedirects(r, reverse("ui_projeto_lista", args=[2026]))
        self.assertTrue(any(m.startswith("Zip recusado. Pendências:") for m in mensagens(r)))

    def test_ano_sem_revistas(self):
        Ano.objects.create(ano=2027)
        r = self.client.get(reverse("ui_projeto_lista", args=[2027]))
        self.assertContains(r, "Nenhum projeto em 2027")
