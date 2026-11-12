from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from nucleo.models import Ano, Componente, Corte, Etapa, Parceiro, ParceiroAno
from nucleo.servicos.cascata import gravar_cortes

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
        "Cria os parceiros do ano (planilha Somativas) e grava os cortes de LP e MT que existem na planilha "
        "de cortes, pela cascata. Parceiro que já tem corte é pulado. Só as etapas cadastradas no ano entram."
    )

    def add_arguments(self, parser):
        parser.add_argument("somativas")
        parser.add_argument("cortes")
        parser.add_argument("--ano", type=int, required=True)
        parser.add_argument("--usuario", required=True, help="username do autor no histórico")
        parser.add_argument("--simular", action="store_true", help="roda tudo e desfaz: só mostra o relatório")

    def handle(self, *args, somativas, cortes, ano, usuario, simular, **opcoes):
        ano_obj = Ano.objects.filter(ano=ano).first()
        if not ano_obj:
            raise CommandError(f"ano {ano} não cadastrado (rode carregar_cadastros --ano {ano})")
        autor = get_user_model().objects.filter(username=usuario).first()
        if not autor:
            raise CommandError(f"usuário {usuario!r} não existe")
        parceiros, tabela = ler_somativas(somativas), ler_cortes(cortes)
        etapas = {e.codigo: e for e in Etapa.objects.filter(ano=ano_obj)}
        componentes = {c.codigo: c for c in Componente.objects.filter(ano=ano_obj)}

        gravados = 0
        with transaction.atomic():
            for nome, pedidas in sorted(parceiros.items()):
                linhas, faltam = [], []
                for etapa in (e for e in etapas if e in pedidas):
                    for comp, componente in componentes.items():
                        valores = tabela.get((nome, etapa, comp))
                        if valores:
                            linhas.append((etapas[etapa], componente, valores))
                        else:
                            faltam.append(f"{etapa}-{comp}")
                pa = ParceiroAno.objects.get_or_create(
                    parceiro=Parceiro.objects.get_or_create(nome=nome)[0], ano=ano_obj
                )[0]
                if Corte.objects.filter(parceiro_ano=pa).exists():
                    estado = "pulado (já tem cortes)"
                elif linhas:
                    gravar_cortes(pa, linhas, autor)
                    gravados += len(linhas)
                    estado = f"{len(linhas)} corte(s)"
                else:
                    estado = "sem cortes"
                ignoradas = sorted(pedidas - set(etapas))
                self.stdout.write(
                    f"{nome}: {estado}"
                    + (f"; faltam {', '.join(faltam)}" if faltam else "")
                    + (f"; etapas ignoradas {', '.join(ignoradas)}" if ignoradas else "")
                )
            self.stdout.write(f"{len(parceiros)} parceiro(s), {gravados} corte(s) gravado(s).")
            if simular:
                transaction.set_rollback(True)
                self.stdout.write("Simulação: nada foi gravado.")
