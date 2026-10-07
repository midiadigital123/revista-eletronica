---
name: Editor da Revista Eletrônica
description: Ferramenta shadcn neutra e densa em que a escala de proficiência é a única coisa colorida da tela.
colors:
  primary: "oklch(0.205 0 0)"
  primary-foreground: "oklch(0.985 0 0)"
  padrao-1: "#f72628"
  padrao-2: "#ff8d43"
  padrao-3: "#b3ccff"
  padrao-4: "#0ed3ff"
  warning: "#7a4f00"
  warning-bg: "#fff3d6"
  destructive: "oklch(0.5 0.2 27.325)"
  background: "oklch(1 0 0)"
  foreground: "oklch(0.145 0 0)"
  muted: "oklch(0.97 0 0)"
  muted-foreground: "oklch(0.5 0 0)"
  border: "oklch(0.922 0 0)"
  input: "oklch(0.6 0 0)"
  ring: "oklch(0.45 0 0)"
typography:
  headline:
    fontFamily: "Inter Variable, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Inter Variable, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  subtitle:
    fontFamily: "Inter Variable, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.55
  body:
    fontFamily: "Inter Variable, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "Inter Variable, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.43
    fontFeature: "\"tnum\" 1"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "14px"
  pill: "26px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "6": "24px"
  "8": "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "36px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "36px"
  button-ghost-hover:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
  button-destructive:
    textColor: "{colors.destructive}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "36px"
  input:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "4px 10px"
    height: "36px"
  badge-warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"
    height: "20px"
  alert-warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
  nav-link-active:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "6px 12px"
---

# Design System: Editor da Revista Eletrônica

Escopo: o editor em `editor/src`. A revista pública (`revista/`, `escala.html`, `styles.css`) é outra identidade e não segue este sistema; a única coisa que os dois compartilham são as cores dos Padrões 01–04.

## Overview

**Creative North Star: "A Bancada Neutra"**

Uma ferramenta de trabalho familiar: o preset shadcn bIkeymG (estilo radix-vega, base neutral, Inter, ícones lucide, raio padrão) aplicado sem customização de forma. Neutros puros, primário quase preto, densidade de formulário. A tela não tem atmosfera própria de propósito; quem dá cor e organização é o dado: as quatro faixas da escala de proficiência.

A personalidade está nos detalhes funcionais, não em decoração: algarismos tabulares em toda a interface, o modo (Editando / Somente leitura) sempre visível num selo, o estado do salvamento com troca suave por estado, itens novos que entram com um deslocamento curto e recebem foco. Os tokens de contraste foram escurecidos em relação ao preset para passar AA (anel de foco, borda de campo, texto secundário, destructive).

O sistema recusa a cara "feita por IA" anterior: fundo bege de papel, verde-escuro, mono decorativo, sobrescritos espaçados em caixa alta. Recusa também a direção Cartão-resposta, reprovada pelo usuário.

**Key Characteristics:**
- Componentes shadcn com a forma do preset; customização só em tokens de cor e variantes de estado.
- Cor apenas nos Padrões 01–04, no âmbar de aviso e no destructive.
- Inter em todos os papéis, algarismos tabulares globais, nenhuma fonte mono.
- Plano: profundidade por borda e anel, sombra só a `shadow-xs` do preset.
- Movimento curto (120/180ms) com uma única curva de saída, desligado em reduced-motion.

## Colors

Paleta neutra de cinzas sem matiz, com quatro cores de dado e duas cores de estado.

### Primary
- **Grafite** (primary): botão primário, aba ativa (sublinhado de 2px), selo "Editando", fio indicador do descritor selecionado, seleção de texto e `accent-color` nativo.

### Secondary
- **Padrões 01–04** (padrao-1 vermelho, padrao-2 laranja, padrao-3 azul-lavanda, padrao-4 ciano): dado do produto, idênticos aos da revista publicada. Aparecem só na tarja de 6px de cada bloco da legenda de cortes e no cabeçalho de cada bloco da escala (texto em foreground sobre a cor cheia). Existem variantes de fundo a 10% (`padrao-N-bg`) definidas no tema.

### Tertiary
- **Âmbar de Aviso** (warning sobre warning-bg, 6.5:1): bloqueio de edição por outra pessoa, nível fora do padrão, selos de aviso na lista de projetos. Usado via `Alert` e `Badge` na variante `warning`.
- **Vermelho de Erro** (destructive, 6.7:1 sobre branco): botões de excluir em tom suave (fundo destructive a 10%, 20% no hover), texto de erro de campo, alerta de erro, status "Erro" do salvamento.

