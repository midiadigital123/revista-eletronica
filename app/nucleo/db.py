from django.db import migrations


def fk_composta(tabela, alvo, colunas=None, colunas_alvo=None, nome=None):
    """FK composta (o ORM não declara) mais um índice próprio, com reverse_sql.

    Caso comum: fk_composta("matriz_etapa_cc", "matriz") cria
    (matriz_id, ano_id) -> matriz (id, ano_id), nome fk_matriz_etapa_cc_matriz_ano.
    colunas_alvo padrão: ("id", *colunas[1:]). O alvo precisa ter UNIQUE nelas.
    Fica NO ACTION e MATCH SIMPLE: coluna nula = sem checagem (D-106).
    """
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
