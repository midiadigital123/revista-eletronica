"""Hub Projetos (U7a): abas Lista · Cortes · Variáveis, ações em massa e as rotas antigas.

A Lista substitui a lista de Revistas e os Lotes; Cortes e Variáveis viram abas com URL própria
(`/ui/projeto/ano/<ano>/cortes/`, `…/variaveis/`), que herdam os nomes de rota `cortes` e `ui_variaveis`.
"""

from django.urls import reverse

from nucleo.models import Ano, Matriz, Parceiro, ParceiroAno, Projeto, RevistaFasciculo
from nucleo.tests import test_admin_projeto
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_admin_projeto import ARQUIVADO, Base, mensagens
from nucleo.tests.test_resolver import usuario

LISTA = reverse("ui_projeto_lista", args=[2026])
CORTES = reverse("cortes", args=[2026])
VARIAVEIS = reverse("ui_variaveis", args=[2026])


def massa(acao):
    return reverse("ui_projeto_massa", args=[2026, acao])


class HubListaTest(Base):
    def test_lista_um_grupo_por_parceiro_com_as_revistas(self):
        r = self.client.get(LISTA)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'href="{LISTA}" aria-current="page">Lista')
        self.assertContains(r, f'href="{CORTES}">Cortes')
        self.assertContains(r, f'href="{VARIAVEIS}">Variáveis')
        self.assertContains(r, reverse("ui_projeto", args=[self.projeto_go.pk]))
        lp = self.go["LP"]
        self.assertContains(r, reverse("ui_revista_editar", args=[2026, lp.pk]))
        self.assertContains(r, reverse("preview", args=[lp.pk]))
        self.assertContains(r, reverse("ui_revista_zip", args=[2026, lp.pk]))
        self.assertContains(r, 'name="alvos"', count=2)  # GO e PE

    def test_cada_revista_e_uma_linha_sob_o_cabecalho_do_parceiro(self):
        """Padrão do painel: um <tbody> por projeto, cabeçalho de grupo (parceiro) e uma linha por revista."""
        html = self.client.get(LISTA).content.decode()
        grupo = next(t for t in html.split("<tbody")[1:] if 'aria-label="Marcar GO"' in t)
        self.assertEqual(grupo.count('class="painel-grupo"'), 1)
        self.assertLess(grupo.index('class="painel-grupo"'), grupo.index("data-revista="))
        for codigo, r in self.go.items():
            with self.subTest(codigo):
                self.assertEqual(grupo.count(f'<tr data-revista="{r.pk}">'), 1)
        self.assertEqual(grupo.count("<tr data-revista="), len(self.go))

    def test_grupo_mostra_o_projeto_como_link_e_o_parceiro_em_cinza(self):
        """Projeto primeiro: o nome do projeto é o link do grupo; o parceiro vem ao lado, como contexto.
        Sai o link genérico "Projeto". Parceiro sem projeto continua só com o nome do parceiro."""
        Projeto.objects.filter(pk=self.projeto_go.pk).update(nome="SAEGO 2")
        Parceiro.objects.create(nome="SEM").parceiroano_set.create(ano=self.ano)
        html = self.client.get(LISTA).content.decode()
        grupo = next(t for t in html.split("<tbody")[1:] if 'aria-label="Marcar GO"' in t)
        url = reverse("ui_projeto", args=[self.projeto_go.pk])
        self.assertIn(f'<a class="painel-grupo-nome" href="{url}" title="Abrir o projeto">SAEGO 2</a>', grupo)
        self.assertIn('<span class="painel-grupo-parceiro" title="Parceiro"><span class="sr-only">Parceiro </span>GO</span>', grupo)
        self.assertNotIn("painel-grupo-projeto", html)
        self.assertIn("<span class=\"sr-only\">SAEGO 2 · LP · </span>", grupo)
        sem = next(t for t in html.split("<tbody")[1:] if 'aria-label="Marcar SEM"' in t)
        self.assertIn('<span class="painel-grupo-nome">SEM</span>', sem)
        self.assertIn("sem projeto", sem)

    def test_pendencias_em_balao_e_acoes_com_nome(self):
        """Pendências num balão com o número (texto completo no aria-label, plural certo); Preview e Zip
        são botões-ícone com nome acessível."""
        import re

        from nucleo.urls import painel

        html = self.client.get(LISTA).content.decode()
        self.assertNotIn("pendência(s)", html)
        for r in self.go.values():
            with self.subTest(r.componente.codigo):
                cel = painel.linha(r)["faltas"]
                n = sum(not c["ok"] for k, c in cel.items() if k not in ("validado", "impresso"))
                linha = re.search(rf'<tr data-revista="{r.pk}">.*?</tr>', html, re.S).group(0)
                if n:
                    rotulo = f"{n} pendência" + ("s" if n > 1 else "")
                    self.assertIn(f'<span class="contagem" role="img" aria-label="{rotulo}" title="{rotulo}: ', linha)
                    self.assertIn(f">{n}</span>", linha)
                else:
                    self.assertIn('aria-label="Sem pendências"', linha)
                self.assertIn(f'aria-label="Abrir preview de {r} (nova aba)"', linha)
                self.assertIn(f'aria-label="Baixar zip de {r}"', linha)
                self.assertIn(f'<span class="tag tag-lilas" title="{r.componente.nome}">{r.componente.codigo}</span>', linha)
                # Validado e Impresso são etapas: aparecem na Situação, não no balão.
                self.assertIn('<span class="tag ">Em preparo</span>' if n else '<span class="tag tag-ambar">Pronta para validar</span>', linha)
                self.assertIn('data-dica="Abrir preview"', linha)

    def test_acoes_em_massa_desabilitadas_sem_marcado(self):
        """Sem parceiro marcado, "Atribuir matriz…" e "Atribuir template…" ficam desabilitados com o motivo;
        o servidor continua recusando o envio vazio."""
        r = self.client.get(LISTA)
        for acao in ("matriz", "template"):
            with self.subTest(acao):
                self.assertContains(r, f'data-abrir="dlg-{acao}" data-precisa-marca disabled title="Marque ao menos um parceiro">')
        r = self.client.post(massa("matriz"), {"matriz": self.matriz.pk}, follow=True)
        self.assertIn("Marque ao menos um parceiro", r.content.decode())

    def test_abas_cortes_e_variaveis(self):
        r = self.client.get(CORTES)
        self.assertTemplateUsed(r, "ui/cortes.html")
        self.assertContains(r, 'aria-current="page">Cortes')
        self.assertContains(r, "<h1>Projetos</h1>", html=True)
        r = self.client.get(VARIAVEIS)
        self.assertTemplateUsed(r, "ui/variaveis/pagina.html")
        self.assertContains(r, 'aria-current="page">Variáveis')

    def test_arquivado_e_parceiro_sem_projeto(self):
        Projeto.objects.filter(pk=self.projeto_pe.pk).update(arquivado_em=ARQUIVADO)
        sem = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="SP"), ano=self.ano)
        r = self.client.get(LISTA)
        self.assertContains(r, "Arquivado em")
        self.assertContains(r, "Sem projeto ativo", count=2)  # PE (arquivado) e SP
        self.assertContains(r, f'value="{sem.pk}"')  # a matriz do parceiro sem projeto continua atribuível

    def test_em_edicao_sera_pulado(self):
        self.travar(self.projeto_go)
        self.assertContains(self.client.get(LISTA), "Em edição por outro: será pulado")

    def test_impresso_ve_sem_barra_e_post_403(self):
        self.client.force_login(self.imp)
        r = self.client.get(LISTA)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="alvos"')
        self.assertNotContains(r, "Atribuir matriz…")
        self.assertNotContains(r, "Atribuir template…")
        pa = ParceiroAno.objects.get(parceiro__nome="PE")
        self.assertEqual(self.client.post(massa("matriz"), {"alvos": [pa.pk], "matriz": self.matriz.pk}).status_code, 403)
        self.assertEqual(self.client.post(massa("template"), {"alvos": [pa.pk], "componente": self.lp.pk}).status_code, 403)
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(LISTA).status_code, 403)


