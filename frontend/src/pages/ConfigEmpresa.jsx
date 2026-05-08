import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, Save, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/use-toast";
import { atualizarMinhaEmpresa, buscarMinhaEmpresa } from "@/api/tenants";

export default function ConfigEmpresa() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    contact_email: "",
    max_devices: 0,
    notes: "",
  });

  const { data: tenant, isLoading, error } = useQuery({
    queryKey: ["tenant-me"],
    queryFn: buscarMinhaEmpresa,
  });

  useEffect(() => {
    if (!tenant) return;
    setForm({
      name: tenant.name || "",
      contact_email: tenant.contact_email || "",
      max_devices: tenant.max_devices || 0,
      notes: tenant.notes || "",
    });
  }, [tenant]);

  const mutation = useMutation({
    mutationFn: atualizarMinhaEmpresa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant-me"] });
      toast({ title: "Dados da empresa salvos!" });
    },
    onError: (err) => {
      toast({
        variant: "destructive",
        title: "Erro ao salvar empresa",
        description: err.message || "Tente novamente.",
      });
    },
  });

  const set = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Configurações</h2>

      <Tabs defaultValue="company">
        <TabsList>
          <TabsTrigger value="company">
            <Building2 className="w-4 h-4 mr-2" />
            Empresa
          </TabsTrigger>
          <TabsTrigger value="users" asChild>
            <Link to="/configuracoes/usuarios">
              <Users className="w-4 h-4 mr-2" />
              Usuários
            </Link>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="company" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dados da Empresa</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                  {error.message || "Não foi possível carregar os dados da empresa."}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nome da Empresa</Label>
                  <Input
                    value={form.name}
                    disabled={isLoading}
                    onChange={(e) => set("name", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>E-mail de Contato</Label>
                  <Input
                    type="email"
                    value={form.contact_email}
                    disabled={isLoading}
                    onChange={(e) => set("contact_email", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Plano Atual</Label>
                  <Input value={tenant?.plan || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Limite de Dispositivos</Label>
                  <Input
                    type="number"
                    min="0"
                    value={form.max_devices}
                    disabled={isLoading}
                    onChange={(e) => set("max_devices", Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Observações</Label>
                <Textarea
                  value={form.notes}
                  disabled={isLoading}
                  onChange={(e) => set("notes", e.target.value)}
                  rows={4}
                />
              </div>

              <div className="flex justify-end">
                <Button
                  disabled={mutation.isPending || isLoading}
                  onClick={() => mutation.mutate(form)}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {mutation.isPending ? "Salvando..." : "Salvar"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
