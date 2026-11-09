"""Geometria do infográfico do F2, medida no desenho em uso (tests/fixtures/f2-lp.svg).

O desenho está em templates/revista/f2.svg; aqui ficam só os números que o gerador precisa para
posicionar os blocos e as linhas das tabelas. Coordenadas no viewBox 0 0 1190.6 793.7.
"""

# Caixa de cada bloco (x, y, largura, altura); x e y são o translate do <g id="f2-<bloco>">.
CAIXA = {
    "cabecalho": (43, 85, 335, 56),
    "descritor": (252, 196, 164, 164),
    "habilidades": (661, 69, 468, 480),
    "progressao": (661, 589, 455, 162),
    "tarefas": (64, 463, 436, 254),
}
# Reflow: por coluna, os blocos ligados empilham a partir do primeiro y, com o gap do desenho.
COLUNAS = {"esquerda": (["descritor", "tarefas"], 103), "direita": (["habilidades", "progressao"], 40)}
# I, A, C, R: os azuis da legenda do desenho (do mais claro ao mais escuro).
CORES_MARCA = {"I": "#e6f6fb", "A": "#a9ffff", "C": "#08b4d7", "R": "#006991"}

# Tabela do referencial (bloco habilidades, coordenadas locais): y da 1ª linha e a altura de cada
# etapa, 1EF a 3EM. ponytail: alturas do desenho de LP; texto mais longo é cortado pelo line-clamp.
TABELA_Y = 64.8
ALTURAS_LINHAS = (22.7, 22.6, 22.7, 22.7, 22.7, 39.7, 39.6, 25.6, 25.5, 39.7, 39.6, 39.7)
# Progressão (bloco progressao, local): x da 1ª coluna e largura de cada etapa.
PROGRESSAO_X = 19.3
PROGRESSAO_PASSO = 37.3