class RotasAntigasTest(Base):
    def test_get_redireciona_302_para_a_aba(self):
        for antiga, destino in [
            ("/cortes/2026/", CORTES),
            ("/cortes/", CORTES),
            ("/ui/variaveis/2026/", VARIAVEIS),
            ("/ui/variaveis/", VARIAVEIS),
            (reverse("ui_revista", args=[2026]), LISTA),
            (reverse("ui_revista_inicio"), LISTA),
            (reverse("ui_lotes_matriz", args=[2026]), LISTA),
            (reverse("ui_lotes_template", args=[2026]) + "?componente=1", LISTA),
            (reverse("ui_lotes_inicio"), LISTA),
        ]:
            with self.subTest(antiga):
                r = self.client.get(antiga)
                self.assertEqual(r.status_code, 302)
                self.assertEqual(r.url, destino)

    def test_abas_tem_url_nova(self):
        self.assertEqual(CORTES, "/ui/projeto/ano/2026/cortes/")
        self.assertEqual(VARIAVEIS, "/ui/projeto/ano/2026/variaveis/")

    def test_post_antigo_continua_gravando(self):
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        self.client.post(reverse("ui_lotes_matriz", args=[2026]), {"alvos": [pe.pk], "matriz": nova.pk})
        self.assertEqual(ParceiroAno.objects.get(pk=pe.pk).matriz, nova)


