"""Validar revistas fora do admin (/ui/validar/<ano>/, T24): critérios de aceite de docs/telas/fichas/validar.md."""

import re

from django.urls import reverse

from nucleo.models import Revista
from nucleo.models.revista import Motivo
from nucleo.servicos.foto import fotografar
from nucleo.servicos.resolver import carregar
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_painel import SVG_B, completar, trocar_svg
from nucleo.tests.test_resolver import usuario

URL = reverse("ui_validar", args=[2026])


class ValidarUiTest(Base):
    def setUp(self):
        super().setUp()
        self.lp, self.mt = self.go["LP"], self.go["MT"]
        completar(self.lp)
        completar(self.mt)

    def abrir(self, *revistas, **extra):
        r = self.client.get(URL, {"revista": [x.pk for x in revistas]}, **extra)
        self.assertEqual(r.status_code, 200)
        return r

    def pares(self, resposta):
        return re.findall(r'name="par" value="([^"]+)"', resposta.content.decode())

    def enviar(self, *revistas, pares=None, **dados):
        aberta = self.abrir(*revistas)
        dados = {"par": self.pares(aberta) if pares is None else pares, "revista": [x.pk for x in revistas], **dados}
        return self.client.post(URL, dados, follow=True)

    def validadas(self):
        return set(Revista.objects.filter(hash_validado__isnull=False).values_list("pk", flat=True))

    def test_get_com_permissao(self):
        r = self.abrir(self.lp, self.mt)
        self.assertTemplateUsed(r, "ui/base.html")
        self.assertContains(r, "Validar revistas")
        self.assertContains(r, 'class="card validar-cartao', count=2)
        self.assertContains(r, "Pronta para validar", count=2)
        self.assertEqual(len(re.findall(r'name="par" value="[^"]+" checked', r.content.decode())), 2)  # prontas pré-marcadas
        self.assertContains(r, "Primeira impressão: não há versão impressa para comparar.", count=2)
        self.assertContains(r, "Validar marcadas")
        self.assertContains(r, "ui/telas/validar.css")
        self.assertContains(r, reverse("painel", args=[2026]))  # sem Painel B, volta ao do admin

    def test_pendencia_desabilita_e_aponta_onde_resolver(self):
        pe = self.pe["LP"]  # sem SVG nem capa
        r = self.abrir(pe)
        self.assertContains(r, "pendência(s)")
        self.assertContains(r, "Falta o SVG do F2.")
        self.assertContains(r, reverse("admin:nucleo_revista_change", args=[pe.pk]))
        self.assertRegex(r.content.decode(), r'name="par" value="[^"]+" disabled')
        self.assertContains(r, "validar-pendente")

    def test_so_leitura_e_permissoes(self):
        self.client.force_login(self.imp)  # vê revista, não valida
        r = self.abrir(self.lp)
        self.assertContains(r, "Só leitura: seu perfil confere as revistas, mas não valida.")
        self.assertNotContains(r, 'name="par"')
        self.assertNotContains(r, "Validar marcadas")
        self.assertNotContains(r, "Validar esta")
        self.assertEqual(self.client.post(URL, {"par": [f"{self.lp.pk}:x"]}).status_code, 403)
        self.assertEqual(self.validadas(), set())
        self.client.force_login(usuario("nada"))  # sem view_revista
        self.assertEqual(self.client.get(URL).status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get(URL), f"{reverse('admin:login')}?next={URL}")

    def test_post_grava_pela_regra_e_volta_a_tela(self):
        r = self.enviar(self.lp, self.mt)
        self.assertRedirects(r, f"{URL}?revista={self.lp.pk}&revista={self.mt.pk}")
        self.assertIn("Validadas 2 revista(s).", mensagens(r))
        self.assertEqual(self.validadas(), {self.lp.pk, self.mt.pk})
        self.assertEqual(Revista.objects.get(pk=self.lp.pk).validado_por, self.ped)
        self.assertContains(r, "Validada nesta versão", count=2)
        self.assertNotRegex(r.content.decode(), r'name="par" value="[^"]+" checked')  # já validadas: não pré-marca

    def test_revista_que_mudou_e_recusada_com_motivo(self):
        aberta = self.abrir(self.lp, self.mt)
        trocar_svg(self.mt, SVG_B)  # mudou entre ver e enviar
        r = self.client.post(URL, {"par": self.pares(aberta), "revista": [self.lp.pk, self.mt.pk]}, follow=True)
        msgs = mensagens(r)
        self.assertIn("Validadas 1 revista(s).", msgs)
        self.assertIn(f"Pulados: {self.mt} (a revista mudou depois que a página abriu; confira de novo).", msgs)
        self.assertEqual(self.validadas(), {self.lp.pk})

    def test_projeto_em_edicao_avisa_e_e_pulado(self):
        completar(self.pe["LP"])
        self.travar(self.projeto_pe)
        r = self.abrir(self.pe["LP"])
        self.assertContains(r, "Em edição por outro: será pulada")
        msgs = mensagens(self.enviar(self.pe["LP"]))
        self.assertIn(f"Pulados: {self.pe['LP']} (projeto em edição por outro).", msgs)
        self.assertEqual(self.validadas(), set())

    def test_validar_esta_pelo_htmx_devolve_so_o_cartao(self):
        aberta = self.abrir(self.lp, self.mt)
        par_lp = next(p for p in self.pares(aberta) if p.startswith(f"{self.lp.pk}:"))
        r = self.client.post(URL, {"par": self.pares(aberta), "so": par_lp}, HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "ui/parciais/validar_cartao.html")
        self.assertTemplateNotUsed(r, "ui/base.html")
        self.assertContains(r, f'id="validar-{self.lp.pk}"')
        self.assertNotContains(r, f'id="validar-{self.mt.pk}"')
        self.assertContains(r, "Validada nesta versão")
        self.assertContains(r, 'hx-swap-oob="true"')
        self.assertContains(r, "Validadas 1 revista(s).")
        self.assertEqual(self.validadas(), {self.lp.pk})  # só a do cartão, mesmo com a outra marcada

    def test_vazio_fora_e_nada_marcado(self):
        r = self.client.get(URL)
        self.assertContains(r, "Nenhuma revista para validar")
        self.assertContains(r, reverse("painel", args=[2026]) + "?falta=validado")
        r = self.client.get(URL, {"revista": [self.lp.pk, 999999]})
        self.assertContains(r, "1 revista(s) pedida(s) não aparecem: arquivadas ou de outro ano.")
        r = self.enviar(self.lp, pares=[])
        self.assertIn("Nada foi validado: nenhuma revista marcada. Marque ao menos uma e envie de novo.", mensagens(r))
        self.assertEqual(self.validadas(), set())

    def test_diff_contra_a_ultima_impressa(self):
        fotografar(carregar(self.lp.pk), Motivo.IMPRESSO, self.ped)
        self.assertContains(self.abrir(self.lp), "Sem mudanças desde a última impressa.")
        trocar_svg(self.lp, SVG_B)
        r = self.abrir(self.lp)
        self.assertContains(r, "Mudanças desde a última impressa")
        self.assertContains(r, 'class="diff"')
