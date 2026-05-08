import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { listarPlanos } from "@/api/planos";

function formatPrice(plan) {
  if (!plan.price_brl) return "Sob consulta";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(plan.price_brl);
}

export default function Planos() {
  const { data: planos = [], isLoading, error } = useQuery({
    queryKey: ["plans"],
    queryFn: listarPlanos,
  });

  return (
    <div className="space-y-6">
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold">Planos</h2>
        <p className="text-muted-foreground mt-2">
          Gestão de planos disponível apenas para administradores da Play Wave.
        </p>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {error.message || "Não foi possível carregar os planos."}
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
        {isLoading && (
          <Card className="p-6 text-sm text-muted-foreground">Carregando planos...</Card>
        )}
        {!isLoading && planos.length === 0 && (
          <Card className="p-6 text-sm text-muted-foreground">
            Nenhum plano cadastrado.
          </Card>
        )}
        {planos.map((plano) => (
          <Card
            key={plano.id}
            className={cn(
              "relative overflow-hidden transition-shadow hover:shadow-lg",
              plano.is_popular && "border-primary shadow-md",
              !plano.is_active && "opacity-70",
            )}
          >
            {plano.is_popular && (
              <div className="absolute top-0 right-0">
                <Badge className="rounded-none rounded-bl-lg bg-primary text-primary-foreground">
                  Mais popular
                </Badge>
              </div>
            )}
            {!plano.is_active && (
              <div className="absolute top-0 right-0">
                <Badge variant="outline" className="rounded-none rounded-bl-lg bg-background">
                  Inativo
                </Badge>
              </div>
            )}
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-lg">{plano.name}</CardTitle>
              <p className="text-sm text-muted-foreground">{plano.description}</p>
              <div className="mt-4">
                <span className="text-4xl font-bold">{formatPrice(plano)}</span>
                {plano.price_brl > 0 && <span className="text-muted-foreground">/mês</span>}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-3">
                {(plano.features || []).map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-primary shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
