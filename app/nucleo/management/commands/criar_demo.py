"""Dados de demonstração para ver o preview no navegador (S08).

Cria (idempotente) o parceiro "DEMONSTRAÇÃO" no ano, com matriz pequena, cortes de LP,
templates do seed, os infográficos do F2 com os dados do docx de LP 2026 (D-248) e uma capa
lisa; cria ou atualiza o usuário `demo-preview` (só `view_revista`) com senha nova a cada
execução e imprime a URL. Não toca em outros parceiros. Só com DEBUG; recusa trocar a senha
de um `demo-preview` que não foi criado por este comando (marca em `first_name`).
"""

import base64
import hashlib
import json
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
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
    RevistaInfografico,
    RevistaInfograficoEtapa,
    RevistaInfograficoItem,
    Tarefa,
    Template,
)
from nucleo.servicos.arquivos import receber_capa
from nucleo.servicos.cascata import gravar_cortes

PARCEIRO = "DEMONSTRAÇÃO"
USUARIO = "demo-preview"
MARCA = "demo criado por criar_demo"
# Infográfico de LP 2026 tirado do docx (D-248): só os campos que o modelo guarda.
DOCX = json.loads((settings.BASE_DIR / "nucleo" / "dados" / "infografico-docx.json").read_text(encoding="utf-8"))
CORTES = [150, 200, 250, 300]
TAREFAS = [(100, 150, "Localiza informação explícita."), (225, 275, "Infere o sentido de uma palavra."),
           (325, 375, "Reconhece a tese de um texto argumentativo.")]  # fmt: skip


# Capa lisa da demonstração: PNG 1×1 amarelo.
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4/5oBAATXAesdPD2pAAAAAElFTkSuQmCC")


class Command(BaseCommand):
    help = "Cria a revista de demonstração e o usuário demo; imprime a URL do preview."

    def add_arguments(self, parser):
        parser.add_argument("--ano", type=int, default=2026)

    def handle(self, *args, ano, **opcoes):
        if not settings.DEBUG:
            raise CommandError("criar_demo só roda com DEBUG (desenvolvimento).")
        usuario, _ = get_user_model().objects.get_or_create(
            username=USUARIO, defaults={"is_staff": True, "first_name": MARCA}
        )
        if usuario.first_name != MARCA or usuario.is_superuser:
            raise CommandError(f"O usuário {USUARIO} já existe e não foi criado por este comando.")
        call_command("carregar_cadastros", ano=ano)
        call_command("carregar_templates", ano=ano)
        senha = secrets.token_urlsafe(9)
        usuario.set_password(senha)
        usuario.save()
        usuario.user_permissions.add(Permission.objects.get(codename="view_revista", content_type__app_label="nucleo"))

        with transaction.atomic():
            revista = self.revista(ano, usuario)
            preencher_infograficos(revista)
        url = f"http://localhost:8000/preview/{revista.pk}/"
        self.stdout.write(self.style.SUCCESS(f"Preview: {url}\nUsuário: {USUARIO}  Senha: {senha}"))

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
        receber_capa(revista, SimpleUploadedFile("capa.png", PNG))
        return revista


def preencher_infograficos(revista, caminho="infograficos/demo-{tipo}-{p}.png"):
    """Os infográficos ativos com os dados do docx e o PNG da capa em cada um dos 4 itens. Idempotente."""
    sha = hashlib.sha256(PNG).hexdigest()
    for inf in RevistaInfografico.objects.filter(revista=revista, arquivado_em__isnull=True):
        RevistaInfografico.objects.update_or_create(  # save(): o histórico registra
            pk=inf.pk, defaults={c: DOCX[c] for c in ("habilidade", "texto_descritor", "texto_habilidades", "texto_progressao")}
        )
        for e in DOCX["etapas"]:
            RevistaInfograficoEtapa.objects.update_or_create(
                infografico=inf, etapa=e["etapa"], defaults={"ano_id": inf.ano_id, **e}
            )
        for p, item in enumerate(DOCX["itens"], 1):
            imagem = caminho.format(tipo=inf.tipo, p=p)
            # Direto no storage, não por arquivos.receber_imagem_item: ela grava com nome uuid e cada
            # execução deixaria uma cópia; com nome fixo, rodar de novo não cria arquivo.
            if not default_storage.exists(imagem):
                default_storage.save(imagem, ContentFile(PNG))
            RevistaInfograficoItem.objects.update_or_create(
                infografico=inf, posicao=p, defaults={"ano_id": inf.ano_id, "imagem": imagem, "imagem_sha256": sha, **item}
            )
