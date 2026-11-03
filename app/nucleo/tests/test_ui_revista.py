"""Revistas e revista fora do admin (/ui/revista/<ano>/, T20/T21): critérios de aceite de
docs/telas/fichas/revista.md, pelo client. A regra é a de nucleo/revista.py (testada também pelo admin)."""

from django.contrib.auth import get_user_model
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
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.servicos import bloqueio
from nucleo.servicos.resolver import carregar, hash_validado
from nucleo.tests.test_admin_projeto import ARQUIVADO, SVG_SEM_BOTAO, Base, mensagens
from nucleo.tests.test_painel import completar
from nucleo.tests.test_preview import SVG
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
        self.assertContains(r, f'{reverse("ui_impresso", args=[2026])}?revista={self.rev.pk}')
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
        """Auditoria 03/11: h1 "Parceiro · Componente ano" (não repete o projeto do link de voltar) e
        as seções com o rótulo do editor de template, não o id."""
        r = self.abrir()
        self.assertContains(r, f"<h1>{self.projeto_go.parceiro_ano.parceiro.nome} · {self.rev.componente.nome} 2026</h1>", html=True)
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
        self.assertEqual(self.client.post(self.url, {"acao": "arquivos", "arquivo_svg": SimpleUploadedFile("f2.svg", SVG)}).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=self.rev.pk).svg_f2)

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

    def test_svg_com_id_faltando_grava_e_mostra_os_ids(self):
        corpo = self.arquivo("arquivo_svg", "f2.svg", SVG_SEM_BOTAO).json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertEqual(set(corpo["trocar"]), {"arquivos", "situacao"})
        self.assertIn("Ids que faltam no SVG: btn-action-p2.", corpo["trocar"]["situacao"])  # a pendência, só lá
        self.assertIn(reverse("admin:nucleo_revista_gabarito_ids", args=[self.rev.pk]), corpo["trocar"]["arquivos"])
        self.assertEqual(Revista.objects.get(pk=self.rev.pk).svg_ids, ["fundo", "passo1", "passo2", "outro"])

    def test_capa_grava_e_mostra_a_miniatura(self):
        corpo = self.arquivo("arquivo_capa", "c.png", PNG).json()
        self.assertTrue(corpo["ok"], corpo)
        self.assertIn(reverse("preview_capa", args=[self.rev.pk]), corpo["trocar"]["arquivos"])
        self.assertTrue(Revista.objects.get(pk=self.rev.pk).capa)

    def test_arquivo_invalido_422_e_nao_grava(self):
        r = self.arquivo("arquivo_svg", "f2.svg", b"<html/>")
        self.assertEqual(r.status_code, 422)
        self.assertIn("O arquivo não é um SVG.", r.json()["erros"][0])
        r = self.arquivo("arquivo_capa", "c.png", b"GIF89a")
        self.assertEqual(r.json()["erros"], ["Capa precisa ser PNG, JPG ou WebP."])
        r = self.arquivo("svg_f2", "f2.svg", SVG)  # só os dois campos de arquivo
        self.assertEqual(r.status_code, 422)
        rev = Revista.objects.get(pk=self.rev.pk)
        self.assertFalse(rev.svg_f2)
        self.assertFalse(rev.capa)

    def test_upload_svg_grande_422_com_mensagem(self):
        r = self.arquivo("arquivo_svg", "f2.svg", b" " * (3 * 2**20 + 1))
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["erros"], ["SVG maior que 3 MB: reduza e envie de novo."])
        self.assertFalse(Revista.objects.get(pk=self.rev.pk).svg_f2)

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
        self.assertGreaterEqual(len(pendencias), 3)  # template do F2, SVG, capa
        for p in pendencias:
            self.assertContains(r, p.mensagem, count=1)
        self.assertContains(r, 'href="#templates"')
        self.assertContains(r, 'href="#arquivos"')
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
            self.assertRedirects(self.client.get(url), f"{reverse('admin:login')}?next={url}", fetch_redirect_response=False)

    def test_zip_com_pendencias_volta_com_a_mensagem(self):
        r = self.client.get(reverse("ui_revista_zip", args=[2026, self.rev.pk]) + "?voltar=lista", follow=True)
        self.assertRedirects(r, reverse("ui_projeto_lista", args=[2026]))
        self.assertTrue(any(m.startswith("Zip recusado. Pendências:") for m in mensagens(r)))

    def test_ano_sem_revistas(self):
        Ano.objects.create(ano=2027)
        r = self.client.get(reverse("ui_projeto_lista", args=[2027]))
        self.assertContains(r, "Nenhum projeto neste ano")
