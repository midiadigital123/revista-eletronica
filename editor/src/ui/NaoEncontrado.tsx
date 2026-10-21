import { FileQuestion } from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import { Empty, EmptyContent, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";

export function NaoEncontrado() {
  return (
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <FileQuestion />
        </EmptyMedia>
        <EmptyTitle>
          <h1>Página não encontrada</h1>
        </EmptyTitle>
      </EmptyHeader>
      <EmptyContent>
        <Button asChild variant="outline">
          <Link to="/projetos">Voltar aos projetos</Link>
        </Button>
      </EmptyContent>
    </Empty>
  );
}
