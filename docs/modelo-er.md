# Modelo ER — rascunho (Django + PostgreSQL)

Fonte: decisões D-046 a D-083 do `state.md`. Rascunho para a sessão de modelagem; nada aqui está implementado.

```mermaid
erDiagram
    Ano ||--o{ Matriz : tem
    Ano ||--o{ TextoModelo : tem
    Ano ||--o{ Corte : tem
    Ano ||--o{ Projeto : tem
    Ano ||--o{ Etapa : tem
    Ano ||--o{ ComponenteCurricular : tem
    Ano ||--o{ CorPadrao : tem

    Parceiro ||--o{ Corte : recebe
    Parceiro ||--o{ Projeto : tem

    Etapa ||--o{ MatrizEtapaCC : ""
    ComponenteCurricular ||--o{ MatrizEtapaCC : ""
    Etapa ||--o{ Corte : ""
    ComponenteCurricular ||--o{ Corte : ""

    Matriz ||--o{ MatrizEtapaCC : "dividida em"
    MatrizEtapaCC ||--o{ Descritor : tem
    Descritor ||--o{ Tarefa : tem

    TextoModelo ||--o{ BlocoTexto : "dividido em"

    Matriz ||--o{ Projeto : "usada por"
    TextoModelo ||--o{ Projeto : "usado por"

    Projeto ||--o{ ProjetoBloco : sobrescreve
    BlocoTexto ||--o{ ProjetoBloco : ""
    Projeto ||--o{ ProjetoIntervaloMinimo : sobrescreve
    Projeto ||--o{ ProjetoCor : sobrescreve
    Projeto ||--o{ FotoRevista : "fotos do impresso"

    MatrizEtapaCC ||--o| Bloqueio : ""
    Projeto ||--o| Bloqueio : ""

    Ano {
        int ano UK "2026"
    }
    Parceiro {
        string nome UK "GO, JOINVILLE, Florianopolis"
    }
    Etapa {
        int ano_id FK
        string codigo "2EF, 5EF, 9EF, 3EM"
        int escala_max "1000 no 2EF, 500 nas demais"
        int ordem
    }
    ComponenteCurricular {
        int ano_id FK
        string codigo "LP, MT"
        string nome
    }
    Matriz {
        int ano_id FK
        string nome "Comunitaria, CE, ES, JOINVILLE"
    }
    MatrizEtapaCC {
        int matriz_id FK
        int etapa_id FK
        int cc_id FK
        int intervalo_minimo "nulo = sem linhas vazias (2EF)"
        int passo "largura do intervalo, ex. 25"
    }
    Descritor {
        int matriz_etapa_cc_id FK
        string codigo "D01"
        text descricao
        text_arr prerequisitos
        text praticas
        text conhecimento
        text habilidades_relacionadas
        text habilidade_correspondente
        int ordem
    }
    Tarefa {
        int descritor_id FK
        int inicio "CHECK inicio < fim"
        int fim
        text texto
        file arquivo "PDF/PNG/JPG, opcional"
        int ordem
    }
    TextoModelo {
        int ano_id FK
        string nome
    }
    BlocoTexto {
        int texto_modelo_id FK
        string titulo
        text conteudo "com marcadores PARCEIRO, NOME DO PROJETO, ANO"
        int versao "sobe a cada edicao"
        int ordem
    }
    Corte {
        int parceiro_id FK
        int ano_id FK
        int etapa_id FK
        int cc_id FK
        int_arr valores "1 a 4, crescentes"
    }
    Projeto {
        int parceiro_id FK
        int ano_id FK
        int matriz_id FK
        int texto_modelo_id FK
        string nome "GO - NOME DO PROJETO"
        bool arquivado
        string hash_validado "hash da revista no clique Validado"
    }
    ProjetoBloco {
        int projeto_id FK
        int bloco_id FK
        text conteudo
        int versao_base "versao do bloco ao sobrescrever"
    }
    ProjetoIntervaloMinimo {
        int projeto_id FK
        int etapa_id FK
        int cc_id FK
        int intervalo_minimo
    }
    CorPadrao {
        int ano_id FK
        int padrao "1 a 5"
        string cor "padrao 5 = #FFF"
    }
    ProjetoCor {
        int projeto_id FK
        int padrao "1 a 5"
        string cor
    }
    FotoRevista {
        int projeto_id FK
        jsonb conteudo "revista resolvida"
        datetime criada_em
        int criada_por FK
    }
    Bloqueio {
        int matriz_etapa_cc_id FK "um dos dois"
        int projeto_id FK "um dos dois"
        int usuario_id FK
        datetime expira_em "agora + 30 s"
    }
```

## Restrições que o diagrama não mostra

| Tabela | Restrição | Decisão |
|---|---|---|
| Etapa / ComponenteCurricular | UNIQUE (ano, codigo) | D-086 |
| CorPadrao | UNIQUE (ano, padrao) | D-086 |
| Matriz | UNIQUE (ano, nome) | D-057 |
| MatrizEtapaCC | UNIQUE (matriz, etapa, cc) | D-053 |
| Descritor | UNIQUE (matriz_etapa_cc, codigo) | — |
| Corte | UNIQUE (parceiro, ano, etapa, cc); CHECK 1 ≤ cardinalidade(valores) ≤ 4 | D-050, D-055 |
| Corte | crescente e dentro de 0..escala_max: validado no `clean()` (CHECK não lê outra tabela) | D-055 |
| Projeto | UNIQUE (parceiro, ano) WHERE NOT arquivado | D-047, D-068 |
| ProjetoBloco | UNIQUE (projeto, bloco); bloco precisa ser do texto_modelo do projeto (`clean()`) | D-062 |
| ProjetoIntervaloMinimo / ProjetoCor | UNIQUE (projeto, etapa, cc) / (projeto, padrao) | D-053, D-060 |
| Bloqueio | CHECK exatamente um alvo; UNIQUE parcial em cada alvo | D-081 |
| Histórico | `django-simple-history` em todos os modelos editáveis | D-082 |

## O que não vira tabela

- **Grupo de corte:** calculado na exportação (ordenar listas distintas de `valores` por aba e numerar). D-049, D-056.
- **Etapas avaliadas pelo parceiro:** existem `Corte` para parceiro × ano × etapa × CC. D-049.
- **Padrão de cada tarefa:** calculado na renderização com os cortes do parceiro; cruzou corte → padrão da âncora maior. D-058.
- **Perfis:** `Group` do Django (Admin, Pedagógica, Impresso, Mídias Digitais). D-073, D-083.
- **"Validado" e "mudou para o impresso":** comparação da revista resolvida atual com `hash_validado` e com a última `FotoRevista`. Qualquer caminho (matriz, texto, corte, cor, nome) invalida sozinho, sem sinalização por tabela. D-074, D-077, D-078.

## Decidido depois do rascunho

1. Ao abrir um ano novo, os projetos **não** são clonados: renascem pela cascata dos cortes com "PARCEIRO - NOME DO PROJETO". D-085.
2. `Etapa`, `ComponenteCurricular` e `CorPadrao` são **por ano** (clonados com o ano). D-086.
3. `ProjetoBloco` desatualizado (`versao_base` < `versao` do bloco) **não** bloqueia o "Validado": só avisa e fica marcado. D-087.
