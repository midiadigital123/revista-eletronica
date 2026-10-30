"""S11c: admin de Projeto e Revista, aba Variáveis e lotes (matriz, template)."""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.admin.lote import escrever_travado
from nucleo.models import (
    Ano,
    Bloqueio,
    Matriz,
    Parceiro,
    ParceiroAno,
    Projeto,
    ProjetoCor,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.servicos import bloqueio
from nucleo.tests.test_preview import SVG
from nucleo.tests.test_resolver import MediaTemporaria, Mundo, usuario

SVG_SEM_BOTAO = SVG.replace(b'id="btn-action-p2"', b'id="outro"')  # F2_LP pede passo1 e btn-action-p2


def mensagens(resposta):
    return [str(m) for m in resposta.context["messages"]]


class Base(MediaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        cls.projeto_go = Projeto.objects.get(parceiro_ano__parceiro__nome="GO", arquivado_em__isnull=True)
        cls.projeto_pe = Projeto.objects.get(parceiro_ano__parceiro__nome="PE", arquivado_em__isnull=True)
        User = get_user_model()
        cls.outro = User.objects.create(username="outro")
        cls.ped = usuario("ped", "Pedagógica")
        cls.imp = usuario("imp", "Impresso")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.ped)

    def travar(self, projeto):
        """Outro usuário com o projeto aberto (bloqueio válido de outra sessão)."""
        self.assertTrue(bloqueio.adquirir(projeto, self.outro, "aba-do-outro"))


class LoteMatrizTest(Base):
    URL = reverse("admin:nucleo_projeto_escolher_matriz")

    def test_pula_projeto_travado_e_lista(self):
        nova = Matriz.objects.create(ano=self.ano, nome="Nova")
        self.travar(self.projeto_go)
        pas = ParceiroAno.objects.filter(ano=self.ano)
        r = self.client.post(self.URL, {"alvos": [pa.pk for pa in pas], "matriz": nova.pk}, follow=True)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="PE").matriz, nova)
        self.assertEqual(ParceiroAno.objects.get(parceiro__nome="GO").matriz, self.matriz)
        msgs = mensagens(r)
        self.assertIn("Matriz Nova escolhida para 1 parceiro(s).", msgs)
        self.assertIn("Pulados: GO (projeto em edição por outro).", msgs)

    def test_matriz_de_outro_ano_nao_e_oferecida(self):
        ano25 = Ano.objects.create(ano=2025)
        velha = Matriz.objects.create(ano=ano25, nome="Velha")
        r = self.client.get(self.URL + "?ano=2026")
        self.assertNotIn(velha, r.context["form"].fields["matriz"].queryset)
        pa = ParceiroAno.objects.get(parceiro__nome="PE")
        r = self.client.post(self.URL + "?ano=2026", {"alvos": [pa.pk], "matriz": velha.pk})
        self.assertEqual(r.status_code, 200)  # form inválido
        self.assertEqual(ParceiroAno.objects.get(pk=pa.pk).matriz, self.matriz)


