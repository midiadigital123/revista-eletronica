"""Matrizes e descritores B (/ui/matriz/, T09-T11): critérios de aceite de docs/telas/fichas/matriz.md."""

import tempfile
from unittest import mock
from pathlib import Path

from django.contrib.auth.models import Permission
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos import bloqueio
from nucleo.tests.test_admin_cadastro import Base as BaseCadastro
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_importacao import cadastrar, planilha
from nucleo.tests.test_item import PNG
from nucleo.tests.test_item import Base as BaseMundo
from nucleo.tests.test_resolver import usuario
from nucleo.urls.ui_matriz import DescritorUiForm, NovoDescritorForm, _tarefas

HX = {"HTTP_HX_REQUEST": "true"}


class MatrizUiTest(BaseCadastro):
    """T09: lista do ano, matriz, Duplicar, Renomear, Reimportar, Diferenças."""

    def test_anonimo_vai_ao_login_e_sem_permissao_403(self):
        urls = [reverse("ui_matriz", args=[2026]), reverse("ui_matriz_detalhe", args=[self.matriz.pk]),
                reverse("ui_matriz_mec", args=[self.mec.pk])]  # fmt: skip
        for url in urls:
            r = Client().get(url)
            self.assertRedirects(r, f"/conta/entrar/?next={url}", fetch_redirect_response=False)
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

    def test_nova_matriz_leva_ao_reimportar_e_nome_repetido_nao_grava(self):
        """S6: Pedagógica cria a matriz vazia do ano e cai no Reimportar (sem MEC, sem pedir confirmação)."""
        self.client.force_login(usuario("ped", "Pedagógica"))
        lista = reverse("ui_matriz", args=[2026])
        self.assertContains(self.client.get(lista), 'data-abrir="dlg-nova"')
        url = reverse("ui_matriz_nova", args=[2026])
        self.assertContains(self.client.get(url), 'name="nome"')
        resp = self.client.post(url, {"ano": self.a26.pk, "nome": "Municipal"})
        nova = Matriz.objects.get(ano=self.a26, nome="Municipal")
        self.assertRedirects(resp, reverse("ui_matriz_reimportar", args=[nova.pk]))
        self.assertContains(resp := self.client.get(reverse("ui_matriz_reimportar", args=[nova.pk])), "Reimportar Municipal")
        self.assertNotContains(resp, "Digite Municipal para confirmar")
        resp = self.client.post(url, {"ano": self.a26.pk, "nome": "Municipal"}, **HX)
        self.assertTemplateUsed(resp, "ui/parciais/matriz_form.html")
        self.assertContains(resp, "Já existe uma matriz com este nome neste ano.")
        self.assertEqual(Matriz.objects.filter(ano=self.a26, nome="Municipal").count(), 1)

    def test_nova_matriz_so_para_quem_cria(self):
        self.client.force_login(usuario("imp", "Impresso"))
        lista = self.client.get(reverse("ui_matriz", args=[2026]))
        self.assertNotContains(lista, "dlg-nova")
        self.assertNotContains(lista, "Nova matriz")
        url = reverse("ui_matriz_nova", args=[2026])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"ano": self.a26.pk, "nome": "X"}).status_code, 403)
        self.assertFalse(Matriz.objects.filter(nome="X").exists())

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

    def test_renomear_inline_pelo_protocolo(self):
        """U5: o nome se edita no título (nomeInline), pelo protocolo do autosave (U3)."""
        url = reverse("ui_matriz_renomear", args=[self.matriz.pk])
        resp = self.client.get(reverse("ui_matriz_detalhe", args=[self.matriz.pk]))
        self.assertContains(resp, 'x-data="nomeInline"')
        self.assertContains(resp, f'data-url="{url}"')
        self.assertNotContains(resp, "dlg-renomear")
        json_ = {"HTTP_ACCEPT": "application/json"}
        corpo = self.client.post(url, {"campo": "nome", "valor": "Comum", "original": "Comunitária"}, **json_).json()
        self.assertTrue(corpo["ok"])
        self.assertEqual(corpo["valor"], "Comum")
        self.matriz.refresh_from_db()
        self.assertEqual(self.matriz.nome, "Comum")
        Matriz.objects.create(ano=self.matriz.ano, nome="Outra")
        for valor in ("", "Outra"):
            r = self.client.post(url, {"campo": "nome", "valor": valor}, **json_)
            self.assertEqual(r.status_code, 422, valor)
            self.assertTrue(r.json()["erros"])
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

    def test_excluir_matriz_leva_a_pagina_comum_e_volta_para_a_lista(self):
        """E3 (D-205): zona de perigo no fim do detalhe → ui_excluir, com ?voltar= para as matrizes do ano."""
        url = reverse("ui_excluir", args=["matriz", self.matriz.pk])
        link = f'{url}?voltar={reverse("ui_matriz", args=[2026])}'
        for papel in ("Pedagógica", "Mídias Digitais", "Admin"):
            self.client.force_login(usuario(f"u-{papel}", papel))
            html = self.client.get(reverse("ui_matriz_detalhe", args=[self.matriz.pk])).content.decode()
            self.assertIn(f'href="{link}"', html, papel)
            self.assertIn("Excluir matriz…", html, papel)
            self.assertGreater(html.index(link), html.index("matriz-tabela"), "fim da página, não no topo")
        # a página comum (E0) recebe o voltar
        self.assertContains(self.client.get(link), f'href="{reverse("ui_matriz", args=[2026])}"')

    def test_impresso_so_le_e_posts_403(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(reverse("ui_matriz_detalhe", args=[self.matriz.pk]))
        self.assertContains(resp, "Só leitura")
        self.assertNotContains(resp, 'data-abrir="dlg-duplicar"')
        self.assertNotContains(resp, reverse("ui_excluir", args=["matriz", self.matriz.pk]))
        self.assertNotContains(resp, "zona-perigo")
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
            f"tarefas-{len(tarefas)}-ordem": len(tarefas) + 1,  # a linha em branco vem com a ordem, como no navegador
        }  # fmt: skip
        for i, t in enumerate(tarefas):
            dados.update({f"tarefas-{i}-id": t.pk, f"tarefas-{i}-descritor": self.d.pk, f"tarefas-{i}-inicio": t.inicio,
                          f"tarefas-{i}-fim": t.fim, f"tarefas-{i}-texto": t.texto, f"tarefas-{i}-ordem": t.ordem})  # fmt: skip
        return {**dados, **mudar}

    def test_pagina_lista_painel_e_busca_por_htmx(self):
        resp = self.client.get(reverse("ui_matriz_mec", args=[self.mec.pk]))
        self.assertTemplateUsed(resp, "ui/matriz/mec.html")
        self.assertContains(resp, "Incluir tarefa")
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

    def test_descritor_sem_validada_grava_direto_com_tarefa_nova(self):
        """Afeta 2 revistas, mas nenhuma validada: não há "Validado" a perder, grava sem modal (U2)."""
        sessao = self.abrir()
        n = self.d.tarefa_set.count()
        dados = self.dados(sessao, descricao="Localiza e infere.", **{
            f"tarefas-{n}-inicio": 400, f"tarefas-{n}-fim": 450, f"tarefas-{n}-texto": "Nova.", f"tarefas-{n}-ordem": 9,
        })  # fmt: skip
        resp = self.client.post(self.url, dados, **HX)
        self.assertContains(resp, "Descritor D01 salvo.")
        self.assertNotContains(resp, "data-abrir-ao-carregar")
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Localiza e infere.")
        self.assertTrue(self.d.tarefa_set.filter(inicio=400, fim=450, texto="Nova.").exists())

    def test_descritor_salva_sem_preencher_a_tarefa_nova(self):
        """A linha em branco chega com a ordem preenchida (como no navegador) e não é validada."""
        sessao = self.abrir()
        n = self.d.tarefa_set.count()
        resp = self.client.post(self.url, self.dados(sessao, descricao="Só o texto.", confirmar_impacto="on"), **HX)
        self.assertContains(resp, "Descritor D01 salvo.")
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Só o texto.")
        self.assertEqual(self.d.tarefa_set.count(), n)

    def test_excluir_sem_ver_403_sem_travar(self):
        u = usuario("so_exclui")
        u.user_permissions.add(Permission.objects.get(codename="delete_descritor"))
        self.client.force_login(u)
        url = reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertIsNone(bloqueio.quem_bloqueia(self.mec))

    def test_tarefa_invalida_mostra_erro_e_nada_grava(self):
        sessao = self.abrir()
        resp = self.client.post(self.url, self.dados(sessao, confirmar_impacto="on", **{"tarefas-0-fim": 50}), **HX)
        self.assertContains(resp, "Nada foi gravado")
        self.assertContains(resp, "tarefa_inicio_menor_fim")  # a mesma mensagem do admin (restrição do banco)
        self.assertEqual(self.d.tarefa_set.filter(fim=50).count(), 0)

    def test_intervalo_minimo_sem_validada_grava_direto(self):
        sessao = self.abrir()
        url = reverse("ui_matriz_intervalo", args=[self.mec.pk])
        resp = self.client.post(url, {CAMPO_SESSAO: sessao, "passo": 50}, **HX)
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
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(url, envio, **HX)
        self.assertContains(resp, "Arquivo do item enviado para a tarefa D01 100-150.")
        self.tarefa.refresh_from_db()
        caminho = self.tarefa.arquivo
        self.assertTrue(default_storage.exists(caminho))
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, {CAMPO_SESSAO: sessao, "confirmar_impacto": "on", "_remover": "1"}, **HX)
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)
        self.assertFalse(default_storage.exists(caminho))

    def test_arquivo_do_item_baixa_pela_tela_b(self):
        """S8: o link do item e o download são da tela B (nada de admin:), só leitura e fora do bloqueio."""
        sessao = self.abrir()
        envio = {CAMPO_SESSAO: sessao, "arquivo": SimpleUploadedFile("a.png", PNG, "image/png")}
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk]), envio, **HX)
        self.tarefa.refresh_from_db()
        url = reverse("ui_matriz_item_baixar", args=[self.mec.pk, self.d.pk, self.tarefa.pk])
        pagina = self.client.get(self.url)
        self.assertContains(pagina, f'href="{url}"')
        self.assertNotContains(pagina, "/admin/nucleo/descritor/")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertTrue(resp["Content-Disposition"].startswith("attachment"))
        self.assertEqual(b"".join(resp.streaming_content), PNG)
        self.assertEqual(self.client.post(url).status_code, 405)  # só GET
        default_storage.delete(self.tarefa.arquivo)
        self.assertEqual(self.client.get(url).status_code, 404)  # sumiu do storage
        Tarefa.objects.filter(pk=self.tarefa.pk).update(arquivo=None)
        self.assertEqual(self.client.get(url).status_code, 404)  # sem arquivo
        Tarefa.objects.filter(pk=self.tarefa.pk).update(arquivo="itens/x.exe")
        self.assertEqual(self.client.get(url).status_code, 404)  # tipo desconhecido
        self.client.force_login(usuario("nada"))
        self.assertEqual(self.client.get(url).status_code, 403)

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
        self.assertNotContains(resp, "Incluir tarefa")
        self.assertNotContains(resp, "Excluir descritor")
        self.assertIsNone(resp.wsgi_request.bloqueio)
        for url in (
            self.url, reverse("ui_matriz_intervalo", args=[self.mec.pk]), reverse("ui_matriz_novo", args=[self.mec.pk]),
            reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk]),
            reverse("ui_matriz_excluir_tarefa", args=[self.mec.pk, self.d.pk, self.tarefa.pk]),
            reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk]),
        ):  # fmt: skip
            self.assertEqual(self.client.post(url, {"confirmacao": "D01"}).status_code, 403, url)
        for url in (  # nem a página de excluir abre (auditoria 03/11: era 200 sem botão)
            reverse("ui_matriz_excluir_tarefa", args=[self.mec.pk, self.d.pk, self.tarefa.pk]),
            reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk]),
        ):  # fmt: skip
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_pedagogica_edita(self):
        self.client.force_login(usuario("ped", "Pedagógica"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Incluir tarefa")
        self.assertContains(resp, "Excluir descritor")

    def test_outra_pessoa_editando_so_le_e_nao_grava(self):
        bia = usuario("bia", "Pedagógica", first_name="Bia")
        self.assertTrue(bloqueio.adquirir(self.mec, bia, "aba-bia"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Somente leitura: Bia está editando")
        self.assertNotContains(resp, "Incluir tarefa")
        resp = self.client.post(self.url, self.dados("minha", descricao="X", confirmar_impacto="on"))
        self.assertEqual(resp.status_code, 302)
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Descritor 1 LP")
        self.assertTrue(MatrizEtapaCC.objects.filter(pk=self.mec.pk, passo=25).exists())


class MecImpactoTest(BaseMundo):
    """U2: com GO LP validada, editar a MEC LP 5EF abre o modal de impacto antes de gravar."""

    abrir = MecUiTest.abrir
    dados = MecUiTest.dados

    def setUp(self):
        super().setUp()
        self.d = self.tarefa.descritor
        self.mec = self.d.matriz_etapa_cc
        self.url = reverse("ui_matriz_descritor", args=[self.mec.pk, self.d.pk])
        self.rev = self.go["LP"]
        validar(self.rev)
        self.sessao = self.abrir()

    def assertModal(self, resp, form_id, acao):
        self.assertContains(resp, "<dialog")
        self.assertContains(resp, f'data-abrir-ao-carregar data-form="{form_id}"')
        self.assertContains(resp, f"{acao} tira o “Validado” de 1 revista(s)")
        self.assertContains(resp, f"<li>{self.rev}</li>")
        self.assertNotContains(resp, "corrija os erros")
        self.assertTrue(esta_validada(self.rev))

    def assertPerdeu(self, resp):
        self.assertContains(resp, "1 revista(s) perderam o “Validado”")
        self.assertFalse(esta_validada(self.rev))

    def test_descritor_sem_confirmar_abre_modal_e_nao_grava(self):
        resp = self.client.post(self.url, self.dados(self.sessao, descricao="Outra."), **HX)
        self.assertModal(resp, "form-descritor", "Incluir tarefa")
        self.assertContains(resp, 'data-original="Descritor 1 LP"')
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Descritor 1 LP")

    def test_descritor_confirmado_grava_e_tira_validado(self):
        resp = self.client.post(self.url, self.dados(self.sessao, descricao="Outra.", confirmar_impacto="on"), **HX)
        self.assertContains(resp, "Descritor D01 salvo.")
        self.assertPerdeu(resp)
        self.d.refresh_from_db()
        self.assertEqual(self.d.descricao, "Outra.")

    def test_descritor_sem_mudanca_nao_pede(self):
        resp = self.client.post(self.url, self.dados(self.sessao), **HX)
        self.assertContains(resp, "Descritor D01 salvo.")
        self.assertTrue(esta_validada(self.rev))

    def test_intervalo_sem_confirmar_abre_modal_e_nao_grava(self):
        url = reverse("ui_matriz_intervalo", args=[self.mec.pk])
        resp = self.client.post(url, {CAMPO_SESSAO: self.sessao, "passo": 50}, **HX)
        self.assertModal(resp, "form-intervalo", "Salvar intervalo")
        self.mec.refresh_from_db()
        self.assertEqual(self.mec.passo, 25)

    def test_intervalo_confirmado_grava_e_tira_validado(self):
        url = reverse("ui_matriz_intervalo", args=[self.mec.pk])
        resp = self.client.post(url, {CAMPO_SESSAO: self.sessao, "passo": 50, "confirmar_impacto": "on"}, **HX)
        self.assertContains(resp, "Intervalo mínimo de 5EF LP salvo.")
        self.assertPerdeu(resp)
        self.mec.refresh_from_db()
        self.assertEqual(self.mec.passo, 50)

    def test_novo_descritor_sem_confirmar_abre_modal_e_nao_grava(self):
        url = reverse("ui_matriz_novo", args=[self.mec.pk])
        resp = self.client.post(url, {CAMPO_SESSAO: self.sessao, "codigo": "D09", "descricao": "Novo.", "ordem": 9}, **HX)
        self.assertModal(resp, "form-novo", "Criar descritor")
        self.assertFalse(Descritor.objects.filter(matriz_etapa_cc=self.mec, codigo="D09").exists())

    def test_novo_descritor_confirmado_grava_e_tira_validado(self):
        url = reverse("ui_matriz_novo", args=[self.mec.pk])
        dados = {CAMPO_SESSAO: self.sessao, "codigo": "D09", "descricao": "Novo.", "ordem": 9, "confirmar_impacto": "on"}
        self.assertIn("HX-Redirect", self.client.post(url, dados, **HX))
        self.assertTrue(Descritor.objects.filter(matriz_etapa_cc=self.mec, codigo="D09").exists())
        self.assertFalse(esta_validada(self.rev))

    def test_item_modal_lista_quem_perde(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, f"<li>{self.rev}</li>")
        self.assertContains(resp, "Enviar e tirar Validado")
        self.assertContains(resp, 'name="confirmar_impacto" value="True"')

    def test_item_sem_confirmar_abre_modal_e_nao_grava(self):
        url = reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk])
        envio = {CAMPO_SESSAO: self.sessao, "arquivo": SimpleUploadedFile("a.png", PNG, "image/png")}
        resp = self.client.post(url, envio, **HX)
        self.assertContains(resp, f'x-data="impacto" data-abrir-ao-carregar data-form="item-form-{self.tarefa.pk}"')
        self.assertContains(resp, f"<li>{self.rev}</li>")
        self.assertContains(resp, "Nada foi enviado")
        self.tarefa.refresh_from_db()
        self.assertIsNone(self.tarefa.arquivo)
        self.assertTrue(esta_validada(self.rev))

    def test_item_confirmado_grava_e_tira_validado(self):
        url = reverse("ui_matriz_item", args=[self.mec.pk, self.d.pk, self.tarefa.pk])
        envio = {CAMPO_SESSAO: self.sessao, "arquivo": SimpleUploadedFile("a.png", PNG, "image/png"), "confirmar_impacto": "True"}
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(url, envio, **HX)
        self.assertContains(resp, "Arquivo do item enviado")
        self.assertPerdeu(resp)


class MecLinhasTest(BaseMundo):
    """U4: descritores e tarefas sem campo de ordem, linha nova pelo botão e reordenar sob o bloqueio da MEC."""

    abrir = MecUiTest.abrir
    dados = MecUiTest.dados

    def setUp(self):
        super().setUp()
        self.d = self.tarefa.descritor
        self.mec = self.d.matriz_etapa_cc
        self.url = reverse("ui_matriz_descritor", args=[self.mec.pk, self.d.pk])
        self.outra = Tarefa.objects.create(descritor=self.d, inicio=300, fim=350, texto="Outra.", ordem=7)
        self.reordenar_d = reverse("ui_matriz_reordenar", args=[self.mec.pk])
        self.reordenar_t = reverse("ui_matriz_reordenar", args=[self.mec.pk, self.d.pk])

    def descritores(self):
        return list(Descritor.objects.filter(matriz_etapa_cc=self.mec).order_by("ordem", "pk").values_list("pk", flat=True))

    def tarefas(self):
        return list(Tarefa.objects.filter(descritor=self.d).order_by("ordem", "pk").values_list("pk", flat=True))

    def postar(self, url, sessao, ids, **extra):
        return self.client.post(url, {CAMPO_SESSAO: sessao, "ids": ids, **extra}, HTTP_ACCEPT="application/json")

    def test_form_sem_campo_ordem(self):
        for Form in (DescritorUiForm, NovoDescritorForm, _tarefas(0).form):
            self.assertNotIn("ordem", Form().fields, Form)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, 'name="ordem"')
        self.assertNotContains(resp, "tarefas-0-ordem")
        self.assertNotContains(resp, ">Ordem<")

    def test_novo_descritor_e_nova_tarefa_vao_para_o_fim(self):
        sessao = self.abrir()
        maior = max(Descritor.objects.filter(matriz_etapa_cc=self.mec).values_list("ordem", flat=True))
        dados = {CAMPO_SESSAO: sessao, "codigo": "D09", "descricao": "Novo.", "confirmar_impacto": "on"}
        self.client.post(reverse("ui_matriz_novo", args=[self.mec.pk]), dados, **HX)
        self.assertEqual(Descritor.objects.get(matriz_etapa_cc=self.mec, codigo="D09").ordem, maior + 1)
        n = self.d.tarefa_set.count()
        dados = self.dados(self.abrir(), **{f"tarefas-{n}-inicio": 400, f"tarefas-{n}-fim": 450, f"tarefas-{n}-texto": "Nova."})
        self.assertContains(self.client.post(self.url, dados, **HX), "Descritor D01 salvo.")
        maior = max(Tarefa.objects.filter(descritor=self.d).exclude(texto="Nova.").values_list("ordem", flat=True))
        self.assertEqual(Tarefa.objects.get(descritor=self.d, texto="Nova.").ordem, maior + 1)

    def test_reordenar_grava_1_a_n(self):
        sessao = self.abrir()
        for url, ler in ((self.reordenar_d, self.descritores), (self.reordenar_t, self.tarefas)):
            with self.subTest(url=url):
                invertida = ler()[::-1]
                r = self.postar(url, sessao, invertida, confirmar_impacto="on")
                self.assertEqual(r.status_code, 200, r.content)
                self.assertTrue(r.json()["ok"])
                self.assertEqual(ler(), invertida)
        ordens = list(Tarefa.objects.filter(descritor=self.d).order_by("ordem").values_list("ordem", flat=True))
        self.assertEqual(ordens, list(range(1, len(ordens) + 1)))

    def test_reordenar_lista_incompleta_422(self):
        sessao = self.abrir()
        d, t = self.descritores(), self.tarefas()
        alheia = Tarefa.objects.exclude(descritor=self.d).first()
        casos = ((self.reordenar_d, d[:-1]), (self.reordenar_d, [*d, d[0]]), (self.reordenar_t, [t[0], alheia.pk]), (self.reordenar_t, ["x"]))
        for url, ids in casos:
            with self.subTest(url=url, ids=ids):
                r = self.postar(url, sessao, ids, confirmar_impacto="on")
                self.assertEqual(r.status_code, 422, r.content)
        self.assertEqual((self.descritores(), self.tarefas()), (d, t))

    def test_reordenar_com_validada_simula_e_grava_direto(self):
        """A revista mostra descritores e tarefas pela própria regra, não pela `ordem`: a simulação
        não acha quem perca o "Validado" e grava sem modal."""
        rev = self.go["LP"]
        validar(rev)
        sessao = self.abrir()
        invertida = self.tarefas()[::-1]
        self.assertTrue(self.postar(self.reordenar_t, sessao, invertida).json()["ok"])
        self.assertEqual(self.tarefas(), invertida)
        self.assertTrue(esta_validada(rev))

    def test_reordenar_impacto_e_bloqueio(self):
        """Se a ordem tirasse o "Validado" (simulado aqui), o reordenar segue o protocolo do autosave."""
        rev = self.go["LP"]
        sessao = self.abrir()
        antes = self.descritores()
        invertida = antes[::-1]
        with mock.patch("nucleo.ui_autosave.perdem_validado", return_value=[rev]):
            r = self.postar(self.reordenar_d, sessao, invertida, form_id="ordem-lista-ordem")
            self.assertEqual(r.status_code, 200)
            self.assertIn(str(rev), r.json()["impacto"]["perdem"])
            self.assertIn('data-form="ordem-lista-ordem"', r.json()["impacto"]["html"])
            self.assertEqual(self.descritores(), antes)
            self.assertTrue(self.postar(self.reordenar_d, sessao, invertida, confirmar_impacto="on").json()["ok"])
        self.assertEqual(self.descritores(), invertida)
        self.assertTrue(bloqueio.adquirir(self.mec, self.root, "outra-aba"))
        self.assertEqual(self.postar(self.reordenar_d, sessao, antes).status_code, 409)
        self.assertEqual(self.descritores(), invertida)

    def test_reordenar_impresso_403(self):
        self.client.force_login(usuario("imp", "Impresso"))
        antes = self.descritores()
        self.assertEqual(self.postar(self.reordenar_d, "x", antes[::-1]).status_code, 403)
        self.assertEqual(self.descritores(), antes)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "use as setas para cima e para baixo")
        self.assertNotContains(resp, "Adicionar tarefa")

    def test_sem_linha_vazia(self):
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "Tarefa nova: preencha")
        self.assertEqual(resp.context["tarefas"].extra, 0)
        self.assertEqual(len(resp.context["tarefas"].forms), self.d.tarefa_set.count())  # só as gravadas
        self.assertContains(resp, "Adicionar tarefa")
        self.assertContains(resp, 'x-data="linhaNova"')
        self.assertContains(resp, f'data-ordem-url="{self.reordenar_d}"')
        self.assertContains(resp, f'data-ordem-url="{self.reordenar_t}"')

    def test_alca_e_o_botao_de_teclado(self):
        """Item 4: sem os botões ↑↓; a alça é um <button> com nome acessível e há um aria-live por lista."""
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "data-mover")
        self.assertNotContains(resp, "Mover para cima:")
        self.assertContains(resp, f'<button type="button" class="alca" aria-label="Mover {self.d.codigo}: use as setas para cima e para baixo"', html=False)
        t = self.d.tarefa_set.first()
        self.assertContains(resp, f'aria-label="Mover {t.codigo}: use as setas para cima e para baixo"')


