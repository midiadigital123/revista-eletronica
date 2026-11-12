# Proposta de nova UI/UX do Revista Express (demo clicável)

Demo estática de uma **nova navegação e de um novo visual** para as telas B do sistema. Só UI e UX: dados **100% fictícios**, a revista em si **não é montada**, e **nada em `app/` foi alterado** (D-267, K-041).

## Abrir

Abra `index.html` no navegador (duplo clique ou `xdg-open index.html`). Não precisa de servidor, de Docker nem de internet. Tudo é relativo a esta pasta.

- **Ver como (demo)**, no rodapé da barra lateral: troca o perfil (Pedagógica, Mídias Digitais, Impresso, Admin). Muda a tela Hoje, os números da barra e deixa o Impresso em só leitura.
- **Ctrl K** (ou `/`): busca global por parceiro, revista, descritor, template.
- **Sobre esta proposta** (`sobre.html`): o diagnóstico em 10 achados, o antes e depois da navegação e a tabela "tela de hoje → tela proposta".
- **Estados** (`estados.html`): vazio, só leitura, bloqueio, impacto, "alterações não salvas", conflito de gravação.

## A ideia em uma frase

A **revista** anda numa **esteira de 5 fases** (Preparar → Montar → Conferir → Validada → Impressa), desenhada como uma régua de 5 trechos; a navegação segue a esteira (Hoje, Revistas, Parceiros, Entrega, Biblioteca) e cada tela diz o que falta e qual é o próximo clique. As fases saem de dados que já existem (pendências, Validado, foto do impresso): nenhuma regra de negócio nova.

## Gerar e verificar

```bash
python3 gerar.py                 # escreve todos os .html ao lado deste arquivo (só stdlib)
python3 gerar.py --lista         # lista as páginas
python3 verificar_links.py       # links, âncoras, <dialog> e abas; imprime OK
NODE_PATH=/home/otavio.peres/dev/revista-express/app/e2e/node_modules node verificar.cjs .   # PNGs em _shots/ (1440 e 390 px) + erros de console
```

Estrutura: `dados.py` (dados inventados) · `paginas/shell.py` (casca e componentes) · `paginas/*.py` (uma tela ou grupo de telas por módulo) · `app.css` e `app.js` (um arquivo cada, sem build) · `fontes/` (Inter, copiada de `app/nucleo/static/ui/fontes/`).

## Sistema visual (o que a demo propõe; não é o `DESIGN.md` do projeto)

- **Mundo:** régua de proficiência. Barra lateral tinta (azul-grafite), canvas cinza-frio, cartões brancos, **um** acento cobalto (ação primária, foco, "você está aqui").
- **Régua das fases:** 5 trechos numa rampa fixa de cobalto, o último em verde (`--r1` a `--r5`). É o elemento-assinatura: aparece na tela Hoje (a temporada), nas tabelas, nos cartões e no stepper.
- **Cor de estado:** verde = pronto, âmbar = pendência, vermelho = erro ou perigo.
- **Cores dos Padrões 01–05:** são dado do produto e só aparecem em `escala()` e nas telas de cortes e Padrões, nunca como decoração.
- **Tipografia:** Inter (a do repositório), números tabulares, sem fonte mono. Corpo de 14 px, tabela de 13 px.
- **Regras de ofício:** uma ação primária por tela; sem cartão dentro de cartão; sem fileira de cartões de métrica; sem emoji como ícone (conjunto único de ícones de traço 1,75 em `shell.py`); modal só para confirmação e impacto; impacto sempre mostrado **antes** do clique.

## Dados sintéticos

Parceiros, pessoas, cortes, variáveis, descritores, textos e datas vêm de `dados.py` e são inventados (Vale Verde, Serra Alta, Costa Dourada…). Os 4 Padrões usam os valores de cor padrão do sistema, que são dado público do produto. Os códigos e textos de descritores são plausíveis, não são os da matriz real.

## Limites

Nada grava: autosave, "Validar", "Marcar como impressa" e downloads são simulados (aviso passageiro). A revista e o preview são placeholders. O celular (390 px) cobre o essencial: barra em gaveta, tabelas rolando dentro da caixa.

## Se a direção for aprovada

Plano de implementação no Django em cinco fatias: (1) casca e navegação, (2) Revistas e Revista, (3) Parceiros, (4) Entrega, (5) Biblioteca. A tabela "tela de hoje → tela proposta" de `sobre.html` é o ponto de partida; as rotas antigas redirecionam para as novas.