class LoteTemplateTest(Base):
    def url(self, componente):
        return reverse("admin:nucleo_revista_escolher_template") + f"?ano=2026&componente={componente.pk}"

    def novo_template(self, componente, fasciculo, nome="Outro"):
        t = Template.objects.create(ano=self.ano, componente=componente, fasciculo=fasciculo, nome=nome)
        TemplateVersao.objects.create(template=t, numero=1, texto="x")
        return t

    def test_pula_travado_e_com_copias(self):
        f1 = self.novo_template(self.lp, "F1")
        self.travar(self.projeto_pe)
        rf_go = RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F1")
        versao = TemplateVersao.objects.get(template=rf_go.template, numero=1)
        RevistaSecao.objects.create(
            revista_fasciculo=rf_go, template=rf_go.template, secao="introducao", texto="editado",
            template_versao=versao,
        )  # fmt: skip
        r = self.client.post(
            self.url(self.lp), {"alvos": [self.go["LP"].pk, self.pe["LP"].pk], "template_f1": f1.pk}, follow=True
        )
        self.assertEqual(RevistaFasciculo.objects.get(pk=rf_go.pk).template, self.templates["LP", "F1"])
        self.assertEqual(
            RevistaFasciculo.objects.get(revista=self.pe["LP"], fasciculo="F1").template, self.templates["LP", "F1"]
        )
        aviso = next(m for m in mensagens(r) if m.startswith("Pulados"))
        self.assertIn("Projeto GO · LP (F1 tem cópias de seção; troque o template pela revista)", aviso)
        self.assertIn("Projeto PE · LP (projeto em edição por outro)", aviso)

    def test_troca_sem_copias(self):
        f2 = self.novo_template(self.lp, "F2")
        self.client.post(self.url(self.lp), {"alvos": [self.go["LP"].pk], "template_f2": f2.pk})
        self.assertEqual(RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F2").template, f2)
        self.assertEqual(  # F1 não escolhido: não muda
            RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F1").template, self.templates["LP", "F1"]
        )

    def test_template_de_outro_componente(self):
        mt_f1 = self.templates["MT", "F1"]
        form = self.client.get(self.url(self.lp)).context["form"]
        self.assertNotIn(mt_f1, form.fields["template_f1"].queryset)
        self.assertNotIn(self.go["MT"], form.fields["alvos"].queryset)
        self.client.post(self.url(self.lp), {"alvos": [self.go["LP"].pk], "template_f1": mt_f1.pk})
        rf = RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F1")
        self.assertEqual(rf.template, self.templates["LP", "F1"])
        # Forçado por fora do admin, o banco recusa (FK composta template × ano × componente × fascículo).
        with self.assertRaises(IntegrityError), transaction.atomic():
            RevistaFasciculo.objects.filter(pk=rf.pk).update(template=mt_f1)


class VariaveisTest(Base):
    URL = reverse("admin:nucleo_projeto_variaveis")

    def criar_2025(self, **valores):
        ano25 = Ano.objects.create(ano=2025)
        pa = ParceiroAno.objects.create(parceiro=self.projeto_go.parceiro_ano.parceiro, ano=ano25)
        return Projeto.objects.create(parceiro_ano=pa, ano=ano25, nome="GO 2025", **valores)

    def test_copiar_so_preenche_vazias(self):
        Projeto.objects.filter(pk=self.projeto_go.pk).update(adjetivo_patrio_singular_feminino="   ")  # só espaço = vazio
        self.criar_2025(
            adjetivo_patrio_singular_masculino="goiano", adjetivo_patrio_singular_feminino="goiana", adjetivo_patrio_plural_masculino="velho",
            arquivado_em="2025-12-31T00:00:00Z",  # arquivado também serve
        )  # fmt: skip
        r = self.client.post(self.URL, {"copiar": self.projeto_go.pk}, follow=True)
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual(p.adjetivo_patrio_singular_masculino, "goiano")
        self.assertEqual(p.adjetivo_patrio_singular_feminino, "goiana")
        self.assertEqual(p.adjetivo_patrio_plural_masculino, "goianos")  # já tinha valor: não sobrescreve
        self.assertEqual(p.adjetivo_patrio_plural_feminino, "")  # vazio também em 2025
        self.assertIn("copiado de 2025", mensagens(r)[0])

    def test_sem_ano_anterior_nada_muda(self):
        antes = Projeto.objects.filter(pk=self.projeto_pe.pk).values().get()
        r = self.client.post(self.URL, {"copiar": self.projeto_pe.pk}, follow=True)
        self.assertIn("não há projeto do parceiro em 2025", mensagens(r)[0])
        self.assertEqual(Projeto.objects.filter(pk=self.projeto_pe.pk).values().get(), antes)

    def test_pdnn_mostra_o_nome_do_ano_e_a_escala(self):  # D-175
        r = self.client.get(self.URL)
        self.assertContains(r, 'placeholder="padrão do ano: Padrão 02"', count=2)  # GO e PE
        self.assertContains(r, "escala do F1 (nome do padrão)", count=5)
        r = self.client.get(reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk]))
        self.assertContains(r, 'placeholder="padrão do ano: Padrão 05"')

    def test_planilha_grava_e_pula_travado(self):
        r = self.client.get(self.URL)
        self.assertContains(r, "LP F2 Padrão")  # adjetivo_patrio_plural_masculino aparece no F2 do LP
        dados = {
            "form-TOTAL_FORMS": 2, "form-INITIAL_FORMS": 2, "form-MIN_NUM_FORMS": 0, "form-MAX_NUM_FORMS": 1000,
        }  # fmt: skip
        for i, p in enumerate(r.context["formset"].queryset):
            dados[f"form-{i}-id"] = p.pk
            for nome in ("adjetivo_patrio_singular_masculino", "adjetivo_patrio_singular_feminino", "adjetivo_patrio_plural_masculino", "adjetivo_patrio_plural_feminino"):
                dados[f"form-{i}-{nome}"] = dados[f"initial-form-{i}-{nome}"] = getattr(p, nome)
            dados[f"form-{i}-adjetivo_patrio_singular_masculino"] = f"novo {p.nome}"
        self.travar(self.projeto_pe)
        r = self.client.post(self.URL, dados, follow=True)
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).adjetivo_patrio_singular_masculino, "novo Projeto GO")
        self.assertEqual(Projeto.objects.get(pk=self.projeto_pe.pk).adjetivo_patrio_singular_masculino, "")
        self.assertIn("Pulados: Projeto PE (projeto em edição por outro).", mensagens(r))


