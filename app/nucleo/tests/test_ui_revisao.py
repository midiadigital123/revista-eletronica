"""Tela "Revisar mudanças da base" (D-292): /ui/revisao/<pk>/, a revisão da etapa do projeto contra a base."""

from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Descritor, MatrizEtapaCC, Tarefa
from nucleo.servicos import bloqueio
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.etapa_projeto import RevisaoMudou, criar, pendente, revisao
from nucleo.servicos.resolver import carregar, resolver
from nucleo.tests.test_admin_padrao import esta_validada, validar
from nucleo.tests.test_ui_projeto_abas import EtapaNaoCanonica

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
CAMPOS = {"e": "escolha-", "t": "texto-"}


class RevisaoTelaTest(EtapaNaoCanonica):
    """4EF LP do GO apontada para o 5EF LP da Comunitária: D01 (tarefas 100-150 e 225-275) e D02 (300-350)."""

    def copiar(self):
        self.mec = criar(self.projeto_go, self.e4, self.lp, self.usuario, base=self.mec5)
        self.url_rev = reverse("ui_revisao", args=[self.mec.pk])
        return self.mec

    def desc(self, mec, codigo):
        return Descritor.objects.filter(matriz_etapa_cc=mec, codigo=codigo)

    def tar(self, mec, inicio):
        return Tarefa.objects.filter(descritor__matriz_etapa_cc=mec, inicio=inicio)

    def arquivo(self, i, lado):
        return reverse("ui_revisao_arquivo", args=[self.mec.pk, i, lado])

    def concluir(self, **dados):
        """Abre a tela (pega o bloqueio e o `visto`) e conclui com as escolhas: `e0="local"` é `escolha-0`."""
        r = self.client.get(self.url_rev)
        form = {CAMPO_SESSAO: r.wsgi_request.bloqueio["sessao"], "visto": r.context["visto"]}
        form.update({CAMPOS[k[0]] + k[1:] if k[1:].isdigit() else k: v for k, v in dados.items()})
        return self.client.post(self.url_rev, form)

    def conflito_em_d01(self):
        """D01: a base e o projeto mudaram a descrição (decisão); D02: só a base mudou (entra)."""
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.desc(mec, "D01").update(descricao="Do projeto")
        self.desc(self.mec5, "D02").update(descricao="Descritor dois")
        return mec

    def intacta(self, mec):
        """Nada foi gravado: a pendência segue e o projeto tem o que tinha."""
        mec.refresh_from_db()
        self.assertTrue(pendente(mec))
        self.assertEqual(self.desc(mec, "D01").get().descricao, "Do projeto")
        self.assertEqual(self.desc(mec, "D02").get().descricao, "Descritor 2")

    # --- Leitura ---

    def test_decisoes_primeiro_e_o_resto_recolhido_e_pre_marcado(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.desc(mec, "D01").update(descricao="Do projeto")
        self.desc(self.mec5, "D02").update(descricao="Descritor dois")
        r = self.client.get(self.url_rev)
        html = r.content.decode()
        self.assertContains(r, "<h1>Revisar mudanças da base · 4EF LP</h1>")
        self.assertContains(r, "A base desta etapa, 5EF LP da Comunitária 2026, mudou. Nada muda no projeto até você clicar em Concluir revisão.")
        self.assertContains(r, "1 precisa da sua decisão · 1 entra da base sem conflito")
        self.assertLess(html.index("Precisa da sua decisão"), html.index("Entram da base sem conflito"))
        self.assertContains(r, '<details class="recolhivel rev-grupo">')  # fechado
        self.assertContains(r, "<legend>D01 · Descrição</legend>")
        self.assertContains(r, "<legend>D02 · Descrição</legend>")
        # a decisão não vem marcada e é obrigatória; o que entra já vem em "Usar o da base"
        self.assertContains(r, '<input type="radio" name="escolha-0" value="local" required>')
        self.assertContains(r, '<input type="radio" name="escolha-0" value="base" required>')
        self.assertContains(r, '<input type="radio" name="escolha-1" value="base" checked>')
        for rotulo in ("Manter o do projeto", "Usar o da base", "Escrever outro texto"):
            self.assertContains(r, rotulo)
        # o form sai completo
        self.assertContains(r, f'<form method="post" action="{self.url_rev}"')
        self.assertContains(r, 'name="csrfmiddlewaretoken"')
        self.assertContains(r, f'name="{CAMPO_SESSAO}"')
        mec.refresh_from_db()
        self.assertContains(r, f'<input type="hidden" name="visto" value="{revisao(mec)[1]}">')
        self.assertContains(r, ">Concluir revisão</button>")
        self.assertContains(r, ">Voltar sem concluir</a>")
        self.assertContains(r, "As escolhas só são gravadas ao concluir.")
        self.assertEqual(bloqueio.quem_bloqueia(mec).usuario, self.ped)

    def test_diff_por_palavra_e_como_era(self):
        self.copiar()
        self.desc(self.mec5, "D02").update(descricao="Descritor dois")
        r = self.client.get(self.url_rev)
        self.assertContains(r, "<h3>No projeto</h3>")
        self.assertContains(r, "<h3>Na base agora</h3>")
        self.assertContains(r, 'Descritor <del><span class="sr-only">saiu: </span>2</del><ins><span class="sr-only">entrou: </span>dois</ins>')
        self.assertContains(r, "<summary>Como era quando o projeto copiou</summary>")

    def test_sem_o_vocabulario_do_servico(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.desc(mec, "D01").update(descricao="Do projeto")
        html = self.client.get(self.url_rev).content.decode()
        self.assertNotIn("3 vias", html)
        self.assertNotIn("foto", html)
        self.assertEqual(html.count("conflito"), html.count("sem conflito"))  # só no título do grupo que entra

    def test_ordem_num_cartao_so(self):
        self.copiar()
        self.desc(self.mec5, "D01").update(ordem=9)
        self.desc(self.mec5, "D02").update(ordem=8)
        self.tar(self.mec5, 100).update(ordem=1)
        self.tar(self.mec5, 225).update(ordem=2)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "<legend>A ordem dos descritores mudou na base</legend>", count=1)
        self.assertContains(r, "<legend>D01 · a ordem das tarefas mudou na base</legend>", count=1)
        self.assertContains(r, "<fieldset", count=3)  # o do form e os dois cartões: 4 células, 2 escolhas
        self.assertContains(r, 'name="escolha-0" value="base" checked')
        self.assertContains(r, 'name="escolha-1" value="base" checked')
        self.assertNotContains(r, 'name="escolha-2"')
        self.assertContains(r, "Usar a ordem da base", count=2)
        self.assertContains(r, "Manter a ordem do projeto", count=2)
        self.assertContains(r, "D01, D02")  # no projeto
        self.assertContains(r, "D02, D01")  # na base agora
        self.assertContains(r, "Não muda a revista", count=1)  # só no cartão das tarefas

    def test_ordem_so_renumerada_avisa_que_a_sequencia_e_a_mesma(self):
        self.copiar()
        self.desc(self.mec5, "D01").update(ordem=5)
        self.desc(self.mec5, "D02").update(ordem=6)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "D01, D02", count=3)  # os três lados iguais
        self.assertContains(r, "A sequência é a mesma dos dois lados: só a numeração mudou na base.", count=1)
        self.desc(self.mec5, "D01").update(ordem=7)  # agora troca de lugar
        self.assertNotContains(self.client.get(self.url_rev), "A sequência é a mesma")

    def test_item_inteiro_com_as_opcoes_certas(self):
        self.copiar()
        d3 = Descritor.objects.create(matriz_etapa_cc=self.mec5, codigo="D03", descricao="Descritor novo", ordem=3)
        Tarefa.objects.create(descritor=d3, inicio=100, fim=150, texto="Tarefa nova.", ordem=1)
        self.desc(self.mec5, "D02").delete()
        Tarefa.objects.create(descritor=self.desc(self.mec5, "D01").get(), inicio=400, fim=450, texto="Mais uma.", ordem=3)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "<legend>D03 · descritor</legend>")
        self.assertContains(r, "A base criou este descritor.")
        self.assertContains(r, "Descritor novo")
        self.assertContains(r, "1 tarefa(s)")
        self.assertContains(r, "<legend>D02 · descritor</legend>")
        self.assertContains(r, "A base apagou este descritor.")
        self.assertContains(r, "<legend>D01 · tarefa 400–450</legend>")
        self.assertContains(r, "A base criou esta tarefa.")
        self.assertContains(r, "Trazer para o projeto", count=2)
        self.assertContains(r, "Não trazer", count=2)
        self.assertContains(r, "Apagar também", count=1)
        self.assertContains(r, "> Manter</label>", count=1)
        self.assertNotContains(r, "Escrever outro texto")

    def test_escrever_outro_texto_so_em_campo_de_texto_e_com_as_quebras(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.desc(mec, "D01").update(descricao="Linha um\nLinha dois")
        MatrizEtapaCC.objects.filter(pk=self.mec5.pk).update(passo=30)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "<legend>Intervalo mínimo</legend>")
        self.assertContains(r, "Escrever outro texto", count=1)
        self.assertContains(r, 'name="escolha-1" value="texto"')  # 0 é o passo, 1 a descrição
        self.assertNotContains(r, 'name="texto-0"')
        self.assertContains(r, 'name="texto-1"')
        self.assertContains(r, ">Linha um\nLinha dois</textarea>")

    def test_em_dia_com_a_base(self):
        self.copiar()
        r = self.client.get(self.url_rev)
        self.assertContains(r, "Esta etapa está em dia com a base")
        self.assertNotContains(r, "Concluir revisão")
        self.assertNotContains(r, 'name="visto"')

    def test_base_mudou_e_o_projeto_ja_tem_igual(self):
        mec = self.copiar()
        self.desc(self.mec5, "D02").update(descricao="Igual")
        self.desc(mec, "D02").update(descricao="Igual")
        r = self.client.get(self.url_rev)
        self.assertContains(r, "clique em Concluir revisão para fechar a pendência")
        self.assertContains(r, ">Concluir revisão</button>")
        self.assertContains(r, 'name="visto"')
        self.assertNotContains(r, "Precisa da sua decisão")
        self.assertRedirects(self.concluir(), self.url, fetch_redirect_response=False)  # fecha a pendência sem escolha nenhuma
        mec.refresh_from_db()
        self.assertFalse(pendente(mec))

    # --- Imagem ---

    def test_imagem_da_base_e_do_projeto(self):
        novo = default_storage.save("itens/novo.png", ContentFile(PNG))
        meu = default_storage.save("itens/meu.pdf", ContentFile(b"%PDF-1.4"))
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")  # cartão 0: texto
        self.tar(self.mec5, 100).update(arquivo=novo)  # cartão 1: arquivo
        self.tar(mec, 100).update(arquivo=meu)
        Tarefa.objects.create(descritor=self.desc(self.mec5, "D02").get(), inicio=400, fim=450, texto="Com imagem.", ordem=2, arquivo=novo)  # cartão 2
        r = self.client.get(self.url_rev)
        self.assertContains(r, "<legend>D01 · tarefa 100–150 · Imagem</legend>")
        self.assertContains(r, f'<img src="{self.arquivo(1, "base")}" alt="Imagem: Na base agora">')
        self.assertContains(r, f'<a href="{self.arquivo(1, "local")}">Baixar o PDF</a>')
        self.assertContains(r, "Sem imagem.")  # o "antes"
        self.assertContains(r, f'<img src="{self.arquivo(2, "base")}" alt="Imagem: Na base agora">')  # a tarefa inteira leva a imagem
        self.assertNotContains(r, "itens/novo.png")  # nenhum caminho do storage na página
        resp = self.client.get(self.arquivo(1, "base"))
        self.assertEqual((resp.status_code, resp["Content-Type"]), (200, "image/png"))
        self.assertEqual(b"".join(resp.streaming_content), PNG)
        resp = self.client.get(self.arquivo(1, "local"))
        self.assertEqual((resp.status_code, resp["Content-Type"]), (200, "application/pdf"))
        self.assertEqual(self.client.get(self.arquivo(2, "base")).status_code, 200)
        for i, lado in ((1, "antes"), (2, "local"), (0, "base"), (9, "base")):  # sem arquivo, sem lado, item de texto, índice
            self.assertEqual(self.client.get(self.arquivo(i, lado)).status_code, 404, (i, lado))
        self.assertEqual(self.client.get(self.url_rev + "arquivo/1/outro/").status_code, 404)

    def test_imagem_de_antes_apagada_so_avisa(self):
        velho = default_storage.save("itens/velho.png", ContentFile(PNG))
        novo = default_storage.save("itens/novo.png", ContentFile(PNG))
        self.tar(self.mec5, 100).update(arquivo=velho)
        mec = self.copiar()
        self.tar(self.mec5, 100).update(arquivo=novo)
        r = self.client.get(self.url_rev)
        self.assertContains(r, f'<img src="{self.arquivo(0, "antes")}" alt="Imagem: Como era quando o projeto copiou">')
        self.assertNotContains(r, "A imagem de antes não existe mais.")
        self.tar(mec, 100).update(arquivo=novo)
        default_storage.delete(velho)
        r = self.client.get(self.url_rev)  # base e projeto iguais: nada a decidir, mas a página abre
        self.assertEqual(r.status_code, 200)
        self.tar(mec, 100).update(arquivo=None)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "A imagem de antes não existe mais.")
        self.assertNotContains(r, self.arquivo(0, "antes"))
        self.assertEqual(self.client.get(self.arquivo(0, "antes")).status_code, 404)

    # --- Proteções da leitura ---

    def test_etapa_da_matriz_e_404_sem_travar_a_comunitaria(self):
        self.copiar()
        self.assertEqual(self.client.get(reverse("ui_revisao", args=[self.mec5.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("ui_revisao", args=[self.mec5.pk]), {}).status_code, 404)
        self.assertIsNone(bloqueio.quem_bloqueia(self.mec5))
        self.assertEqual(self.client.get(reverse("ui_revisao_arquivo", args=[self.mec5.pk, 0, "base"])).status_code, 404)

    def test_copia_solta_e_404(self):
        mec = self.copiar()
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(base=None)  # a base saiu (SET NULL)
        self.assertEqual(self.client.get(self.url_rev).status_code, 404)
        self.assertEqual(self.client.post(self.url_rev, {}).status_code, 404)
        self.assertIsNone(bloqueio.quem_bloqueia(mec))
        self.assertEqual(self.client.get(self.arquivo(0, "base")).status_code, 404)

    def test_impresso_so_le(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.client.force_login(self.imp)
        r = self.client.get(self.url_rev)
        self.assertContains(r, "Só leitura: seu perfil vê a revisão, mas não conclui.")
        self.assertContains(r, "<legend>D01 · Descrição</legend>")
        self.assertContains(r, "<fieldset disabled>")
        self.assertNotContains(r, "Concluir revisão</button>")
        self.assertNotContains(r, 'name="visto"')
        self.assertIsNone(bloqueio.quem_bloqueia(mec))

    def test_projeto_arquivado_so_le(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        gravar_cortes(self.projeto_go.parceiro_ano, [], self.usuario)  # sem corte, a cascata arquiva o projeto
        r = self.client.get(self.url_rev)
        self.assertContains(r, "Só leitura: o projeto desta etapa está arquivado.")
        self.assertContains(r, "<fieldset disabled>")
        self.assertNotContains(r, "Concluir revisão</button>")
        self.assertIsNone(bloqueio.quem_bloqueia(mec))

    def test_outra_pessoa_no_editor_da_copia(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(descricao="Da base")
        self.assertTrue(bloqueio.adquirir(mec, self.outro, "aba-do-outro"))  # o editor da cópia trava a mesma etapa
        r = self.client.get(self.url_rev)
        self.assertContains(r, "Somente leitura: outro está editando")
        self.assertContains(r, "<fieldset disabled>")
        self.assertNotContains(r, "Concluir revisão</button>")
        self.assertEqual(bloqueio.quem_bloqueia(mec).usuario, self.outro)

    # --- Gravação ---

    def test_conclui_volta_a_aba_e_some_a_pendencia(self):
        mec = self.conflito_em_d01()
        lacunas = lambda: [lc["tipo"] for lc in resolver(carregar(self.go["LP"].pk))["lacunas"]]  # noqa: E731
        self.assertIn("base", lacunas())
        r = self.concluir(e0="local", e1="base")
        self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.assertEqual(self.desc(mec, "D01").get().descricao, "Do projeto")
        self.assertEqual(self.desc(mec, "D02").get().descricao, "Descritor dois")
        mec.refresh_from_db()
        self.assertFalse(pendente(mec))
        self.assertNotIn("base", lacunas())
        h = mec.history.first()
        self.assertEqual((h.history_user, h.history_change_reason), (self.ped, "revisão da base: aplicou 1, manteve 1"))
        self.assertEqual(self.desc(mec, "D02").get().history.first().history_user, self.ped)
        self.assertIsNone(bloqueio.quem_bloqueia(mec))  # o 302 libera o bloqueio
        r = self.client.get(self.url)
        self.assertContains(r, "Revisão de 4EF LP concluída: 1 mudança(s) da base aplicada(s).")
        self.assertContains(self.client.get(self.url_rev), "Esta etapa está em dia com a base")

    def test_manter_tudo_devolve_o_validado(self):
        # GO sem corte no 5EF LP: a base só chega à revista pela etapa do projeto
        c = [100, 200, 250, 300]
        gravar_cortes(self.projeto_go.parceiro_ano, [(self.e9, self.lp, c), (self.e5, self.mt, c), (self.e4, self.lp, c)], self.usuario)
        mec = self.copiar()
        validar(self.go["LP"])
        self.desc(self.mec5, "D02").update(descricao="Descritor dois")
        self.assertFalse(esta_validada(self.go["LP"]))  # a pendência da base tira o "Validado"
        r = self.concluir(e0="local")
        self.assertRedirects(r, self.url, fetch_redirect_response=False)  # sem modal: nada estava validado
        self.assertEqual(self.desc(mec, "D02").get().descricao, "Descritor 2")
        self.assertTrue(esta_validada(self.go["LP"]))  # o conteúdo voltou a ser o validado (D-094)
        self.assertContains(self.client.get(self.url), "Revisão de 4EF LP concluída: nada mudou no projeto.")

    def test_descritor_novo_da_base_aparece_na_revista(self):
        self.copiar()
        d3 = Descritor.objects.create(matriz_etapa_cc=self.mec5, codigo="D03", descricao="Descritor novo", ordem=3)
        Tarefa.objects.create(descritor=d3, inicio=100, fim=150, texto="Tarefa nova.", ordem=1)
        dados = lambda: resolver(carregar(self.go["LP"].pk))["f1"]["dados"]["4ef"]  # noqa: E731
        self.assertNotIn("D03", dados())
        self.assertRedirects(self.concluir(e0="base"), self.url, fetch_redirect_response=False)
        self.assertEqual(dados()["D03"]["description"], "Descritor novo")

    def test_escolha_de_ordem_vale_para_todas_as_celulas(self):
        mec = self.copiar()
        self.desc(self.mec5, "D01").update(ordem=9)
        self.desc(self.mec5, "D02").update(ordem=8)
        ordens = lambda m: list(Descritor.objects.filter(matriz_etapa_cc=m).order_by("codigo").values_list("ordem", flat=True))  # noqa: E731
        antes = ordens(mec)
        # sem escolha, a célula que só a base mudou entra: "manter" tem de chegar às duas
        self.assertRedirects(self.concluir(e0="local"), self.url, fetch_redirect_response=False)
        self.assertEqual(ordens(mec), antes)
        self.assertEqual(mec.history.first().history_change_reason, "revisão da base: aplicou 0, manteve 2")

    def test_escrever_outro_texto_grava_com_as_quebras(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="texto", t0="Linha um\nLinha dois", t1="não vale: o cartão 1 ficou na base")
        self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.assertEqual(self.desc(mec, "D01").get().descricao, "Linha um\nLinha dois")
        self.assertEqual(self.desc(mec, "D02").get().descricao, "Descritor dois")  # sem escolha postada, entra o da base

    # --- Proteções da gravação ---

    def test_visto_velho_e_409_sem_gravar_e_sem_repintar(self):
        mec = self.conflito_em_d01()
        r = self.client.get(self.url_rev)
        form = {CAMPO_SESSAO: r.wsgi_request.bloqueio["sessao"], "visto": r.context["visto"], "escolha-0": "local", "escolha-1": "local"}
        passo = mec.passo
        MatrizEtapaCC.objects.filter(pk=self.mec5.pk).update(passo=passo + 5)  # a base mudou de novo: os índices andam
        r = self.client.post(self.url_rev, form)
        self.assertContains(r, "Não salvo: a base ou a etapa mudou depois que você abriu a revisão.", status_code=409)
        self.intacta(mec)
        self.assertEqual(mec.passo, passo)
        self.assertContains(r, "<legend>Intervalo mínimo</legend>", status_code=409)  # a lista de agora
        self.assertNotContains(r, 'value="local" checked', status_code=409)  # o índice 0 já é outra célula
        self.assertContains(r, f'<input type="hidden" name="visto" value="{revisao(mec)[1]}">', status_code=409)
        self.assertEqual(bloqueio.quem_bloqueia(mec).usuario, self.ped)  # segue na tela, com o bloqueio
        form["visto"] = revisao(mec)[1]
        self.assertEqual(self.client.post(self.url_rev, {**form, "escolha-2": "local"}).status_code, 302)

    def test_mudou_durante_a_gravacao_e_409_com_a_lista_do_banco(self):
        mec = self.conflito_em_d01()

        def mudou(m, *args):
            MatrizEtapaCC.objects.filter(pk=self.mec5.pk).update(passo=m.passo + 5)  # entre a leitura da view e a do serviço
            raise RevisaoMudou("mudou")

        with mock.patch("nucleo.urls.ui_revisao.concluir", side_effect=mudou):
            r = self.concluir(e0="local")
        self.assertContains(r, "Não salvo: a base ou a etapa mudou depois que você abriu a revisão.", status_code=409)
        self.assertContains(r, "<legend>Intervalo mínimo</legend>", status_code=409)
        self.assertNotContains(r, 'value="local" checked', status_code=409)
        self.assertContains(r, f'<input type="hidden" name="visto" value="{revisao(MatrizEtapaCC.objects.get(pk=mec.pk))[1]}">', status_code=409)

    def test_decisao_sem_escolha_nao_grava_e_mantem_as_outras(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e1="local")
        self.assertContains(r, "Não salvo: escolha D01 · descricao.")
        self.intacta(mec)
        self.assertContains(r, '<input type="radio" name="escolha-0" value="local" required>')
        self.assertContains(r, '<input type="radio" name="escolha-1" value="local" checked>')
        self.assertNotContains(r, 'name="escolha-1" value="base" checked')

    def test_escolha_malformada_nao_grava(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="xyz", e1="local")
        self.assertContains(r, "Não salvo: escolha inválida: &#x27;xyz&#x27;.")
        self.intacta(mec)
        self.assertContains(r, '<input type="radio" name="escolha-1" value="local" checked>')
        MatrizEtapaCC.objects.filter(pk=self.mec5.pk).update(passo=mec.passo + 5)  # cartão 0 passa a ser o intervalo
        r = self.concluir(e0="texto", t0="40", e1="local")
        self.assertContains(r, "Não salvo: passo não é campo de texto.")
        self.intacta(mec)

    def test_texto_sem_o_campo_nao_grava(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="texto", e1="local")
        self.assertContains(r, "Não salvo: faltou o texto de D01 · Descrição.")
        self.intacta(mec)
        self.assertContains(r, '<input type="radio" name="escolha-0" value="texto" checked>')
        self.assertContains(r, '<input type="radio" name="escolha-1" value="local" checked>')

    def test_texto_vazio_em_campo_obrigatorio_nao_grava(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="texto", t0=" \n ", e1="local")
        self.assertContains(r, "Não salvo: o texto de D01 · descricao não pode ficar vazio.")
        self.intacta(mec)
        self.assertContains(r, '<input type="radio" name="escolha-0" value="texto" checked>')

    def test_texto_com_nul_nao_grava_nem_quebra(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="texto", t0="a\x00b", e1="local")
        self.assertContains(r, "Não salvo: texto com caractere inválido em D01 · descricao.")
        self.intacta(mec)

    def test_texto_digitado_volta_no_campo_quando_nao_grava(self):
        mec = self.conflito_em_d01()
        r = self.concluir(e0="texto", t0="Meio a meio", e1="xyz")
        self.assertContains(r, "Não salvo: escolha inválida")
        self.intacta(mec)
        self.assertContains(r, ">Meio a meio</textarea>")

    def test_sem_bloqueio_nao_grava(self):
        mec = self.conflito_em_d01()
        visto = self.client.get(self.url_rev).context["visto"]
        form = {"visto": visto, "escolha-0": "base", "escolha-1": "base"}
        r = self.client.post(self.url_rev, {**form, CAMPO_SESSAO: "outra-aba"}, follow=True)
        self.assertContains(r, "Não salvo: você perdeu o bloqueio de edição")
        self.intacta(mec)
        self.assertEqual(self.client.post(self.url_rev, form).status_code, 302)  # sem a sessão do bloqueio
        self.intacta(mec)

    def test_outra_pessoa_no_editor_da_copia_nao_grava(self):
        mec = self.conflito_em_d01()
        self.assertTrue(bloqueio.adquirir(mec, self.outro, "aba-do-outro"))
        r = self.client.get(self.url_rev)
        form = {"visto": r.context["visto"], "escolha-0": "base", "escolha-1": "base", CAMPO_SESSAO: "aba-do-outro"}
        r = self.client.post(self.url_rev, form, follow=True)
        self.assertContains(r, "Não salvo: você perdeu o bloqueio de edição")
        self.intacta(mec)
        self.assertEqual(bloqueio.quem_bloqueia(mec).usuario, self.outro)

    def test_impresso_e_arquivado_403(self):
        mec = self.conflito_em_d01()
        r = self.client.get(self.url_rev)
        form = {CAMPO_SESSAO: r.wsgi_request.bloqueio["sessao"], "visto": r.context["visto"], "escolha-0": "base", "escolha-1": "base"}
        self.client.force_login(self.imp)
        self.assertEqual(self.client.post(self.url_rev, form).status_code, 403)
        self.intacta(mec)
        self.client.force_login(self.ped)
        gravar_cortes(self.projeto_go.parceiro_ano, [], self.usuario)  # sem corte, a cascata arquiva o projeto
        self.assertEqual(self.client.post(self.url_rev, form).status_code, 403)
        self.intacta(mec)

    def test_revista_validada_a_forca_abre_o_modal_e_so_grava_confirmada(self):
        """Com a pendência da base ninguém valida pela tela; se o "Validado" estiver lá, concluir passa
        pelo modal de impacto como toda gravação que o tira (D-202)."""
        mec = self.conflito_em_d01()
        validar(self.go["LP"])
        r = self.concluir(e0="texto", t0="Meio a meio", e1="local")
        self.assertContains(r, 'data-form="revisao"')  # o modal, ligado ao form da revisão
        self.assertContains(r, 'id="revisao"')
        self.assertContains(r, "Concluir revisão tira o “Validado” de 1 revista(s)")
        self.assertContains(r, f"<li>{self.go['LP']}</li>")
        self.intacta(mec)
        self.assertTrue(esta_validada(self.go["LP"]))
        # as escolhas voltam no form: confirmar no modal reenvia o que a pessoa marcou
        self.assertContains(r, '<input type="radio" name="escolha-0" value="texto" checked>')
        self.assertContains(r, ">Meio a meio</textarea>")
        self.assertContains(r, '<input type="radio" name="escolha-1" value="local" checked>')
        r = self.concluir(e0="texto", t0="Meio a meio", e1="local", confirmar_impacto="on")
        self.assertRedirects(r, self.url, fetch_redirect_response=False)
        self.assertEqual(self.desc(mec, "D01").get().descricao, "Meio a meio")
        self.assertFalse(esta_validada(self.go["LP"]))
        self.assertContains(self.client.get(self.url), "1 revista(s) perderam o “Validado”")

    def test_simulacao_do_modal_nao_apaga_arquivo(self):
        meu = default_storage.save("itens/meu.png", ContentFile(PNG))
        novo = default_storage.save("itens/novo.png", ContentFile(PNG))
        mec = self.copiar()
        self.tar(mec, 100).update(arquivo=meu)
        self.tar(self.mec5, 100).update(arquivo=novo)
        validar(self.go["LP"])
        with self.captureOnCommitCallbacks(execute=True):
            r = self.concluir(e0="base")
        self.assertContains(r, 'data-form="revisao"')  # só simulou
        self.assertEqual(self.tar(mec, 100).get().arquivo, meu)
        self.assertTrue(default_storage.exists(meu))
        with self.captureOnCommitCallbacks(execute=True):
            r = self.concluir(e0="base", confirmar_impacto="on")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.tar(mec, 100).get().arquivo, novo)
        self.assertFalse(default_storage.exists(meu))  # gravou de verdade: o arquivo que ficou sem dono sai
