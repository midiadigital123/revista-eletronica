import {
  cadernosDasDisciplinas,
  CORTES_PADRAO,
  FAIXA_PADRAO,
  Padrao,
  problemasDoAno,
  rotuloCaderno,
  type Ano,
  type AnoProjeto,
  type Caderno,
  type CadernoProjeto,
  type AtualizarAnoEntrada,
  type AtualizarDescritorEntrada,
  type AtualizarProjetoEntrada,
  type CriarAnoEntrada,
  type CriarProjetoEntrada,
  type Descritor,
  type LinhaEscala,
  type PaginaPatch,
  type Revista,
} from "../../contrato/schemas.js";
import { anosDaRevista, revistaDosAnos } from "../../contrato/revista.js";
import { conflito, naoEncontrado, problemasInvalidos, requisicaoInvalida } from "../../errors.js";
import { novoBloqueio, type Editor } from "../bloqueio/service.js";
import { copiarImagens } from "../imagens/service.js";
import { ProjetoModel, type ProjetoDb } from "./model.js";
import {
  definirCampoPagina,
  excluirProjeto,
  listarProjetos,
  obterProjeto,
  paraCadernos,
  paraPagina,
  paraProjeto,
  paraResumo,
  removerCampoPagina,
} from "./repository.js";

// ---------- projeto

export const listar = async () => (await listarProjetos()).map(paraResumo);

export const obter = async (slug: string) => paraProjeto(await obterProjeto(slug));

export async function exportarRevista(slug: string, caderno: Caderno): Promise<Revista> {
  const projeto = await obterProjeto(slug);
  return revistaDosAnos(acharCaderno(paraCadernos(projeto), caderno).anos, paraPagina(projeto));
}

async function exigirSlugLivre(slug: string): Promise<void> {
  if (await ProjetoModel.exists({ slug }))
    throw conflito("Já existe um projeto com esse identificador", "slug");
}

const anoVazio = (ano: Ano): AnoProjeto => ({
  ano,
  scaleRange: { ...FAIXA_PADRAO },
  cortes: { ...CORTES_PADRAO },
  descritores: [],
});

/** Textos importados: "" e [] equivalem a ausente (como no PaginaPatch). */
const textosPreenchidos = (pagina: Record<string, string | string[] | undefined>) =>
  Object.fromEntries(
    Object.entries(pagina).filter(
      (e): e is [string, string | string[]] => e[1] !== undefined && e[1].length > 0,
    ),
  );

/** Cadernos das disciplinas marcadas, preenchidos conforme a origem. */
async function conteudoDaOrigem({
  disciplinas,
  origem,
}: CriarProjetoEntrada): Promise<Pick<ProjetoDb, "cadernos" | "pagina">> {
  const ids = cadernosDasDisciplinas(disciplinas);
  switch (origem.tipo) {
    case "vazio": {
      const anos = [...new Set(origem.anos)];
      return { cadernos: ids.map((id) => ({ id, anos: anos.map(anoVazio) })), pagina: {} };
    }
    case "importar": {
      const revistas = ids.map((id) => {
        const revista = origem.cadernos[id];
        if (!revista)
          throw requisicaoInvalida(`Falta a revista de ${rotuloCaderno(id)}`, {
            campo: `origem.cadernos.${id}`,
          });
        return { id, revista };
      });
      const cadernos = revistas.map(({ id, revista }) => ({ id, anos: anosDaRevista(revista) }));
      const problemas = cadernos.flatMap(({ id, anos }) =>
        anos.flatMap((a) =>
          problemasDoAno(a).map((p) => ({ ...p, campo: `${id}.${a.ano}.${p.campo}` })),
        ),
      );
      if (problemas.length) throw problemasInvalidos(problemas);
      // Página é uma só: vem da primeira revista que a traz.
      const pagina = revistas.find(({ revista }) => revista.pagina)?.revista.pagina ?? {};
      return { cadernos, pagina: textosPreenchidos(pagina) };
    }
    case "copiar": {
      const fonte = await obterProjeto(origem.de);
      const daFonte = paraCadernos(fonte);
      const cadernos = ids.map((id) => {
        const c = daFonte.find((x) => x.id === id);
        if (!c)
          throw requisicaoInvalida(`O projeto de origem não tem ${rotuloCaderno(id)}`, {
            campo: "disciplinas",
          });
        return c;
      });
      // copiarImagens devolve a mesma página, com novos arquivoId nas imagens.
      const pagina = await copiarImagens(fonte.pagina);
      return { cadernos, pagina };
    }
  }
}

/** Cria o projeto já bloqueado para quem o criou. */
export async function criar(entrada: CriarProjetoEntrada, editor: Editor) {
  await exigirSlugLivre(entrada.slug);
  const conteudo = await conteudoDaOrigem(entrada);
  const projeto = await ProjetoModel.create({
    slug: entrada.slug,
    nome: entrada.nome,
    ...conteudo,
    bloqueio: novoBloqueio(editor),
  });
  return paraProjeto(projeto);
}

export async function atualizar(slug: string, entrada: AtualizarProjetoEntrada) {
  const projeto = await obterProjeto(slug);
  if (entrada.slug !== undefined && entrada.slug !== projeto.slug) {
    await exigirSlugLivre(entrada.slug);
    projeto.slug = entrada.slug;
  }
  if (entrada.nome !== undefined) projeto.nome = entrada.nome;
  await projeto.save();
  return paraProjeto(projeto);
}

