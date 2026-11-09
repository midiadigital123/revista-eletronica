import xml.etree.ElementTree as ET

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from nucleo.servicos import f2

ETAPAS = ("1EF", "2EF", "3EF", "4EF", "5EF", "6EF", "7EF", "8EF", "9EF", "1EM", "2EM", "3EM")
MARCAS = "IIAACAAAAAAR"


def contexto_cheio():
    """Contexto do f2.svg com os 4 passos ligados, montado à mão (o gerador é da tarefa 3)."""
    pos = {nome: {"x": x, "y": y} for nome, (x, y, _, _) in f2.CAIXA.items()}
    tabela, y = [], f2.TABELA_Y
    for etapa, marca, altura in zip(ETAPAS, MARCAS, f2.ALTURAS_LINHAS):
        tabela.append({"etapa": etapa, "marca": marca, "cor": f2.CORES_MARCA[marca],
                       "y": round(y, 1), "altura": altura, "meio": altura / 2})
        y += altura
    return {
        "componente": "Língua Portuguesa",
        "habilidade": "Interpretar texto com auxílio de material gráfico diverso.",
        "pos": pos,
        "linhas": [{"pontos": "111.9 445 111.9 216.8 262.8 216.8", "fim": {"x": 262.8, "y": 216.8}}],
        "tabela": tabela,
        "celulas": [{"codigo": "EF15LP18", "texto": "Relacionar texto com ilustrações.",
                     "y": f2.TABELA_Y, "altura": 45.3, "clamp": 3}],
        "pontos": [{"etapa": etapa, "marca": marca, "cor": f2.CORES_MARCA[marca],
                    "x": round(f2.PROGRESSAO_X + i * f2.PROGRESSAO_PASSO, 1)}
                   for i, (etapa, marca) in enumerate(zip(ETAPAS, MARCAS))],
        "itens": [{"posicao": i, "descritor": "D05", "rotulo": "2º ano do Ensino Fundamental"}
                  for i in range(1, 5)],
    }


class SvgTest(SimpleTestCase):
    def test_svg_valido_e_sem_curvas(self):
        svg = render_to_string("revista/f2.svg", contexto_cheio())

        raiz = ET.fromstring(svg)
        ids = {el.get("id") for el in raiz.iter()}
        for bloco in ("cabecalho", "descritor", "habilidades", "progressao", "tarefas"):
            self.assertIn(f"f2-{bloco}", ids)
        for passo in ("descritor", "habilidades", "progressao", "tarefa-1", "tarefa-2", "tarefa-3", "tarefa-4"):
            self.assertIn(f"f2-btn-action-{passo}", ids)
        self.assertLess(len(svg.encode()), 150_000)  # o original tem 837 KB de texto em curva
        self.assertLess(svg.count("<path"), 20)  # sem glifos: só as formas do desenho
        self.assertIn("Língua Portuguesa".upper(), svg)
        self.assertIn('translate(19.3,0)', svg)  # número com ponto, não com a vírgula do pt-br