class RevistaUploadTest(Base):
    def post_revista(self, revista, **extra):
        url = reverse("admin:nucleo_revista_change", args=[revista.pk])
        sessao = self.client.get(url).context["bloqueio"]["sessao"]
        rfs = RevistaFasciculo.objects.filter(revista=revista).order_by("pk")
        dados = {
            CAMPO_SESSAO: sessao, "revistafasciculo_set-TOTAL_FORMS": len(rfs),
            "revistafasciculo_set-INITIAL_FORMS": len(rfs), "revistafasciculo_set-MIN_NUM_FORMS": 0,
            "revistafasciculo_set-MAX_NUM_FORMS": 1000,
        }  # fmt: skip
        for i, rf in enumerate(rfs):
            dados[f"revistafasciculo_set-{i}-id"] = rf.pk
            dados[f"revistafasciculo_set-{i}-revista"] = revista.pk
            dados[f"revistafasciculo_set-{i}-template"] = rf.template_id
        return self.client.post(url, {**dados, **extra}, follow=True)

    def test_svg_sem_um_id_grava_e_avisa(self):
        rev = self.go["LP"]
        r = self.post_revista(rev, arquivo_svg=SimpleUploadedFile("f2.svg", SVG_SEM_BOTAO))
        aviso = next(m for m in mensagens(r) if "Ids que faltam" in m)
        self.assertIn("<strong>btn-action-p2</strong>", aviso)
        self.assertIn("Esperados: passo1, btn-action-p2", aviso)
        gabarito = reverse("admin:nucleo_revista_gabarito_ids", args=[rev.pk])
        self.assertIn(f'href="{gabarito}">Baixar gabarito de ids', aviso)
        self.assertEqual(Revista.objects.get(pk=rev.pk).svg_ids, ["fundo", "passo1", "passo2", "outro"])
        # O aviso continua no formulário até o SVG ser trocado.
        r = self.client.get(reverse("admin:nucleo_revista_change", args=[rev.pk]))
        self.assertContains(r, "Baixar gabarito de ids")
        csv = self.client.get(gabarito)
        self.assertEqual(csv.content.decode().splitlines(), ["id_no_svg,secao_do_template", "passo1,passo1", "btn-action-p2,dlg-p2"])

    def test_svg_e_capa_validos(self):
        from nucleo.management.commands.criar_demo import png

        rev = self.go["LP"]
        r = self.post_revista(
            rev, arquivo_svg=SimpleUploadedFile("f2.svg", SVG), arquivo_capa=SimpleUploadedFile("c.png", png(2, 2, (0, 0, 0)))
        )
        self.assertFalse([m for m in mensagens(r) if "Ids que faltam" in m])
        rev = Revista.objects.get(pk=rev.pk)
        self.assertTrue(rev.svg_f2 and rev.capa)

    def test_arquivo_invalido_mostra_erro_e_nao_grava(self):
        rev = self.go["LP"]
        r = self.post_revista(
            rev, arquivo_svg=SimpleUploadedFile("f2.svg", b"<html/>"), arquivo_capa=SimpleUploadedFile("c.png", b"GIF89a")
        )
        self.assertContains(r, "O arquivo não é um SVG.")
        self.assertContains(r, "Capa precisa ser PNG, JPG ou WebP.")
        rev = Revista.objects.get(pk=rev.pk)
        self.assertIsNone(rev.svg_f2)
        self.assertIsNone(rev.capa)

    def test_trocar_template_com_copias_recusado_no_form(self):
        rev = self.go["LP"]
        rf = RevistaFasciculo.objects.get(revista=rev, fasciculo="F1")
        RevistaSecao.objects.create(
            revista_fasciculo=rf, template=rf.template, secao="introducao", texto="editado",
            template_versao=TemplateVersao.objects.get(template=rf.template),
        )  # fmt: skip
        outro = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Outro")
        i = list(RevistaFasciculo.objects.filter(revista=rev).order_by("pk")).index(rf)
        r = self.post_revista(rev, **{f"revistafasciculo_set-{i}-template": outro.pk})
        self.assertContains(r, "Este fascículo tem textos editados")
        self.assertEqual(RevistaFasciculo.objects.get(pk=rf.pk).template, self.templates["LP", "F1"])