class MecHierarquiaTest(BaseMundo):
    """U9: cabeçalho com "Configurações" (popover com o intervalo mínimo, autosave com impacto),
    "+ Novo descritor" no topo da lista e "Excluir descritor" numa zona de perigo no fim do painel."""

    abrir = MecUiTest.abrir

    def setUp(self):
        super().setUp()
        self.d = self.tarefa.descritor
        self.mec = self.d.matriz_etapa_cc
        self.url = reverse("ui_matriz_descritor", args=[self.mec.pk, self.d.pk])
        self.intervalo = reverse("ui_matriz_intervalo", args=[self.mec.pk])

    def campo(self, sessao, valor, **extra):
        dados = {CAMPO_SESSAO: sessao, "campo": "passo", "valor": valor, "form_id": "form-intervalo", **extra}
        return self.client.post(self.intervalo, dados, HTTP_ACCEPT="application/json")

    def test_cabecalho_lista_e_zona_de_perigo(self):
        html = self.client.get(self.url).content.decode()
        cab = html[html.index('<header class="pagina-cab">') : html.index("</header>", html.index('<header class="pagina-cab">'))]
        self.assertIn('popovertarget="mec-config"', cab)
        self.assertIn("Configurações", cab)
        self.assertIn("data-status-salvo", cab)
        self.assertNotIn("Novo descritor", cab)
        self.assertLess(cab.index('id="mec-config" popover'), cab.index("Intervalo mínimo"))  # dentro do popover
        lista = html.index('aria-label="Descritores de')
        novo = html.index('data-abrir="dlg-novo"')
        self.assertLess(lista, novo)
        self.assertLess(novo, html.index('id="lista-descritores"'))
        self.assertIn('class="btn btn-outline', html[novo - 80 : novo])
        perigo = html.index('class="zona-perigo"')
        self.assertLess(html.index('id="sec-tarefas"'), perigo)
        self.assertLess(perigo, html.index("Excluir descritor"))
        self.assertEqual(html.count("Excluir descritor"), 1)  # só o título da zona de perigo, nada no topo
        self.assertIn(f'aria-label="Excluir o descritor {self.d.codigo}"', html[perigo:])

    def test_excluir_continua_exigindo_o_codigo(self):
        url = reverse("ui_matriz_excluir_descritor", args=[self.mec.pk, self.d.pk])
        sessao = self.client.get(url).wsgi_request.bloqueio["sessao"]
        self.assertContains(self.client.post(url, {CAMPO_SESSAO: sessao, "confirmacao": "D0"}), "o código não confere")
        self.assertTrue(Descritor.objects.filter(pk=self.d.pk).exists())

    def test_intervalo_autosave_impacto_bloqueio_e_403(self):
        sessao = self.abrir()
        r = self.campo(sessao, "40")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()["ok"])
        self.mec.refresh_from_db()
        self.assertEqual(self.mec.passo, 40)
        self.assertEqual(self.campo(sessao, "0").status_code, 422)
        rev = self.go["LP"]
        validar(rev)
        corpo = self.campo(sessao, "45").json()
        self.assertIn(str(rev), corpo["impacto"]["perdem"])
        self.assertIn('data-form="form-intervalo"', corpo["impacto"]["html"])
        self.assertEqual(MatrizEtapaCC.objects.get(pk=self.mec.pk).passo, 40)
        self.assertTrue(self.campo(sessao, "45", confirmar_impacto="on").json()["ok"])
        self.assertEqual(MatrizEtapaCC.objects.get(pk=self.mec.pk).passo, 45)
        self.assertFalse(esta_validada(rev))
        self.assertTrue(bloqueio.adquirir(self.mec, self.root, "outra-aba"))
        self.assertEqual(self.campo(sessao, "50").status_code, 409)
        self.client.force_login(usuario("imp", "Impresso"))
        self.assertEqual(self.campo("x", "50").status_code, 403)
        self.assertEqual(MatrizEtapaCC.objects.get(pk=self.mec.pk).passo, 45)

    def test_impresso_ve_configuracoes_so_leitura(self):
        self.client.force_login(usuario("imp", "Impresso"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Configurações")
        self.assertNotContains(resp, 'data-abrir="dlg-novo"')
        self.assertNotContains(resp, "zona-perigo")
        self.assertNotContains(resp, 'x-data="campoAuto" data-url="' + self.intervalo)
