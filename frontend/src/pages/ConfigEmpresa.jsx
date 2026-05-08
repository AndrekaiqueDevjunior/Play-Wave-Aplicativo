import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Save, Building2, Users, Upload } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "@/components/ui/use-toast";

export default function ConfigEmpresa() {
  const { toast } = useToast();
  const [form, setForm] = useState({
    company_name: "Minha Empresa Ltda",
    cnpj: "12.345.678/0001-99",
    responsible: "João Silva",
    email: "joao@empresa.com",
    phone: "(11) 99999-9999",
    primary_color: "#2563eb",
  });

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
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nome da Empresa</Label>
                  <Input
                    value={form.company_name}
                    onChange={(e) =>
                      setForm({ ...form, company_name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>CNPJ</Label>
                  <Input
                    value={form.cnpj}
                    onChange={(e) => setForm({ ...form, cnpj: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Responsável</Label>
                  <Input
                    value={form.responsible}
                    onChange={(e) =>
                      setForm({ ...form, responsible: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>E-mail</Label>
                  <Input
                    value={form.email}
                    onChange={(e) =>
                      setForm({ ...form, email: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Telefone</Label>
                  <Input
                    value={form.phone}
                    onChange={(e) =>
                      setForm({ ...form, phone: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cor Principal</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={form.primary_color}
                      onChange={(e) =>
                        setForm({ ...form, primary_color: e.target.value })
                      }
                      className="w-12 h-10 p-1 cursor-pointer"
                    />
                    <Input
                      value={form.primary_color}
                      onChange={(e) =>
                        setForm({ ...form, primary_color: e.target.value })
                      }
                      className="font-mono"
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Logo da Empresa</Label>
                <div className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors">
                  <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Clique para enviar ou arraste
                  </p>
                  <p className="text-xs text-muted-foreground">
                    PNG, SVG. Max 2MB
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={() => toast({ title: "Configurações salvas!" })}
                >
                  <Save className="w-4 h-4 mr-2" />
                  Salvar
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