class ProjetoAdminTest(Base):
    def test_nome_e_cor(self):
        url = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        sessao = self.client.get(url).context["bloqueio"]["sessao"]
        dados = {
            CAMPO_SESSAO: sessao, "nome": "Avalia GO",
            **{n: "" for n in ("adjetivo_patrio_singular_masculino", "adjetivo_patrio_singular_feminino", "adjetivo_patrio_plural_feminino")},
            "adjetivo_patrio_plural_masculino": "goianos",
            "projetopasso_set-TOTAL_FORMS": 1, "projetopasso_set-INITIAL_FORMS": 0,
            "projetopasso_set-0-etapa": self.e5.pk, "projetopasso_set-0-componente": self.lp.pk,
            "projetopasso_set-0-passo": "",
            "projetocor_set-TOTAL_FORMS": 1, "projetocor_set-INITIAL_FORMS": 0,
            "projetocor_set-0-padrao": 2, "projetocor_set-0-cor": "#GG0000",
        }  # fmt: skip
        r = self.client.post(url, dados)
        self.assertContains(r, "Use o formato #RRGGBB.")
        dados["projetocor_set-0-cor"] = "#00aa00"
        self.assertEqual(self.client.post(url, dados).status_code, 302)
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual(p.nome, "Avalia GO")
        self.assertEqual(ProjetoCor.objects.get(projeto=p).cor, "#00aa00")
        passo = p.projetopasso_set.get()
        self.assertEqual((passo.ano_id, passo.passo), (self.ano.pk, None))  # nulo = sem linhas vazias

    def test_arquivado_so_leitura(self):
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em="2026-01-01T00:00:00Z")
        url = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"nome": "x"}).status_code, 403)
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))  # só ver não trava


