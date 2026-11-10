import xml.etree.ElementTree as ET

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.html import escape, json_script
from django.utils.safestring import SafeData

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
        for passo in ("descritor", "habilidades", "progressao", "tarefas", "tarefa-1", "tarefa-2", "tarefa-3", "tarefa-4"):
            self.assertIn(f"f2-btn-action-{passo}", ids)
        self.assertLess(len(svg.encode()), 150_000)  # o original tem 837 KB de texto em curva
        self.assertLess(svg.count("<path"), 20)  # sem glifos: só as formas do desenho
        self.assertIn("Língua Portuguesa".upper(), svg)
        self.assertIn('translate(19.3,0)', svg)  # número com ponto, não com a vírgula do pt-br


ESCAPE = '<b>&"</script>'


def secoes():
    """Seções efetivas por id, como o resolvido as entrega (título escapado, corpo renderizado)."""
    def s(id_, titulo, corpo):
        return {"id": id_, "titulo": titulo, "corpo": corpo}

    return {
        "abertura": s("abertura", "Avaliação e currículo", "<p>Primeiro parágrafo.</p>\n<p>Segundo.</p>"),
        "passo-descritor": s("passo-descritor", "Descritor", "<p>O descritor.</p>"),
        "passo-habilidades": s("passo-habilidades", "Habilidades", "<p>As habilidades.</p>"),
        "passo-progressao": s("passo-progressao", "Progressão", "<p>A progressão.</p>"),
        "passo-tarefas": s("passo-tarefas", "Tarefas", "<p>As tarefas.</p>"),
        "dlg-descritor": s("dlg-descritor", "Sobre o descritor", "<p>Corpo do descritor.</p>"),
        "dlg-tarefas": s("dlg-tarefas", "Tarefas por nível", "<p>Corpo das tarefas.</p>"),
    }


def infografico(passos=f2.PASSOS, tipo="alfa", etapas=None):
    """Uma entrada de resolvido["f2"]["infograficos"] (formato da tarefa 4)."""
    if etapas is None:
        etapas = [{"etapa": e, "rotulo": e, "marca": m, "codigo": f"EF{i:02}", "texto": f"Texto {e}."}
                  for i, (e, m) in enumerate(zip(ETAPAS, MARCAS))]
    return {
        "tipo": tipo, "titulo": tipo, "passos": list(passos),
        "habilidade": "Interpretar texto com auxílio de material gráfico diverso.",
        "textos": {"descritor": "<p>Texto ❶.</p>", "progressao": "<p>Texto ❸.</p>", "habilidades": "<p>Texto ❷.</p>"},
        "etapas": etapas,
        "itens": [{"posicao": p, "etapa": e, "rotulo": f"{e} rótulo", "descritor": "D05", "imagem": f"item{p}.png",
                   "imagem_sha256": "0" * 64, "texto_alternativo": f"Item {p}", "analise": f"<p>Análise {p}.</p>"}
                  for p, e in ((4, "3EM"), (2, "5EF"), (1, "2EF"), (3, "9EF"))],
    }


def gerar(info=None, secs=None):
    return f2.gerar(info or infografico(), secs or secoes(), "arquivos/", "Língua Portuguesa")


def ids(svg):
    return {el.get("id") for el in ET.fromstring(svg).iter()} - {None}