### Neutral
- **Branco** (background): fundo de página, cards, popovers e campos.
- **Quase Preto** (foreground): texto principal.
- **Cinza Névoa** (muted): hover de linha e link de navegação ativo, fundo de miniatura.
- **Cinza Legível** (muted-foreground, 6.0:1): texto de apoio, links de navegação inativos, contadores, status "Salvo às HH:MM".
- **Fio** (border): divisores, bordas de card, bloco e tabela.
- **Borda de Campo** (input, 3.9:1): contorno de inputs e textareas.
- **Anel** (ring, 7.4:1): foco visível e pulso de autosave.

### Named Rules
**The Escala Colorida Rule.** Fora dos Padrões 01–04, do âmbar e do destructive, nada na tela tem matiz. Uma cor nova é uma pergunta para o usuário, não uma decisão de tela.

**The Padrões Intocáveis Rule.** Os quatro valores dos padrões são dado publicado: não clareie, não escureça, não troque por tokens do preset. Se precisar de contraste, ponha texto foreground sobre a cor, como no cabeçalho da escala.

## Typography

**Display Font:** Inter Variable (auto-hospedada via @fontsource, com sans-serif)
**Body Font:** Inter Variable
**Label/Mono Font:** nenhuma; não há fonte mono.

**Character:** Uma família só, hierarquia por tamanho e peso 600. Algarismos tabulares ligados no `html` para que níveis, cortes, contadores e códigos D01–D40 alinhem em coluna.

### Hierarchy
- **Headline** (600, 30px, tracking -0.025em): h1 de todas as telas (Projetos, projeto, Usuários).
- **Title** (600, 20px, tracking -0.025em): h2 de seção (ano, página do projeto). O código do descritor usa 24px/600 como título da tela do descritor.
- **Subtitle** (600, 18px): h3 das seções do formulário do descritor.
- **Body** (400, 14px): texto de interface, tabelas, alertas, diálogos. Campos usam 16px no celular e 14px a partir de md.
- **Label** (500, 14px): rótulos de campo, botões, abas, links de navegação. Selos usam 12px/500.

### Named Rules
**The Tabular Rule.** Todo número é tabular (`tabular-nums` global, reforçado em campos de nível e corte). Alinhamento numérico vem do recurso da Inter, nunca de uma fonte mono.

**The Sem Sobrescrito Rule.** Nenhum rótulo pequeno em caixa alta e espaçado acima de títulos. Títulos falam por si; contexto vai no breadcrumb.

## Layout

Contêiner único da área autenticada: largura máxima de 1280px centralizada, 24px de margem lateral, 32px de respiro vertical. Barra superior com borda inferior: nome do sistema em 600, navegação Projetos/Usuários, usuário e Sair à direita.

Ritmo de espaço da escala do Tailwind, usado em degraus fechados: 4, 8, 12, 16, 24, 32px. Pilhas de seção em 24px; grupos de campo em 12–16px; ações em linha a 8px.

Tela do ano: legenda de cortes em quatro blocos iguais (2 colunas abaixo de md, 4 a partir de md). Abaixo, grade de duas colunas a partir de lg: lista de descritores de 20rem, fixa (sticky) com rolagem própria, e o descritor à direita. Abaixo de lg a lista vira um botão recolhível, que começa fechado quando há descritor aberto. Abas de ano roláveis na horizontal. Páginas de formulário limitadas a 48rem.

## Elevation & Depth

Sistema plano. Separação por borda (border) e anel de 1px em foreground a 10% (cards e diálogos). A única sombra é a `shadow-xs` do preset em campos, botões outline e cards. O overlay de diálogo é preto a 10% com desfoque leve.