class NenhumaAcaoPerdidaTest(Base):
    """Inventário (regra dura do U7): cada ação das telas antigas continua na tela nova, com o mesmo nome."""

    def setUp(self):
        super().setUp()
        self.client.force_login(usuario("tudo", is_superuser=True))
        Ano.objects.create(ano=2025)

    def test_nenhuma_acao_perdida(self):
        go, lp = self.projeto_go.parceiro_ano.parceiro, self.go["LP"]
        inventario = {
            "/cortes/<ano>/": (CORTES, [
                "Adicionar parceiro", "Incluir parceiro", "Baixar planilha de grupos", f"Renomear {go.nome}",
                reverse("cortes_celula", args=[2026]), reverse("cortes_novo_parceiro", args=[2026]),
            ]),
            "/ui/variaveis/<ano>/": (VARIAVEIS, [
                "Copiar de 2025", "O que é cada variável", reverse("ui_projeto_campo", args=[self.projeto_go.pk]),
            ]),
            "/ui/revista/<ano>/": (LISTA, [
                reverse("ui_revista_editar", args=[2026, lp.pk]), reverse("preview", args=[lp.pk]),
                reverse("ui_revista_zip", args=[2026, lp.pk]) + "?voltar=lista", "Abrir preview de", "Baixar zip de",
            ]),
            "/ui/lotes/<ano>/matriz/": (LISTA, ["Atribuir matriz…", 'name="matriz"', 'name="alvos"', massa("matriz")]),
            "/ui/lotes/<ano>/template/": (LISTA, [
                "Atribuir template…", 'name="componente"', 'name="template_f1"', 'name="template_f2"', massa("template"),
            ]),
        }
        for antiga, (nova, acoes) in inventario.items():
            r = self.client.get(nova)
            for acao in acoes:
                with self.subTest(antiga=antiga, acao=acao):
                    self.assertContains(r, acao)


