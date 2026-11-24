from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from nucleo.models import Ano, Componente, Corte, Etapa, Matriz, Parceiro, ParceiroAno
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.matriz import atribuir_matriz

# Nome na planilha Somativas -> Parceiro.nome (D-261): sigla para estado; cidade com o nome da planilha de cortes.
# ponytail: carga única de 2026; se virar rotina anual, o mapa sai do comando.
NOMES = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Ceará": "CE", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG", "Pará": "PA",
    "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE", "Tocantins": "TO",
    "Florianópolis": "Florianópolis", "Joinville": "JOINVILLE", "Porto Alegre": "PORTO ALEGRE",
    "Salvador": "SALVADOR", "Anchieta": "Anchieta", "Angra dos Reis": "Angra dos Reis",
    "Belo Horizonte": "Belo Horizonte", "Niterói": "Niterói", "Rio de Janeiro (município)": "Rio (município)",
}

# D-278: a carga cria a etapa que a Somativas pede e o ano não tem, e preenche o corte que falta.
# ponytail: valores fixos da carga única de 2026; a Pedagógica corrige o corte pela tela.
ESCALA_1000 = {"1EF", "2EF"}  # as demais vão a 500
ARBITRARIO = [100, 200, 300]  # cabe em toda escala (0 < corte < escala_max)


def ler_somativas(caminho):
    """{parceiro: {etapas da revista}}. Linhas ALFA e regular do mesmo parceiro somam as etapas."""
    parceiros = {}
    for aba in load_workbook(caminho, read_only=True, data_only=True):
        for linha in list(aba.iter_rows(values_only=True))[1:]:
            subprograma, etapas = linha[0], linha[4]
            if not subprograma:
                continue
            partes = [p.strip() for p in subprograma.split(" - ")]
            chave = partes[1] if partes[0] == "Municípios" else partes[0]
            if chave not in NOMES:
                raise CommandError(f"parceiro sem mapeamento: {subprograma!r}")
            parceiros.setdefault(NOMES[chave], set()).update(e.strip() for e in (etapas or "").split(",") if e.strip())
    return parceiros


def ler_cortes(caminho):
    """{(parceiro, etapa, componente): [valores]} das abas "ETAPA - CC"."""
    cortes = {}
    for aba in load_workbook(caminho, read_only=True, data_only=True):
        etapa, componente = (s.strip() for s in aba.title.split(" - "))
        for linha in list(aba.iter_rows(values_only=True))[1:]:
            parceiro, valores = linha[1], linha[3]  # a aba 9EF - LP tem uma coluna E sobrando
            if parceiro and valores:
                cortes[(parceiro.strip(), etapa, componente)] = [int(v) for v in str(valores).split(",")]
    return cortes


class Command(BaseCommand):
    help = (
        "Cria os parceiros do ano e as etapas que faltam (planilha Somativas) e grava os cortes de LP e MT pela "
        "cascata: o valor da planilha de cortes ou, se faltar, 100, 200, 300 (listado no relatório). "
        "Parceiro que já tem corte é pulado. --matriz atribui a matriz a quem ainda não tem."
    )

    def add_arguments(self, parser):
        parser.add_argument("somativas")
        parser.add_argument("cortes")
        parser.add_argument("--ano", type=int, required=True)
        parser.add_argument("--usuario", required=True, help="username do autor no histórico")
        parser.add_argument("--matriz", help='nome da matriz dos parceiros sem matriz, ex.: "Comunitária" (criada se faltar)')
        parser.add_argument("--simular", action="store_true", help="roda tudo e desfaz: só mostra o relatório")

    def handle(self, *args, somativas, cortes, ano, usuario, matriz, simular, **opcoes):
        ano_obj = Ano.objects.filter(ano=ano).first()
        if not ano_obj:
            raise CommandError(f"ano {ano} não cadastrado (rode carregar_cadastros --ano {ano})")
        autor = get_user_model().objects.filter(username=usuario).first()
        if not autor:
            raise CommandError(f"usuário {usuario!r} não existe")
        parceiros, tabela = ler_somativas(somativas), ler_cortes(cortes)
        componentes = {c.codigo: c for c in Componente.objects.filter(ano=ano_obj)}

        gravados = arbitrarios = 0
        with transaction.atomic():
            existentes = set(Etapa.objects.filter(ano=ano_obj).values_list("codigo", flat=True))
            criadas = sorted(set().union(*parceiros.values()) - existentes)
            for codigo in criadas:
                etapa = Etapa(ano=ano_obj, codigo=codigo, escala_max=1000 if codigo in ESCALA_1000 else 500)
                etapa._history_user = autor
                etapa.save()  # a ordem escolar sai do save
            etapas = {e.codigo: e for e in Etapa.objects.filter(ano=ano_obj).order_by("ordem")}
            matriz_obj = Matriz.objects.get_or_create(ano=ano_obj, nome=matriz)[0] if matriz else None

            for nome, pedidas in sorted(parceiros.items()):
                linhas, sem_valor = [], []
                for etapa in (e for e in etapas if e in pedidas):
                    for comp, componente in componentes.items():
                        valores = tabela.get((nome, etapa, comp))
                        if not valores:
                            valores = ARBITRARIO
                            sem_valor.append(f"{etapa}-{comp}")
                        linhas.append((etapas[etapa], componente, valores))
                pa = ParceiroAno.objects.get_or_create(
                    parceiro=Parceiro.objects.get_or_create(nome=nome)[0], ano=ano_obj
                )[0]
                if matriz_obj and pa.matriz_id is None:
                    atribuir_matriz(pa, matriz_obj, autor)
                if Corte.objects.filter(parceiro_ano=pa).exists():
                    self.stdout.write(f"{nome}: pulado (já tem cortes)")
                    continue
                if linhas:
                    gravar_cortes(pa, linhas, autor)
                    gravados += len(linhas)
                    arbitrarios += len(sem_valor)
                self.stdout.write(
                    f"{nome}: " + (f"{len(linhas)} corte(s)" if linhas else "sem cortes")
                    + (f"; arbitrários {', '.join(sem_valor)}" if sem_valor else "")
                )
            if criadas:
                self.stdout.write(f"etapas criadas: {', '.join(criadas)}")
            self.stdout.write(
                f"{len(parceiros)} parceiro(s), {gravados} corte(s) gravado(s), {arbitrarios} arbitrário(s)."
            )
            if simular:
                transaction.set_rollback(True)
                self.stdout.write("Simulação: nada foi gravado.")
