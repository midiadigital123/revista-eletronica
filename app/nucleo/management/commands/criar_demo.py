"""Dados de demonstração para ver o preview no navegador (S08).

Cria (idempotente) o parceiro "DEMONSTRAÇÃO" no ano, com matriz pequena, cortes de LP,
templates do seed, o SVG real do F2 (fixture dos testes) e uma capa lisa; cria ou atualiza
o usuário `demo` com senha nova a cada execução e imprime a URL do preview.
Não toca em outros parceiros. Só para desenvolvimento.
"""

import secrets
import struct
import zlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from nucleo.models import (
    Componente,
    Descritor,
    Etapa,
    Matriz,
    MatrizEtapaCC,
    Parceiro,
    ParceiroAno,
    Revista,
    RevistaFasciculo,
    Tarefa,
    Template,
)
from nucleo.servicos.arquivos import receber_capa, receber_svg
from nucleo.servicos.cascata import gravar_cortes

PARCEIRO = "DEMONSTRAÇÃO"
SVG = settings.BASE_DIR / "nucleo" / "tests" / "fixtures" / "f2-lp.svg"
CORTES = [150, 200, 250, 300]
TAREFAS = [(100, 150, "Localiza informação explícita."), (225, 275, "Infere o sentido de uma palavra."),
           (325, 375, "Reconhece a tese de um texto argumentativo.")]  # fmt: skip


def png(largura, altura, rgb):
    """PNG liso, só com a stdlib (capa de demonstração)."""
    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    linhas = b"".join(b"\x00" + bytes(rgb) * largura for _ in range(altura))
    cabecalho = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", cabecalho) + bloco(b"IDAT", zlib.compress(linhas)) + bloco(b"IEND", b"")


class Command(BaseCommand):
    help = "Cria a revista de demonstração e o usuário demo; imprime a URL do preview."

    def add_arguments(self, parser):
        parser.add_argument("--ano", type=int, default=2026)

    def handle(self, *args, ano, **opcoes):
        call_command("carregar_cadastros", ano=ano)
        call_command("carregar_templates", ano=ano)
        usuario, _ = get_user_model().objects.get_or_create(
            username="demo", defaults={"is_staff": True}
        )
        senha = secrets.token_urlsafe(9)
        usuario.set_password(senha)
        usuario.save()

        with transaction.atomic():
            revista = self.revista(ano, usuario)
        url = f"http://localhost:8000/preview/{revista.pk}/"
        self.stdout.write(self.style.SUCCESS(f"Preview: {url}\nUsuário: demo  Senha: {senha}"))

    def revista(self, ano, usuario):
        lp = Componente.objects.get(ano__ano=ano, codigo="LP")
        etapas = list(Etapa.objects.filter(ano__ano=ano, codigo__in=["5EF", "9EF"]).order_by("ordem"))
        matriz, nova = Matriz.objects.get_or_create(ano=lp.ano, nome="Demonstração")
        if nova:
            for etapa in etapas:
                mec = MatrizEtapaCC.objects.create(matriz=matriz, etapa=etapa, componente=lp, ano=lp.ano, passo=25)
                for k in range(1, 4):
                    d = Descritor.objects.create(
                        matriz_etapa_cc=mec, codigo=f"D0{k}", ordem=k,
                        descricao=f"Descritor {k} de demonstração ({etapa.codigo}).",
                        prerequisitos=["Ler frases simples.", "Reconhecer o assunto do texto."],
                        praticas="Leitura", conhecimento="Estratégias de leitura",
                        habilidades_relacionadas="EF15LP03",
                    )  # fmt: skip
                    for ordem, (inicio, fim, texto) in enumerate(TAREFAS, 1):
                        Tarefa.objects.create(descritor=d, inicio=inicio, fim=fim, texto=texto, ordem=ordem)
        parceiro, _ = Parceiro.objects.get_or_create(nome=PARCEIRO)
        pa, _ = ParceiroAno.objects.get_or_create(parceiro=parceiro, ano=lp.ano, defaults={"matriz": matriz})
        revista = Revista.objects.filter(projeto__parceiro_ano=pa, componente=lp, arquivada_em__isnull=True).first()
        if revista is not None:
            return revista
        gravar_cortes(pa, [(e, lp, CORTES) for e in etapas], usuario)
        revista = Revista.objects.get(projeto__parceiro_ano=pa, componente=lp, arquivada_em__isnull=True)
        for rf in RevistaFasciculo.objects.filter(revista=revista):
            rf.template = Template.objects.get(ano=lp.ano, componente=lp, fasciculo=rf.fasciculo, nome="Padrão")
            rf.save()
        receber_svg(revista, SimpleUploadedFile("f2.svg", SVG.read_bytes()))
        receber_capa(revista, SimpleUploadedFile("capa.png", png(320, 320, (255, 235, 0))))
        return revista
