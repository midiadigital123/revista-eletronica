from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual


def max_len(tabela, campo, n):
    """Convenção do ER: text + CHECK de tamanho, sem varchar(n)."""
    return models.CheckConstraint(
        condition=LessThanOrEqual(Length(campo), n), name=f"{tabela}_{campo}_tamanho"
    )


def sha256(tabela, campo):
    """Convenção do ER: hash é text com 64 hex minúsculos (nulo passa)."""
    return models.CheckConstraint(
        condition=Q(**{f"{campo}__regex": r"^[0-9a-f]{64}$"}), name=f"{tabela}_{campo}_sha256"
    )


def fk_composta(tabela, alvo, colunas=None, colunas_alvo=None, nome=None):
    """FK composta (o ORM não declara) mais um índice próprio, com reverse_sql.

    Caso comum, coerência de ano: fk_composta("matriz_etapa_cc", "matriz") cria
    (matriz_id, ano_id) -> matriz (id, ano_id), nome fk_matriz_etapa_cc_matriz_ano.
    Com `colunas` explícitas, `nome` é obrigatório: a FK pode não ser de ano e
    duas FKs da mesma tabela para o mesmo alvo não podem colidir.
    colunas_alvo padrão: ("id", *colunas[1:]). O alvo precisa de UNIQUE nelas.

    Fica NO ACTION (ON DELETE e ON UPDATE) e MATCH SIMPLE: se QUALQUER coluna
    da FK for nula, o banco não confere nada. Por isso toda coluna de FK composta
    precisa ser NOT NULL, exceto as que o ER declara anuláveis de propósito
    (parceiro_ano.matriz_id, revista_fasciculo.template_id); o teste de
    catálogo confere isso.
    """
    if colunas is not None and nome is None:
        raise ValueError("fk_composta com colunas explícitas exige nome")
    colunas = tuple(colunas or (f"{alvo}_id", "ano_id"))
    colunas_alvo = tuple(colunas_alvo or ("id", *colunas[1:]))
    nome = nome or f"fk_{tabela}_{alvo}_ano"
    indice = "ix_" + nome.removeprefix("fk_")
    return migrations.RunSQL(
        sql=[
            f"ALTER TABLE {tabela} ADD CONSTRAINT {nome} FOREIGN KEY ({', '.join(colunas)}) "
            f"REFERENCES {alvo} ({', '.join(colunas_alvo)})",
            f"CREATE INDEX {indice} ON {tabela} ({', '.join(colunas)})",
        ],
        reverse_sql=[
            f"DROP INDEX {indice}",
            f"ALTER TABLE {tabela} DROP CONSTRAINT {nome}",
        ],
    )