class PermissoesTest(Base):
    def test_impresso_so_ve(self):
        self.client.force_login(self.imp)
        variaveis = reverse("admin:nucleo_projeto_variaveis")
        r = self.client.get(variaveis)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "disabled")
        self.assertNotContains(r, "Copiar valores do ano anterior</button>")
        self.assertEqual(self.client.post(variaveis, {"copiar": self.projeto_go.pk}).status_code, 403)
        for nome in ("admin:nucleo_projeto_escolher_matriz", "admin:nucleo_revista_escolher_template"):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 403, nome)
        projeto = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        self.assertEqual(self.client.get(projeto).status_code, 200)
        self.assertEqual(self.client.post(projeto, {"nome": "x"}).status_code, 403)
        revista = reverse("admin:nucleo_revista_change", args=[self.go["LP"].pk])
        self.assertNotContains(self.client.get(revista), 'name="arquivo_svg"')
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))  # só ver não trava
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).nome, "Projeto GO")

    def test_pedagogica_edita_sem_excluir(self):
        for nome in ("admin:nucleo_projeto_escolher_matriz", "admin:nucleo_revista_escolher_template",
                     "admin:nucleo_projeto_variaveis", "admin:nucleo_projeto_changelist"):  # fmt: skip
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)
        r = self.client.get(reverse("admin:nucleo_revista_change", args=[self.go["LP"].pk]))
        self.assertContains(r, 'name="arquivo_svg"')
        apagar = reverse("admin:nucleo_projeto_delete", args=[self.projeto_go.pk])
        self.assertEqual(self.client.get(apagar).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:nucleo_projeto_add")).status_code, 403)

    def test_sem_login_vai_para_o_login(self):
        self.client.logout()
        r = self.client.get(reverse("admin:nucleo_projeto_variaveis"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])


ARQUIVADO = "2026-01-01T00:00:00Z"
VARS = ("adjetivo_patrio_singular_masculino", "adjetivo_patrio_singular_feminino", "adjetivo_patrio_plural_masculino", "adjetivo_patrio_plural_feminino")


def planilha(resposta):
    """POST da planilha com os valores da carga (como o navegador mandaria sem mexer)."""
    projetos = list(resposta.context["formset"].queryset)
    dados = {
        "form-TOTAL_FORMS": len(projetos), "form-INITIAL_FORMS": len(projetos),
        "form-MIN_NUM_FORMS": 0, "form-MAX_NUM_FORMS": 1000,
    }  # fmt: skip
    for i, p in enumerate(projetos):
        dados[f"form-{i}-id"] = p.pk
        for nome in VARS:
            dados[f"form-{i}-{nome}"] = dados[f"initial-form-{i}-{nome}"] = getattr(p, nome)
    return dados


class PlanilhaConcorrenteTest(Base):
    URL = reverse("admin:nucleo_projeto_variaveis")

    def test_preserva_coluna_alterada_por_outro_entre_carga_e_post(self):
        dados = planilha(self.client.get(self.URL))
        dados["form-0-adjetivo_patrio_singular_masculino"] = "goiano"  # GO é a 1ª linha
        Projeto.objects.filter(pk=self.projeto_go.pk).update(adjetivo_patrio_singular_feminino="goiana")  # outra pessoa
        self.client.post(self.URL, dados)
        p = Projeto.objects.get(pk=self.projeto_go.pk)
        self.assertEqual((p.adjetivo_patrio_singular_masculino, p.adjetivo_patrio_singular_feminino), ("goiano", "goiana"))

    def test_mais_de_200_caracteres_e_erro_de_form(self):
        dados = planilha(self.client.get(self.URL))
        dados["form-0-adjetivo_patrio_singular_masculino"] = "x" * 201
        r = self.client.post(self.URL, dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "no máximo 200 caracteres")
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).adjetivo_patrio_singular_masculino, "")