export const excluir = async (slug: string) => excluirProjeto(await obterProjeto(slug));

// ---------- página (textos)

export async function atualizarPagina(slug: string, patch: PaginaPatch) {
  const projeto = await obterProjeto(slug);
  for (const [chave, valor] of Object.entries(patch)) {
    if (valor === undefined) continue;
    if (valor === null || valor.length === 0) removerCampoPagina(projeto, chave);
    else definirCampoPagina(projeto, chave, valor);
  }
  await projeto.save();
  return paraPagina(projeto);
}

// ---------- cadernos e anos

function acharCaderno(cadernos: CadernoProjeto[], id: Caderno): CadernoProjeto {
  const alvo = cadernos.find((c) => c.id === id);
  if (!alvo) throw naoEncontrado("Caderno");
  return alvo;
}

function validarAno(ano: AnoProjeto): void {
  const problemas = problemasDoAno(ano);
  if (problemas.length) throw problemasInvalidos(problemas);
}

function acharAno(anos: AnoProjeto[], ano: Ano): AnoProjeto {
  const alvo = anos.find((a) => a.ano === ano);
  if (!alvo) throw naoEncontrado("Ano");
  return alvo;
}

/**
 * Carrega o projeto, aplica `editar` no ano do caderno, valida o ano inteiro com
 * problemasDoAno e grava. Devolve o que `editar` devolver.
 */
async function editarAno<T>(
  slug: string,
  caderno: Caderno,
  ano: Ano,
  editar: (alvo: AnoProjeto) => T,
): Promise<T> {
  const projeto = await obterProjeto(slug);
  const cadernos = paraCadernos(projeto);
  const alvo = acharAno(acharCaderno(cadernos, caderno).anos, ano);
  const resultado = editar(alvo);
  validarAno(alvo);
  projeto.cadernos = cadernos;
  await projeto.save();
  return resultado;
}

export async function criarAno(slug: string, caderno: Caderno, entrada: CriarAnoEntrada) {
  const projeto = await obterProjeto(slug);
  const cadernos = paraCadernos(projeto);
  const { anos } = acharCaderno(cadernos, caderno);
  if (anos.some((a) => a.ano === entrada.ano))
    throw conflito("Esse ano já existe no caderno", "ano");
  const novo: AnoProjeto = { ...entrada, descritores: [] };
  validarAno(novo);
  anos.push(novo);
  projeto.cadernos = cadernos;
  await projeto.save();
  return novo;
}

export const atualizarAno = (
  slug: string,
  caderno: Caderno,
  ano: Ano,
  entrada: AtualizarAnoEntrada,
) => editarAno(slug, caderno, ano, (alvo) => Object.assign(alvo, entrada));

export async function excluirAno(slug: string, caderno: Caderno, ano: Ano): Promise<void> {
  const projeto = await obterProjeto(slug);
  const cadernos = paraCadernos(projeto);
  const alvo = acharCaderno(cadernos, caderno);
  acharAno(alvo.anos, ano);
  if (alvo.anos.length === 1) throw requisicaoInvalida("O caderno precisa ter ao menos um ano");
  alvo.anos = alvo.anos.filter((a) => a.ano !== ano);
  projeto.cadernos = cadernos;
  await projeto.save();
}

// ---------- descritores

function acharDescritor(ano: AnoProjeto, codigo: string): Descritor {
  const d = ano.descritores.find((x) => x.codigo === codigo);
  if (!d) throw naoEncontrado("Descritor");
  return d;
}

function exigirCodigoLivre(ano: AnoProjeto, codigo: string): void {
  if (ano.descritores.some((d) => d.codigo === codigo))
    throw conflito("Já existe um descritor com esse código no ano", "codigo");
}

export const criarDescritor = (slug: string, caderno: Caderno, ano: Ano, descritor: Descritor) =>
  editarAno(slug, caderno, ano, (alvo) => {
    exigirCodigoLivre(alvo, descritor.codigo);
    alvo.descritores.push(descritor);
    return descritor;
  });

export const atualizarDescritor = (
  slug: string,
  caderno: Caderno,
  ano: Ano,
  codigo: string,
  { bncc, ...campos }: AtualizarDescritorEntrada,
) =>
  editarAno(slug, caderno, ano, (alvo) => {
    const d = acharDescritor(alvo, codigo);
    if (campos.codigo !== undefined && campos.codigo !== codigo)
      exigirCodigoLivre(alvo, campos.codigo);
    Object.assign(d, campos);
    if (bncc) d.bncc = { ...d.bncc, ...bncc };
    return d;
  });

export const excluirDescritor = (slug: string, caderno: Caderno, ano: Ano, codigo: string) =>
  editarAno(slug, caderno, ano, (alvo) => {
    const d = acharDescritor(alvo, codigo);
    alvo.descritores.splice(alvo.descritores.indexOf(d), 1);
  });

/** Substitui um padrão inteiro da escala. `linhas` já vem ordenada (LinhasPadrao). */
export async function salvarEscala(
  slug: string,
  caderno: Caderno,
  ano: Ano,
  codigo: string,
  padrao: string,
  linhas: LinhaEscala[],
) {
  const p = Padrao.safeParse(padrao);
  if (!p.success) throw naoEncontrado("Padrão");
  return editarAno(slug, caderno, ano, (alvo) => {
    acharDescritor(alvo, codigo).scale[p.data] = linhas;
    return linhas;
  });
}
