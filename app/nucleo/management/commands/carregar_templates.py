"""Carrega os templates de texto do ano a partir de `templates_seed/<ano>/f{1,2}-{lp,mt}.hbs`.

Cria o template e a versão 1. Template que já existe fica como está (nunca sobrescreve).
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nucleo.models import Ano, Componente, Template, TemplateVersao
from nucleo.texto import validar

NOME = "Padrão"
ARQUIVO = re.compile(r"f([12])-(lp|mt)\.hbs")
SEEDS = {f"f{n}-{cc}.hbs" for n in "12" for cc in ("lp", "mt")}
# Aviso de revisão no topo do seed: não chega ao banco (HTML é recusado).
AVISO = re.compile(r"\A<!-- revisar com a Pedagógica[^>]*-->\n")


class Command(BaseCommand):
    help = "Cria os templates de texto do ano a partir dos seeds .hbs (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--ano", type=int, required=True)

    @transaction.atomic
    def handle(self, *args, ano, **opcoes):
        pasta = settings.BASE_DIR / "templates_seed" / str(ano)
        arquivos = sorted(p for p in pasta.glob("*.hbs") if ARQUIVO.fullmatch(p.name))
        if not arquivos:
            raise CommandError(f"Nenhum seed f1/f2-lp/mt.hbs em {pasta}.")
        try:
            ano_obj = Ano.objects.get(ano=ano)
        except Ano.DoesNotExist:
            raise CommandError(f"Ano {ano} não cadastrado: rode carregar_cadastros --ano {ano}.")
        faltando = sorted(SEEDS - {p.name for p in arquivos})
        if faltando:
            self.stdout.write(self.style.WARNING(f"aviso: seeds faltando em {pasta}: {', '.join(faltando)}"))

        for arquivo in arquivos:
            num, cc = ARQUIVO.fullmatch(arquivo.name).groups()
            fasciculo, origem = f"F{num}", f"templates_seed/{ano}/{arquivo.name}"
            try:
                componente = Componente.objects.get(ano=ano_obj, codigo=cc.upper())
            except Componente.DoesNotExist:
                raise CommandError(f"Componente {cc.upper()} não cadastrado em {ano}.")

            texto = AVISO.sub("", arquivo.read_text(encoding="utf-8-sig"))
            try:
                validar(texto, fasciculo)
            except ValidationError as e:
                raise CommandError(f"{origem} inválido: {' '.join(e.messages)}")

            template, criado = Template.objects.get_or_create(
                ano=ano_obj, componente=componente, fasciculo=fasciculo, nome=NOME,
                defaults={"origem": origem},
            )  # fmt: skip
            if criado:
                TemplateVersao.objects.create(template=template, numero=1, texto=texto)
                self.stdout.write(f"criado: {origem}")
            else:
                self.stdout.write(f"já existe, mantido: {origem}")
                v1 = TemplateVersao.objects.filter(template=template, numero=1).first()
                if v1 and v1.texto != texto:
                    self.stdout.write(self.style.WARNING(f"aviso: {origem} difere da versão 1 no banco"))