class ArquivadosTest(Base):
    def test_revista_arquivada_so_leitura(self):
        rev = self.go["LP"]
        Revista.objects.filter(pk=rev.pk).update(arquivada_em=ARQUIVADO)
        url = reverse("admin:nucleo_revista_change", args=[rev.pk])
        r = self.client.get(url)
        self.assertNotContains(r, 'name="arquivo_svg"')
        self.assertNotContains(r, 'name="revistafasciculo_set-0-template"')
        self.assertFalse(bloqueio.quem_bloqueia(self.projeto_go))  # só ver não trava
        self.assertEqual(self.client.post(url, {"arquivo_svg": SimpleUploadedFile("f2.svg", SVG)}).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=rev.pk).svg_f2)
        lote = reverse("admin:nucleo_revista_escolher_template") + f"?ano=2026&componente={self.lp.pk}"
        self.assertNotIn(rev, self.client.get(lote).context["form"].fields["alvos"].queryset)

    def test_projeto_arquivado_inlines_so_leitura(self):
        ProjetoCor.objects.create(projeto=self.projeto_go, padrao=1, cor="#000000")
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em=ARQUIVADO)
        url = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        r = self.client.get(url)
        self.assertNotContains(r, 'name="projetocor_set-0-cor"')
        self.assertNotContains(r, 'name="nome"')
        self.assertEqual(self.client.post(url, {"nome": "x"}).status_code, 403)
        planilha_ = self.client.get(reverse("admin:nucleo_projeto_variaveis"))
        self.assertNotIn(self.projeto_go, planilha_.context["formset"].queryset)

    def test_escrever_travado_pula_arquivado(self):
        Projeto.objects.filter(pk=self.projeto_go.pk).update(arquivado_em=ARQUIVADO)
        chamou = []
        self.assertEqual(escrever_travado(self.projeto_go, self.ped, lambda: chamou.append(1)), "projeto arquivado")
        self.assertEqual(chamou, [])
        self.assertFalse(Bloqueio.objects.exists())


class RevistaPermissoesTest(Base):
    def test_upload_com_bloqueio_de_outro_nao_grava(self):
        rev = self.go["LP"]
        self.travar(self.projeto_go)
        url = reverse("admin:nucleo_revista_change", args=[rev.pk])
        r = self.client.get(url)
        self.assertNotIn("bloqueio", r.context)  # só leitura
        self.assertNotContains(r, 'name="arquivo_svg"')
        r = self.client.post(url, {CAMPO_SESSAO: "chute", "arquivo_svg": SimpleUploadedFile("f2.svg", SVG)}, follow=True)
        self.assertIn("Não salvo: você perdeu o bloqueio de edição.", mensagens(r))
        self.assertIsNone(Revista.objects.get(pk=rev.pk).svg_f2)

    def test_impresso_post_403(self):
        self.client.force_login(self.imp)
        url = reverse("admin:nucleo_revista_change", args=[self.go["LP"].pk])
        self.assertEqual(self.client.post(url, {"arquivo_svg": SimpleUploadedFile("f2.svg", SVG)}).status_code, 403)
        self.assertIsNone(Revista.objects.get(pk=self.go["LP"].pk).svg_f2)

    def test_gabarito(self):
        self.assertEqual(self.client.get(reverse("admin:nucleo_revista_gabarito_ids", args=[999999])).status_code, 404)
        url = reverse("admin:nucleo_revista_gabarito_ids", args=[self.go["LP"].pk])
        RevistaFasciculo.objects.filter(revista=self.go["LP"], fasciculo="F2").update(template=None)
        self.assertEqual(self.client.get(url).content.decode().splitlines(), ["id_no_svg,secao_do_template"])
        self.client.force_login(get_user_model().objects.create(username="sem", is_staff=True))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_nome_com_mais_de_200_caracteres(self):
        url = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        sessao = self.client.get(url).context["bloqueio"]["sessao"]
        dados = {
            CAMPO_SESSAO: sessao, "nome": "x" * 201,
            "projetopasso_set-TOTAL_FORMS": 0, "projetopasso_set-INITIAL_FORMS": 0,
            "projetocor_set-TOTAL_FORMS": 0, "projetocor_set-INITIAL_FORMS": 0,
        }  # fmt: skip
        r = self.client.post(url, dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "no máximo 200 caracteres")
        self.assertContains(r, 'maxlength="200"')

    def test_pedagogica_exclui_cor_impresso_nao(self):
        cor = ProjetoCor.objects.create(projeto=self.projeto_go, padrao=1, cor="#000000")
        url = reverse("admin:nucleo_projeto_change", args=[self.projeto_go.pk])
        r = self.client.get(url)
        self.assertContains(r, 'name="projetocor_set-0-DELETE"')
        dados = {
            CAMPO_SESSAO: r.context["bloqueio"]["sessao"], "nome": "Projeto GO", "adjetivo_patrio_plural_masculino": "goianos",
            "projetopasso_set-TOTAL_FORMS": 0, "projetopasso_set-INITIAL_FORMS": 0,
            "projetocor_set-TOTAL_FORMS": 1, "projetocor_set-INITIAL_FORMS": 1,
            "projetocor_set-0-id": cor.pk, "projetocor_set-0-projeto": self.projeto_go.pk,
            "projetocor_set-0-padrao": 1, "projetocor_set-0-cor": "#000000", "projetocor_set-0-DELETE": "on",
        }  # fmt: skip
        self.assertEqual(self.client.post(url, dados).status_code, 302)
        self.assertFalse(ProjetoCor.objects.filter(pk=cor.pk).exists())
        self.client.force_login(self.imp)
        ProjetoCor.objects.create(projeto=self.projeto_go, padrao=1, cor="#000000")
        self.assertNotContains(self.client.get(url), "projetocor_set-0-DELETE")