class GerarTest(SimpleTestCase):
    def test_passo_desligado_some_do_svg_do_tour_e_dos_modais(self):
        r = gerar(infografico(passos=("descritor", "habilidades", "tarefas")))
        self.assertNotIn("f2-progressao", ids(r["svg"]))
        self.assertNotIn("dlg-progressao", [m["id"] for m in r["modais"]])
        self.assertNotIn("dlg-progressao", r["tour"]["modais"])
        self.assertNotIn("f2-progressao", [s["target"] for s in r["tour"]["steps"]])

        r = gerar(infografico(passos=("descritor", "progressao", "tarefas")))
        self.assertNotIn("f2-habilidades", ids(r["svg"]))
        self.assertIn('id="f2-progressao" transform="translate(661,69)"', r["svg"])
        self.assertIn('points="640.6 74.5 550.6 74.5 550.6 250.8 405.7 250.8"', r["svg"])

    def test_todos_desligados_so_descritor(self):
        r = gerar(infografico(passos=("descritor",)))
        self.assertLessEqual({"f2-cabecalho", "f2-descritor"}, ids(r["svg"]))
        self.assertFalse({"f2-habilidades", "f2-progressao", "f2-tarefas"} & ids(r["svg"]))
        self.assertNotIn("<polyline", r["svg"])
        self.assertEqual([s["target"] for s in r["tour"]["steps"]], ["f2-descritor"])
        self.assertEqual([m["id"] for m in r["modais"]], ["dlg-descritor"])
        self.assertEqual(r["tour"]["modais"], ["dlg-descritor"])

    def test_escape(self):
        info = infografico()
        info["habilidade"] = ESCAPE
        info["etapas"][0]["codigo"] = ESCAPE
        info["itens"][0]["descritor"] = ESCAPE
        info["itens"][0]["texto_alternativo"] = ESCAPE
        secs = secoes()
        secs["passo-descritor"]["titulo"] = escape(ESCAPE)  # o resolvido entrega o título escapado
        r = gerar(info, secs)

        textos = ["".join(el.itertext()) for el in ET.fromstring(r["svg"]).iter()]
        self.assertTrue(any(t == ESCAPE for t in textos))  # a habilidade, literal
        self.assertTrue(any(f"({ESCAPE})" in t for t in textos))  # o código BNCC
        self.assertNotIn("</script>", r["svg"])
        self.assertEqual(r["tour"]["steps"][0]["title"], ESCAPE)
        self.assertEqual(json_script(r["tour"]).count("</script>"), 1)  # só o fechamento da tag
        self.assertIn(escape(ESCAPE), r["modais"][-1]["titulo"])
        self.assertIn(f'alt="{escape(ESCAPE)}"', r["modais"][-1]["corpo"])

    def test_celula_mesclada_e_marca_vazia(self):
        etapas = [  # 1EF não gravada (vazia no topo); 3EF e 5EF.. 3EM vazias entram na de cima
            {"etapa": "2EF", "rotulo": "", "marca": "", "codigo": "EF15LP18", "texto": "Relacionar."},
            {"etapa": "3EF", "rotulo": "", "marca": "I", "codigo": "", "texto": ""},
            {"etapa": "4EF", "rotulo": "", "marca": "A", "codigo": "", "texto": "Só texto."},
        ]
        r = gerar(infografico(etapas=etapas))

        celulas = [(fo.get("height"), "".join(fo.itertext())) for fo in ET.fromstring(r["svg"]).iter("{http://www.w3.org/2000/svg}foreignObject")
                   if fo.get("width") == "351"]
        self.assertEqual(celulas, [("22.7", ""), ("45.3", "(EF15LP18) Relacionar."), ("294.8", "Só texto.")])
        self.assertEqual(r["svg"].count(f'fill="{f2.COR_SEM_MARCA}"'), 2 * 10)  # tabela e progressão
        self.assertEqual(r["svg"].count(f'fill="{f2.CORES_MARCA["I"]}"'), 2)
        self.assertEqual(r["svg"].count(f'fill="{f2.CORES_MARCA["A"]}"'), 2)

    def test_sem_secoes_e_sem_etapas(self):
        info = infografico()
        info["etapas"] = []
        r = f2.gerar(info, {}, "arquivos/", "Língua Portuguesa")
        self.assertEqual(r["tour"]["intro"], {"title": "", "text": ""})
        self.assertEqual(r["svg"].count(f'fill="{f2.COR_SEM_MARCA}"'), 2 * 12)  # tabela e progressão

    def test_item_sem_imagem_sai_sem_img(self):
        info = infografico()
        info["itens"][2]["imagem"] = ""  # posição 1
        info["itens"][1]["imagem"] = "infograficos/item2.png"  # posição 2: o caminho do storage
        modais = {m["id"]: m for m in gerar(info)["modais"]}
        self.assertNotIn("<img", modais["dlg-tarefa-1"]["corpo"])
        self.assertIsInstance(modais["dlg-tarefa-1"]["corpo"], SafeData)
        self.assertIn("Análise 1.", modais["dlg-tarefa-1"]["corpo"])
        # O src é <base_imagens><nome do arquivo>: sem "infograficos/" duplicado (D-244).
        self.assertIn('<img src="arquivos/item2.png" alt="Item 2">', modais["dlg-tarefa-2"]["corpo"])
        self.assertEqual(modais["dlg-tarefa-2"]["titulo"], "D05 – 5EF rótulo")

    def test_ids_do_tour_existem_no_svg(self):
        r = gerar()
        no_svg = ids(r["svg"])
        self.assertEqual([s["target"] for s in r["tour"]["steps"]], [f"f2-{p}" for p in f2.PASSOS])
        for s in r["tour"]["steps"]:
            self.assertIn(s["target"], no_svg)
        self.assertEqual(r["tour"]["modais"], [m["id"] for m in r["modais"]])
        self.assertEqual(len(r["modais"]), 8)
        for m in r["modais"]:
            self.assertIn(m["id"].replace("dlg-", "f2-btn-action-"), no_svg)
        self.assertEqual(r["tour"]["intro"], {"title": "Avaliação e currículo", "text": "Primeiro parágrafo."})
        self.assertEqual(r["tour"]["label"], f2.ROTULO_TOUR)

    def test_alfa_e_outras_mesmo_desenho(self):
        outras = infografico(tipo="outras")
        for item in outras["itens"]:
            item["rotulo"] = "outro rótulo"

        def caixas(info):
            return [(el.get("id"), el.get("transform")) for el in ET.fromstring(gerar(info)["svg"]).iter() if el.get("id")]

        self.assertEqual(caixas(infografico()), caixas(outras))
