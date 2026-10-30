"""Matrizes e descritores B (/ui/matriz/, T09-T11): critérios de aceite de docs/telas/fichas/matriz.md."""

import tempfile
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos import bloqueio
from nucleo.tests.test_admin_cadastro import Base as BaseCadastro
from nucleo.tests.test_importacao import cadastrar, planilha
from nucleo.tests.test_item import PNG
from nucleo.tests.test_item import Base as BaseMundo
from nucleo.tests.test_resolver import usuario

HX = {"HTTP_HX_REQUEST": "true"}


class MatrizUiTest(BaseCadastro):
    """T09: lista do ano, matriz, Duplicar, Renomear, Reimportar, Diferenças."""

    def test_anonimo_vai_ao_login_e_sem_permissao_403(self):
        urls = [reverse("ui_matriz", args=[2026]), reverse("ui_matriz_detalhe", args=[self.matriz.pk]),
                reverse("ui_matriz_mec", args=[self.mec.pk])]  # fmt: skip
        for url in urls:
            r = Client().get(url)
            self.assertRedirects(r, f"/admin/login/?next={url}", fetch_redirect_response=False)
        self.client.force_login(usuario("nada"))
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_lista_do_ano_e_matriz(self):
        self.assertRedirects(self.client.get(reverse("ui_matriz_inicio")), reverse("ui_matriz", args=[2026]))
        resp = self.client.get(reverse("ui_matriz", args=[2026]))
        self.assertTemplateUsed(resp, "ui/base.html")
        self.assertContains(resp, reverse("ui_matriz_detalhe", args=[self.matriz.pk]))
        resp = self.client.get(reverse("ui_matriz_detalhe", args=[self.matriz.pk]))
        for texto in ("Duplicar", "Renomear", "Reimportar", reverse("ui_matriz_mec", args=[self.mec.pk])):
            self.assertContains(resp, texto)
        cadastrar(2027)
        self.assertContains(self.client.get(reverse("ui_matriz", args=[2027])), "Nenhuma matriz em 2027")

    def test_duplicar_leva_a_copia_e_nome_repetido_mostra_erro(self):
        a27 = cadastrar(2027)
        url = reverse("ui_matriz_duplicar", args=[self.matriz.pk])
        resp = self.client.post(url, {"ano": a27.pk, "nome": "Exceção GO"}, **HX)
        nova = Matriz.objects.get(ano=a27, nome="Exceção GO")
        self.assertEqual(resp["HX-Redirect"], reverse("ui_matriz_detalhe", args=[nova.pk]))
        self.assertEqual(nova.duplicada_de, self.matriz)
        resp = self.client.post(url, {"ano": a27.pk, "nome": "Exceção GO"}, **HX)
        self.assertTemplateUsed(resp, "ui/parciais/matriz_form.html")
        self.assertTemplateNotUsed(resp, "ui/base.html")
        self.assertContains(resp, "Não duplicado: já existe a matriz Exceção GO em 2027")

        diff = reverse("ui_matriz_diferencas", args=[nova.pk])
        self.assertContains(self.client.get(diff), "Nenhuma diferença para Comunitária")
        Descritor.objects.filter(matriz_etapa_cc__matriz=nova, codigo="D02").update(descricao="Infere.")
        self.assertContains(self.client.get(diff), "5EF LP D02")

    def test_renomear(self):
        url = reverse("ui_matriz_renomear", args=[self.matriz.pk])
        resp = self.client.post(url, {"nome": "Comum"})
        self.assertRedirects(resp, reverse("ui_matriz_detalhe", args=[self.matriz.pk]), fetch_redirect_response=False)
        self.matriz.refresh_from_db()
        self.assertEqual(self.matriz.nome, "Comum")

    def test_reimportar_pede_o_nome_e_grava_pela_regra_do_admin(self):
        with tempfile.TemporaryDirectory() as tmp:
            xlsx = planilha(Path(tmp) / "m.xlsx", [("LP", "5EF", [(0, 200), (200, 500)], [
                ["D09", "Novo.", "", "–", "Tarefa N", "", "", "", ""],
            ])]).read_bytes()  # fmt: skip
        url = reverse("ui_matriz_reimportar", args=[self.matriz.pk])

        def enviar(**extra):
            return self.client.post(url, {"arquivo": SimpleUploadedFile("m.xlsx", xlsx), **extra})

        resp = enviar()
        self.assertContains(resp, "Digite Comunitária para confirmar")
        self.assertContains(resp, "Nada foi importado")
        self.assertEqual(set(self.mec.descritor_set.values_list("codigo", flat=True)), {"D01", "D02"})
        resp = enviar(confirmacao="Comunitária")
        self.assertRedirects(resp, reverse("ui_matriz_detalhe", args=[self.matriz.pk]), fetch_redirect_response=False)
        self.assertEqual(list(self.mec.descritor_set.values_list("codigo", flat=True)), ["D09"])

    def test_impresso_so_le_e_posts_403(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(reverse("ui_matriz_detalhe", args=[self.matriz.pk]))
        self.assertContains(resp, "Só leitura")
        self.assertNotContains(resp, 'data-abrir="dlg-duplicar"')
        for nome in ("ui_matriz_duplicar", "ui_matriz_renomear", "ui_matriz_reimportar"):
            self.assertEqual(self.client.post(reverse(nome, args=[self.matriz.pk]), {"nome": "X"}).status_code, 403)


class MecUiTest(BaseMundo):
    """T10/T11 com o mundo do resolver: MEC LP 5EF afeta 2 revistas (GO e PE)."""

    def setUp(self):
        super().setUp()
        self.d = self.tarefa.descritor
        self.mec = self.d.matriz_etapa_cc
        self.url = reverse("ui_matriz_descritor", args=[self.mec.pk, self.d.pk])

    def abrir(self, cliente=None):
        """GET da página (trava a MEC) e devolve a sessão da aba."""
        resp = (cliente or self.client).get(self.url)
        self.assertEqual(resp.status_code, 200)
        return resp.wsgi_request.bloqueio["sessao"]

    def dados(self, resp_ou_sessao, **mudar):
        tarefas = list(self.d.tarefa_set.order_by("ordem", "pk"))
        dados = {
            CAMPO_SESSAO: resp_ou_sessao, "codigo": self.d.codigo, "ordem": self.d.ordem, "descricao": self.d.descricao,
            "prerequisitos": "\n".join(self.d.prerequisitos), "praticas": self.d.praticas, "conhecimento": self.d.conhecimento,
            "habilidades_relacionadas": self.d.habilidades_relacionadas, "habilidade_correspondente": "",
            "tarefas-TOTAL_FORMS": len(tarefas) + 1, "tarefas-INITIAL_FORMS": len(tarefas),
            "tarefas-MIN_NUM_FORMS": 0, "tarefas-MAX_NUM_FORMS": 1000,
        }  # fmt: skip
        for i, t in enumerate(tarefas):
            dados.update({f"tarefas-{i}-id": t.pk, f"tarefas-{i}-descritor": self.d.pk, f"tarefas-{i}-inicio": t.inicio,
                          f"tarefas-{i}-fim": t.fim, f"tarefas-{i}-texto": t.texto, f"tarefas-{i}-ordem": t.ordem})  # fmt: skip
        return {**dados, **mudar}

    def test_pagina_lista_painel_e_busca_por_htmx(self):
        resp = self.client.get(reverse("ui_matriz_mec", args=[self.mec.pk]))
        self.assertTemplateUsed(resp, "ui/matriz/mec.html")
        self.assertContains(resp, "Salvar descritor")
        self.assertContains(resp, "Novo descritor")
        self.assertContains(resp, "2 de 2 descritores")
        self.assertContains(resp, "nucleo/bloqueio.js")
        self.assertContains(resp, f'data-abrir="item-{self.tarefa.pk}"')
        self.assertContains(resp, "perde(m) o “Validado”")
        busca = self.client.get(reverse("ui_matriz_mec", args=[self.mec.pk]), {"q": "d02"}, HTTP_HX_TARGET="lista-descritores", **HX)
        self.assertTemplateUsed(busca, "ui/parciais/matriz_lista.html")
        self.assertContains(busca, "1 de 2 descritores")
        self.assertNotContains(busca, "Descritor 1 LP")
        painel = self.client.get(self.url, **HX)
        self.assertTemplateUsed(painel, "ui/parciais/matriz_painel.html")
        self.assertTemplateNotUsed(painel, "ui/base.html")
        self.assertContains(painel, 'hx-swap-oob="true"')  # lista e mensagens fora do alvo

    def test_descritor_pede_impacto_e_grava_com_tarefa_nova(self):
        sessao = self.abrir()
        resp = self.client.post(self.url, self.dados(sessao, descricao="Localiza e infere."), **HX)
        self.assertContains(resp, "afeta 2 revista(s) ativa(s)")
        self.assertContains(resp, "Nada foi gravado: corrija os erros marcados.")
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Descritor 1 LP")

        n = self.d.tarefa_set.count()
        dados = self.dados(sessao, descricao="Localiza e infere.", confirmar_impacto="on", **{
            f"tarefas-{n}-inicio": 400, f"tarefas-{n}-fim": 450, f"tarefas-{n}-texto": "Nova.", f"tarefas-{n}-ordem": 9,
        })  # fmt: skip
        resp = self.client.post(self.url, dados, **HX)
        self.assertContains(resp, "Descritor D01 salvo.")
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Localiza e infere.")
        self.assertTrue(self.d.tarefa_set.filter(inicio=400, fim=450, texto="Nova.").exists())

    def test_tarefa_invalida_mostra_erro_e_nada_grava(self):
        sessao = self.abrir()
        resp = self.client.post(self.url, self.dados(sessao, confirmar_impacto="on", **{"tarefas-0-fim": 50}), **HX)
        self.assertContains(resp, "Nada foi gravado")
        self.assertContains(resp, "tarefa_inicio_menor_fim")  # a mesma mensagem do admin (restrição do banco)
        self.assertEqual(self.d.tarefa_set.filter(fim=50).count(), 0)

    def test_intervalo_minimo_com_confirmacao(self):
        sessao = self.abrir()
        url = reverse("ui_matriz_intervalo", args=[self.mec.pk])
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "passo": 50}, **HX)
        self.assertContains(resp, "afeta 2 revista(s) ativa(s)")
        self.mec.refresh_from_db()
        self.assertEqual(self.mec.passo, 25)
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "passo": 50, "confirmar_impacto": "on"}, **HX)
        self.assertContains(resp, "Intervalo mínimo de 5EF LP salvo.")
        self.mec.refresh_from_db()
        self.assertEqual(self.mec.passo, 50)

    def test_novo_descritor_abre_o_descritor_criado(self):
        sessao = self.abrir()
        url = reverse("ui_matriz_novo", args=[self.mec.pk])
        dados = {CAMPO_SESSAO: sessao, "codigo": "D09", "descricao": "Novo.", "ordem": 9, "confirmar_impacto": "on"}
        resp = self.client.post(url, dados, **HX)
        novo = Descritor.objects.get(matriz_etapa_cc=self.mec, codigo="D09")
        self.assertEqual(resp["HX-Redirect"], reverse("ui_matriz_descritor", args=[self.mec.pk, novo.pk]))
        resp = self.client.post(url, {**dados, CAMPO_SESSAO: self.abrir()}, **HX)
        self.assertContains(resp, "Já existe um descritor com este código")

    def test_arquivo_do_item_envia_e_remove(self):
        sessao = self.abrir()
        url = reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk])
        envio = {CAMPO_SESSAO: sessao, "arquivo": SimpleUploadedFile("a.png", PNG, "image/png"), "texto_alternativo": "Mapa"}
        resp = self.client.post(url, envio, **HX)
        self.assertContains(resp, "afeta 2 revista(s) ativa(s)")
        envio["arquivo"].seek(0)
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(url, {**envio, "confirmar_impacto": "on"}, **HX)
        self.assertContains(resp, "Arquivo do item enviado para a tarefa D01 100-150.")
        self.tarefa.refresh_from_db()
        caminho = self.tarefa.arquivo
        self.assertTrue(default_storage.exists(caminho))
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, {CAMPO_SESSAO: sessao, "confirmar_impacto": "on", "_remover": "1"}, **HX)
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)
        self.assertFalse(default_storage.exists(caminho))

    def test_excluir_tarefa_pede_o_codigo(self):
        url = reverse("ui_matriz_excluir_tarefa", args=[self.mec.pk, self.d.pk, self.tarefa.pk])
        resp = self.client.get(url)
        self.assertContains(resp, "Revistas ativas afetadas: 2")
        self.assertContains(resp, "D01 100-150")
        sessao = resp.wsgi_request.bloqueio["sessao"]
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "confirmacao": "D01"})
        self.assertContains(resp, "Nada foi excluído: o código não confere")
        self.assertTrue(Tarefa.objects.filter(pk=self.tarefa.pk).exists())
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "confirmacao": "D01 100-150"}, follow=True)
        self.assertRedirects(resp, self.url)
        self.assertContains(resp, "Tarefa D01 100-150 excluída.")
        self.assertFalse(Tarefa.objects.filter(pk=self.tarefa.pk).exists())

    def test_excluir_descritor(self):
        url = reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk])
        sessao = self.client.get(url).wsgi_request.bloqueio["sessao"]
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "confirmacao": "D01"})
        self.assertRedirects(resp, reverse("ui_matriz_mec", args=[self.mec.pk]), fetch_redirect_response=False)
        self.assertFalse(Descritor.objects.filter(pk=self.d.pk).exists())

    def test_impresso_so_le_e_todo_post_403(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Só leitura: seu perfil vê a matriz")
        self.assertContains(resp, "<fieldset disabled>")
        self.assertNotContains(resp, "Salvar descritor")
        self.assertNotContains(resp, "Excluir descritor")
        self.assertIsNone(resp.wsgi_request.bloqueio)
        for url in (
            self.url, reverse("ui_matriz_intervalo", args=[self.mec.pk]), reverse("ui_matriz_novo", args=[self.mec.pk]),
            reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk]),
            reverse("ui_matriz_excluir_tarefa", args=[self.mec.pk, self.d.pk, self.tarefa.pk]),
            reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk]),
        ):  # fmt: skip
            self.assertEqual(self.client.post(url, {"confirmacao": "D01"}).status_code, 403, url)

    def test_pedagogica_edita(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Salvar descritor")
        self.assertContains(resp, "Excluir descritor")

    def test_outra_pessoa_editando_so_le_e_nao_grava(self):
        bia = usuario("bia", "Pedagógica", first_name="Bia")
        self.assertTrue(bloqueio.adquirir(self.mec, bia, "aba-bia"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Somente leitura: Bia está editando")
        self.assertNotContains(resp, "Salvar descritor")
        resp = self.client.post(self.url, self.dados("minha", descricao="X", confirmar_impacto="on"))
        self.assertEqual(resp.status_code, 302)
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Descritor 1 LP")
        self.assertTrue(MatrizEtapaCC.objects.filter(pk=self.mec.pk, passo=25).exists())