class CsrfTest(Base):
    def test_views_novas_exigem_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.ped)
        for url in (
            reverse("admin:nucleo_projeto_variaveis"),
            reverse("admin:nucleo_projeto_escolher_matriz"),
            reverse("admin:nucleo_revista_escolher_template"),
        ):
            self.assertEqual(cliente.post(url, {"copiar": self.projeto_go.pk}).status_code, 403, url)
        self.assertEqual(Projeto.objects.get(pk=self.projeto_go.pk).adjetivo_patrio_singular_masculino, "")


class LoteConcorrenteTest(TransactionTestCase):
    """Bloqueio entre conexões com transações efetivadas (invariante 6)."""

    def setUp(self):
        ano = Ano.objects.create(ano=2026)
        self.matriz = Matriz.objects.create(ano=ano, nome="M")
        self.pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=ano)
        self.projeto = Projeto.objects.create(parceiro_ano=self.pa, ano=ano, nome="P")
        User = get_user_model()
        self.editor = User.objects.create_superuser("editor", password="x")
        self.lote = User.objects.create_superuser("lote", password="x")

    def test_lote_pula_projeto_aberto_pelo_editor(self):
        editor = Client()
        editor.force_login(self.editor)
        r = editor.get(reverse("admin:nucleo_projeto_change", args=[self.projeto.pk]))
        self.assertIn("bloqueio", r.context)  # o editor pegou o bloqueio (efetivado)
        self.client.force_login(self.lote)
        r = self.client.post(
            reverse("admin:nucleo_projeto_escolher_matriz"), {"alvos": [self.pa.pk], "matriz": self.matriz.pk}, follow=True
        )
        self.assertIn("Pulados: GO (projeto em edição por editor).", mensagens(r))
        self.assertIsNone(ParceiroAno.objects.get(pk=self.pa.pk).matriz)

    def test_escrever_travado_libera_no_fim_e_no_rollback(self):
        def gravar():
            Projeto.objects.filter(pk=self.projeto.pk).update(nome="novo")

        self.assertIsNone(escrever_travado(self.projeto, self.lote, gravar))
        self.assertFalse(Bloqueio.objects.exists())

        def falhar():
            Projeto.objects.filter(pk=self.projeto.pk).update(nome="perdido")
            raise RuntimeError("falhou")

        with self.assertRaises(RuntimeError):
            escrever_travado(self.projeto, self.lote, falhar)
        self.assertFalse(Bloqueio.objects.exists())
        self.assertEqual(Projeto.objects.get(pk=self.projeto.pk).nome, "novo")
