/** Marcador de tela ainda não implementada (removido pelos donos de cada módulo). */
export function EmConstrucao({ titulo }: { titulo: string }) {
  return (
    <section className="p-8">
      <h1 className="text-2xl">{titulo}</h1>
      <p className="text-tinta-suave mt-2">Em construção.</p>
    </section>
  );
}
