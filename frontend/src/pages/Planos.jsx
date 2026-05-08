import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const planos = [
  {
    name: "Inicial",
    price: "R$ 79",
    period: "/mês",
    description: "Ideal para começar",
    features: [
      "Até 3 TVs",
      "Biblioteca básica",
      "Relatórios simples",
      "1 usuário",
      "Suporte por e-mail",
    ],
    popular: false,
  },
  {
    name: "Profissional",
    price: "R$ 199",
    period: "/mês",
    description: "Para equipes em crescimento",
    features: [
      "Até 20 TVs",
      "Campanhas ilimitadas",
      "Agendamento avançado",
      "Relatórios completos",
      "Até 5 usuários",
      "Suporte prioritário",
      "Editor de playlist",
    ],
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Sob consulta",
    period: "",
    description: "Para grandes operações",
    features: [
      "TVs ilimitadas",
      "Multiunidade",
      "Suporte prioritário",
      "White label",
      "Usuários ilimitados",
      "API de integração",
      "SLA dedicado",
      "Gerente de conta",
    ],
    popular: false,
  },
];

export default function Planos() {
  return (
    <div className="space-y-6">
      <div className="text-center max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold">Escolha seu plano</h2>
        <p className="text-muted-foreground mt-2">
          Escale sua operação de Digital Signage com o plano ideal para sua
          empresa
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {planos.map((plano) => (
          <Card
            key={plano.name}
            className={cn(
              "relative overflow-hidden transition-shadow hover:shadow-lg",
              plano.popular && "border-primary shadow-md",
            )}
          >
            {plano.popular && (
              <div className="absolute top-0 right-0">
                <Badge className="rounded-none rounded-bl-lg bg-primary text-primary-foreground">
                  Mais popular
                </Badge>
              </div>
            )}
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-lg">{plano.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {plano.description}
              </p>
              <div className="mt-4">
                <span className="text-4xl font-bold">{plano.price}</span>
                <span className="text-muted-foreground">{plano.period}</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-3">
                {plano.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-primary shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Button
                className="w-full"
                variant={plano.popular ? "default" : "outline"}
              >
                {plano.price === "Sob consulta"
                  ? "Falar com vendas"
                  : "Selecionar plano"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