### Shadow Vocabulary
- **Sombra de repouso** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)`): campos, botão outline, card. Herdada do preset.
- **Pulso de salvo** (anel de 0 a 3px na cor ring, 360ms): keyframe definido para confirmar autosave num campo.

### Named Rules
**The Flat Rule.** Nenhuma sombra nova. Hierarquia vem de borda, fundo muted e peso tipográfico.

## Shapes

Cantos suaves do preset sobre um raio base de 10px: campos e botões em 8px (botões pequenos até 10px, ícones pequenos idem), blocos, alertas e tabelas em 10px, cards e diálogos em 14px, selos em pílula. Tarjas de padrão são barras de 6px com pontas arredondadas. Indicador de seleção na lista de descritores é um fio vertical de 1px em primary.

**The Forma do Preset Rule.** Não altere raio, altura ou padding dos componentes shadcn. Customização entra por variante (`warning` em Alert e Badge) e por token de cor.

## Components

Componentes de `editor/src/components/ui` (shadcn, gerados pelo CLI) consumidos por fachadas em português em `editor/src/ui`.

### Buttons
- **Shape:** cantos suaves (8px), altura 36px; `sm` 32px, usado nas ações de cabeçalho.
- **Primary:** grafite com texto quase branco, hover a 80%. Uma ação primária por cabeçalho ("Gerar pacote .zip").
- **Outline:** fundo branco, borda fio, hover muted. Ação padrão da fachada `Botao` (variante `secundario`).
- **Ghost:** sem fundo, hover muted; fechar de diálogo e ações de linha.
- **Destructive:** tom suave (vermelho a 10%, texto vermelho), isolado à direita com `ml-auto` quando divide linha com outras ações.
- **Focus:** borda e anel de 3px na cor ring. Ativo desce 1px.
- **Fachada `Botao`:** variantes `primario | secundario | perigo | fantasma`, tamanhos `md | sm`, `type="button"` por padrão.

### Chips
- **Selos (Badge):** pílula de 20px, 12px/500. Modo: "Editando" (default), "Somente leitura" (secondary), "Conectando…" (outline). Aviso na variante `warning`.

### Cards / Containers
- **Corner Style:** 14px (Card do login), 10px nos blocos da escala, da legenda e na tabela de usuários.
- **Background:** branco.
- **Shadow Strategy:** ver Elevation; plano.
- **Border:** fio de 1px.
- **Internal Padding:** 24px no Card; 12px nos blocos da legenda; 16px no corpo do bloco da escala.

### Inputs / Fields
- **Style:** contorno input (3.9:1), fundo transparente, 8px de raio, 36px de altura.
- **Focus:** borda e anel de 3px na cor ring.
- **Error / Disabled:** `aria-invalid` troca a borda para destructive com anel a 20%; mensagem em `FieldError` ligada por `aria-describedby`. Desabilitado a 50% de opacidade.
- **Fachadas `CampoTexto` / `AreaTexto`:** rótulo obrigatório, `erro` e `ajuda` acessíveis, compatíveis com `register()`.
- **Modo leitura:** os formulários ficam dentro de `<fieldset disabled>` nativo; fora do modo edição todos os controles se desabilitam de uma vez.

### Navigation
- **Barra principal:** links 14px/500, 6px×12px, cantos 8px; ativo em muted com texto foreground, inativo em muted-foreground.
- **Abas de ano:** sublinhado de 2px em primary na ativa, transparente nas demais, rolagem horizontal.
- **Breadcrumb** do shadcn acima do h1 do projeto.

### Aviso
Fachada sobre `Alert`: tons `info` (default), `alerta` (warning) e `erro` (destructive), com ícone lucide e ação opcional à direita. `erro` usa `role="alert"`, os demais `role="status"`.

### Dialogo / Confirmacao
`Dialog` do Radix, nunca `AlertDialog`. Título é o nome acessível; fechar fica por último no DOM para o foco inicial cair no primeiro campo; o foco volta a quem abriu (ou a `focoAoFechar` se quem abriu sumiu). `bloqueado` (Dialogo) e `pendente` (Confirmacao) impedem Esc, clique fora e o X durante o envio. Confirmacao: Cancelar (outline) e confirmar (destructive com spinner quando pendente).

### Indicador de salvamento
Selo de modo + status ao lado do h1 do projeto: "Salvando…" com spinner, "Salvo às HH:MM" com check, "Erro" em destructive. Cada troca de estado entra com fade de 180ms.

### Bloco da escala
Seção com borda e cantos de 10px; cabeçalho na cor cheia do padrão com nome e intervalo de nível (tabular); linhas em grade `6rem | texto | ação`, nível alinhado à direita em 16px/600. Linha nova entra com `animate-entra` (120ms) e recebe foco.

## Do's and Don'ts

### Do:
- **Do** usar os componentes shadcn com a forma do preset e as fachadas de `editor/src/ui` para botão, campo, aviso e diálogo.
- **Do** restringir cor aos Padrões 01–04, ao âmbar de aviso (#7a4f00 sobre #fff3d6) e ao destructive.
- **Do** manter algarismos tabulares em todo número e Inter em todos os papéis.
- **Do** envolver formulários editáveis em `<fieldset disabled>` ligado ao modo.
- **Do** manter os rótulos e papéis acessíveis que os testes fixam; mudar um rótulo é mudar o teste junto.
- **Do** animar só com `ease-saida` em 120ms (entrada) ou 150–180ms (estado), e deixar o reduced-motion global cortar tudo.

### Don't:
- **Don't** customizar raio, altura ou padding dos componentes shadcn.
- **Don't** usar fonte mono, nem para números ou códigos.
- **Don't** pôr sobrescrito (eyebrow) em caixa alta espaçada acima de títulos.
- **Don't** usar `AlertDialog`; confirmações usam `Dialog` via `Confirmacao`.
- **Don't** usar fundo bege de papel, verde-escuro ou qualquer cor de marca inventada.
- **Don't** aplicar o visual da revista pública ao editor, nem o deste sistema à revista.
