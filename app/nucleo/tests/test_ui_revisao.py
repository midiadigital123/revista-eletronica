"""Tela "Revisar mudanças da base" (D-292): /ui/revisao/<pk>/, a revisão da etapa do projeto contra a base."""

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Descritor, MatrizEtapaCC, Tarefa
from nucleo.servicos import bloqueio
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.etapa_projeto import criar, revisao
from nucleo.tests.test_ui_projeto_abas import EtapaNaoCanonica

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


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
        self.assertContains(r, f'<img src="{self.arquivo(1, "base")}" alt="">')
        self.assertContains(r, f'<a href="{self.arquivo(1, "local")}">Baixar o PDF</a>')
        self.assertContains(r, "Sem imagem.")  # o "antes"
        self.assertContains(r, f'<img src="{self.arquivo(2, "base")}" alt="">')  # a tarefa inteira leva a imagem
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
        self.assertContains(r, f'<img src="{self.arquivo(0, "antes")}" alt="">')
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
        self.assertIsNone(bloqueio.quem_bloqueia(self.mec5))
        self.assertEqual(self.client.get(reverse("ui_revisao_arquivo", args=[self.mec5.pk, 0, "base"])).status_code, 404)

    def test_copia_solta_e_404(self):
        mec = self.copiar()
        MatrizEtapaCC.objects.filter(pk=mec.pk).update(base=None)  # a base saiu (SET NULL)
        self.assertEqual(self.client.get(self.url_rev).status_code, 404)
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
