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
import {
  atualizarConfigAudioEmpresa,
  atualizarMinhaEmpresa,
  atualizarOSDConfigEmpresa,
  buscarMinhaEmpresa,
} from "@/api/tenants";
import { AudioPolicySelector } from "@/components/shared/AudioPolicySelector";
import { OSDConfigForm } from "@/components/shared/OSDConfigForm";
import { OSDConfigPreview, normalizeOSDConfig } from "@/components/shared/OSDConfigPreview";

export default function ConfigEmpresa() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    contact_email: "",
    max_devices: 0,
    notes: "",
  });
  const [osdForm, setOsdForm] = useState({
    show_current_audio: true,
    position: "top_right",
    duration_seconds: 8,
    opacity: 0.6,
    font_size: "medium",
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
    setOsdForm(normalizeOSDConfig(tenant.osd_config || {
      show_current_audio: tenant.osd_show_current_audio,
      position: tenant.osd_position,
      duration_seconds: tenant.osd_duration_seconds,
      opacity: tenant.osd_opacity,
      font_size: tenant.osd_font_size,
    }));
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

  // SPEC 005 — mutation para configuração de áudio
  const audioMutation = useMutation({
    mutationFn: atualizarConfigAudioEmpresa,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant-me"] });
      toast({ title: "Configuração de áudio salva!" });
    },
    onError: (err) => {
      toast({
        variant: "destructive",
        title: "Erro ao salvar áudio",
        description: err.message || "Tente novamente.",
      });
    },
  });

  const osdMutation = useMutation({
    mutationFn: (payload) => atualizarOSDConfigEmpresa(tenant.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant-me"] });
      toast({ title: "Overlay de música salvo!" });
    },
    onError: (err) => {
      toast({
        variant: "destructive",
        title: "Erro ao salvar overlay",
        description: err.message || "Tente novamente.",
      });
    },
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

      {/* SPEC 005 — configuração de áudio global */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configuração de Áudio</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <AudioPolicySelector
            value={tenant?.audio_policy_default ?? "auto"}
            onChange={(v) => {
              audioMutation.mutate({
                audio_policy_default: v || "auto",
                audio_fade_ms: tenant?.audio_fade_ms ?? 200,
              });
            }}
            allowNull={false}
            disabled={audioMutation.isPending || isLoading}
          />

          <div className="space-y-2">
            <Label>
              Tempo de fade de áudio: {tenant?.audio_fade_ms ?? 200}ms
            </Label>
            <input
              type="range"
              min="0"
              max="2000"
              step="50"
              value={tenant?.audio_fade_ms ?? 200}
              disabled={audioMutation.isPending || isLoading}
              onChange={(e) => {
                audioMutation.mutate({
                  audio_policy_default: tenant?.audio_policy_default || "auto",
                  audio_fade_ms: parseInt(e.target.value, 10),
                });
              }}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Suavização da transição entre rádio e áudio de mídia. 0 = sem
              fade, 200ms = padrão recomendado.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Overlay de Música</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
            <OSDConfigForm
              value={osdForm}
              onChange={setOsdForm}
              allowNull={false}
            />
            <OSDConfigPreview config={osdForm} />
          </div>
          <div className="flex justify-end">
            <Button
              disabled={osdMutation.isPending || isLoading || !tenant?.id}
              onClick={() => osdMutation.mutate(normalizeOSDConfig(osdForm))}
            >
              <Save className="w-4 h-4 mr-2" />
              {osdMutation.isPending ? "Salvando..." : "Salvar overlay"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