class MassaMatrizTest(Base):
    def setUp(self):
        super().setUp()
        self.nova = Matriz.objects.create(ano=self.ano, nome="Nova")

    def test_sem_impacto_grava_pula_travado_e_volta_a_lista(self):
        self.travar(self.projeto_go)
        pas = ParceiroAno.objects.filter(ano=self.ano)
        r = self.client.post(massa("matriz"), {"alvos": [pa.pk for pa in pas], "matriz": self.nova.pk}, follow=True)
        self.assertRedirects(r, LISTA)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="PE").matriz, self.nova)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="GO").matriz, self.matriz)
        self.assertIn("Matriz Nova escolhida para 1 parceiro(s).", mensagens(r))
        self.assertIn("Pulados: GO (projeto em edição por outro).", mensagens(r))

    def test_erro_mantem_a_selecao(self):
        pe = ParceiroAno.objects.get(parceiro__nome="PE")
        r = self.client.post(massa("matriz"), {"alvos": [pe.pk], "matriz": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nada foi gravado")
        self.assertContains(r, "Escolha a matriz.")
        self.assertContains(r, f'value="{pe.pk}" checked')

    def test_com_impacto_abre_modal_e_so_grava_confirmado(self):
        rev = self.go["LP"]
        validar(rev)
        go = ParceiroAno.objects.get(parceiro__nome="GO")
        dados = {"alvos": [go.pk], "matriz": self.nova.pk}
        r = self.client.post(massa("matriz"), dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-abrir-ao-carregar data-form="massa"')
        self.assertContains(r, "Atribuir matriz tira o “Validado” de 1 revista(s)")
        self.assertContains(r, f'action="{massa("matriz")}"')  # o Confirmar reenvia para a mesma ação
        self.assertContains(r, f'value="{go.pk}" checked')
        self.assertEqual(ParceiroAno.objects.get(pk=go.pk).matriz, self.matriz)
        self.assertTrue(esta_validada(rev))
        r = self.client.post(massa("matriz"), {**dados, "confirmar_impacto": "on"}, follow=True)
        self.assertEqual(ParceiroAno.objects.get(pk=go.pk).matriz, self.nova)
        self.assertTrue(any("1 revista(s) perderam o “Validado”" in m for m in mensagens(r)))
        self.assertFalse(esta_validada(rev))

    def test_acao_desconhecida_404(self):
        self.assertEqual(self.client.post(massa("nada"), {}).status_code, 404)


class MassaTemplateTest(Base):
    novo_template = test_admin_projeto.LoteTemplateTest.novo_template

    def test_sem_impacto_grava_nas_revistas_do_componente(self):
        f2 = self.novo_template(self.lp, "F2", nome="Outro F2")
        self.travar(self.projeto_pe)
        pas = ParceiroAno.objects.filter(ano=self.ano)
        dados = {"alvos": [pa.pk for pa in pas], "componente": self.lp.pk, "template_f2": f2.pk}
        r = self.client.post(massa("template"), dados, follow=True)
        self.assertRedirects(r, LISTA)
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F2").template, f2)
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.go["MT"], fasciculo="F2").template, self.templates["MT", "F2"])
        self.assertIn("Template escolhido em 1 revista(s).", mensagens(r))
        self.assertTrue(any("Projeto PE · LP (projeto em edição por outro)" in m for m in mensagens(r)))

    def test_sem_componente_ou_template_de_outro_componente(self):
        go = ParceiroAno.objects.get(parceiro__nome="GO")
        r = self.client.post(massa("template"), {"alvos": [go.pk], "template_f1": self.templates["LP", "F1"].pk})
        self.assertContains(r, "Escolha o componente.")
        r = self.client.post(massa("template"), {"alvos": [go.pk], "componente": self.lp.pk, "template_f1": self.templates["MT", "F1"].pk})
        self.assertContains(r, "Escolha uma opção da lista")

    def test_com_impacto_abre_modal(self):
        rev = self.go["LP"]
        validar(rev)
        f2 = self.novo_template(self.lp, "F2", nome="Outro F2")
        go = ParceiroAno.objects.get(parceiro__nome="GO")
        r = self.client.post(massa("template"), {"alvos": [go.pk], "componente": self.lp.pk, "template_f2": f2.pk})
        self.assertContains(r, "Atribuir template tira o “Validado” de 1 revista(s)")
        self.assertEqual(RevistaFasciculo.objects.get(revista=rev, fasciculo="F2").template, self.templates["LP", "F2"])
        self.assertTrue(esta_validada(rev))
