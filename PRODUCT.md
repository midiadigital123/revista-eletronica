# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Equipe interna da Fundação CAEd, em dois perfis:
- **Pedagógico:** especialistas que escrevem, descritor por descritor (D01–D40), o tópico, a descrição, os pré-requisitos, a BNCC e as linhas da escala de proficiência de cada ano (5º EF, 9º EF, 3ª EM). São sessões longas de digitação, em desktop.
- **Design:** quem confere a revista no preview e gera o pacote .zip entregue.

## Product Purpose
Editor que monta revistas eletrônicas de resultados de avaliação. Cada projeto tem uma página (título, introdução, imagem do topo) e anos. Cada ano tem uma faixa da escala, três cortes que dividem 4 padrões de desempenho e os descritores. A API renderiza a revista (`escala.html`) a partir desses dados para preview e para o zip offline. Sucesso é um texto pedagógico correto, sem perda de digitação, que chega na revista sem retrabalho.

## Positioning
O centro do produto é a escala de proficiência e seus descritores. Os 4 padrões são contíguos: o primeiro vai do mínimo até o corte 1, o seguinte começa no valor seguinte, e assim por diante. Cada habilidade é ancorada em um nível, e a leitura é cumulativa: todo aluno com nota maior ou igual ao nível domina aquela habilidade.

## Operating Context
- Só uma pessoa edita um projeto por vez. Há bloqueio com heartbeat; quem chega depois vê o projeto em somente leitura com o nome de quem edita.
- Cada campo salva sozinho ao sair dele (autosave no blur). O cabeçalho do projeto mostra o estado do salvamento.
- Ações do projeto: renomear, preview, gerar pacote .zip, exportar JSON, excluir (vai para a lixeira).
- Perfis de acesso: admin (cadastra usuários) e editor.

## Capabilities and Constraints
- Stack: React 19 + Vite + Tailwind 4 + TanStack Query + react-hook-form/zod. Componentes de interface: shadcn/ui.
- Atrás de nginx com CSP. Fontes e recursos são auto-hospedados, sem CDN.
- Níveis da escala podem ser valores "quebrados" (não redondos).
- Sem dark mode por enquanto.

## Brand Commitments
- As cores dos Padrões 01–04 (`#f72628`, `#ff8d43`, `#b3ccff`, `#0ed3ff`) são dado do produto e precisam bater com a revista publicada.
- Base estrutural herdada das diretrizes do CMS interno: escalas fechadas de espaço e raio, foco de 2px, movimento de 120/180ms com `cubic-bezier(0.16, 1, 0.3, 1)` e `prefers-reduced-motion` respeitado. Cor e tipografia são próprias do editor.
- O usuário rejeita o visual "morno, com cara de feito por IA". Isso inclui fontes genéricas, mono decorativo, sobrescrito espaçado em caixa alta e fundo bege "papel".

## Evidence on Hand
- Dados reais de exemplo: `descritores.json` (raiz do repositório).
- Não há logo do editor nem manual de marca CAEd neste repositório. Nada disso deve ser inventado.

## Product Principles
1. Nenhum texto digitado se perde. O estado do salvamento está sempre visível.
2. O modo (editando ou somente leitura) nunca é ambíguo.
3. A escala é a protagonista. As cores dos padrões organizam a tela, não a enfeitam.
4. A ferramenta é familiar e densa onde a tarefa pede. Expressão fica nos detalhes.

## Accessibility & Inclusion
WCAG 2.x AA: contraste de 4.5:1 no texto, foco visível, teclado em todas as ações, papéis e rótulos acessíveis (fixados pelos testes).
