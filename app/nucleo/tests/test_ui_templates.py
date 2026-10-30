"""Templates B (T12-T14, /ui/templates/): critérios de aceite de docs/telas/fichas/templates.md pelo client."""

from django.test import Client
from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Ano, Bloqueio, FotoRevista, RevistaFasciculo, RevistaSecao, TemplateVersao
from nucleo.models.revista import Motivo
from nucleo.servicos.resolver import versao_atual
from nucleo.tests.test_admin_templates import F2_NOVO, Base
from nucleo.tests.test_resolver import usuario


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
        self.assertContains(r, 'href="/ui/variaveis/2026/">Variáveis')
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
            self.assertRedirects(r, f"{reverse('admin:login')}?next={url}", fetch_redirect_response=False)
        self.assertEqual(Client().post(reverse("ui_templates_previa", args=[self.tpl.pk]), {"texto": "x"}).status_code, 403)


class EditarTest(UiBase):
    def test_get_com_permissao_editor_e_previa(self):
        r = self.ped.get(self.editar)
        self.assertContains(r, 'name="texto"')
        self.assertContains(r, "Inserir variável")
        self.assertContains(r, 'hx-trigger="input changed delay:400ms"')
        self.assertContains(r, "nucleo/bloqueio.js")
        self.assertContains(r, '<span class="variavel-vazia">{{adjetivo_patrio_plural_masculino}}</span>')
        self.assertContains(r, "Texto válido para o fascículo.")

    def test_previa_htmx_mostra_erros(self):
        url = reverse("ui_templates_previa", args=[self.tpl.pk])
        r = self.ped.post(url, {"texto": "## passo1\nOi\n\nPara {{ano}}.\n"}, HTTP_HX_REQUEST="true")
        self.assertContains(r, '<span class="variavel-vazia">{{ano}}</span>')
        self.assertContains(r, "Seções obrigatórias faltando: abertura.")
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
        go = self.go["LP"]
        go.svg_f2, go.svg_sha256, go.svg_ids = "f2/go.svg", "a" * 64, ["passo1", "btn-action-p2"]
        go.save()
        FotoRevista.objects.create(revista=self.pe["LP"], motivo=Motivo.IMPRESSO, conteudo={}, hash="b" * 64, criada_por=self.usuario)
        sessao = self.sessao()
        r = self.post(sessao, F2_NOVO)
        self.assertTemplateUsed(r, "ui/templates/impacto.html")
        self.assertContains(r, "Confirmar e criar versão 2")
        self.assertContains(r, "SVG incompleto: passo2")
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
        for troca in ({"_impacto": "adulterada"}, {"texto": F2_NOVO + "\n## passo3\nT\n\nM.\n"}):
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
        r = self.post(self.sessao(), F2_NOVO + "\n## passo3\nT\n\nOi {{x}}.\n")
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
