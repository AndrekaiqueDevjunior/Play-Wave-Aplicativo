import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Monitor,
  Download,
  Smartphone,
  Type,
  Link2,
  CheckCircle2,
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { criarDispositivo } from "@/api/dispositivos";

const TIPOS_DISPOSITIVO = [
  { value: "tv", label: "TV" },
  { value: "tablet", label: "Tablet" },
  { value: "totem", label: "Totem" },
  { value: "smartphone", label: "Celular" },
  { value: "panel", label: "Painel" },
  { value: "other", label: "Outro" },
];

const passos = [
  { icon: Download, label: "Instale o player na TV" },
  { icon: Smartphone, label: "Abra o aplicativo na TV" },
  { icon: Type, label: "Copie o código exibido na tela" },
  { icon: Monitor, label: "Digite o código aqui no painel" },
  { icon: Link2, label: "Clique em vincular dispositivo" },
];

export default function DispositivoNovo() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [form, setForm] = useState({
    name: "",
    location: "",
    group: "",
    pairing_code: "",
    device_type: "tv",
    os: "web_player",
    audio_playlist_id: "",  // Adicionar campo que existe no schema backend
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.pairing_code.trim()) return;
    setSaving(true);
    try {
      // Limpar campos vazios antes de enviar
      const payload = {
        ...form,
        status: "offline", 
        is_active: true,
        // Converter strings vazias em null para campos UUID
        audio_playlist_id: form.audio_playlist_id?.trim() || null,
        // Remover campos que não existem no schema backend
        current_campaign_id: undefined,
      };
      await criarDispositivo(payload);
      toast({
        title: "Dispositivo vinculado!",
        description: `${form.name} foi vinculado com sucesso.`,
      });
      navigate("/dispositivos");
    } catch (error) {
      toast({
        title: "Erro ao vincular dispositivo",
        description: error.message || "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold">Adicionar TV / Pareamento</h2>
        <p className="text-sm text-muted-foreground">
          Vincule uma nova TV ou player ao painel
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Como funciona</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {passos.map((passo, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="text-sm font-bold text-primary">
                    {i + 1}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <passo.icon className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{passo.label}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Dados do Dispositivo</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Nome da TV</Label>
              <Input
                placeholder="Ex: TV Recepção"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tipo de dispositivo</Label>
                <Select
                  value={form.device_type}
                  onValueChange={(v) => setForm({ ...form, device_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS_DISPOSITIVO.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Sistema Operacional</Label>
                <Select
                  value={form.os}
                  onValueChange={(v) => setForm({ ...form, os: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="web_player">Web Player</SelectItem>
                    <SelectItem value="android_tv">Android TV</SelectItem>
                    <SelectItem value="windows">Windows</SelectItem>
                    <SelectItem value="ios">iOS</SelectItem>
                    <SelectItem value="linux">Linux</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Localização</Label>
                <Input
                  placeholder="Ex: Recepção"
                  value={form.location}
                  onChange={(e) =>
                    setForm({ ...form, location: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Grupo</Label>
                <Input
                  placeholder="Ex: Matriz, Filial SP"
                  value={form.group}
                  onChange={(e) => setForm({ ...form, group: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Código de Pareamento</Label>
              <Input
                placeholder="Ex: TV-4821"
                value={form.pairing_code}
                onChange={(e) => {
                  let code = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
                  if (code.length > 6) code = code.slice(0, 6);
                  if (code.length > 2) code = code.slice(0, 2) + "-" + code.slice(2);
                  setForm({ ...form, pairing_code: code });
                }}
                className="font-mono text-lg tracking-widest"
                required
              />
              <p className="text-xs text-muted-foreground">
                Digite o código exibido na tela da TV
              </p>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/dispositivos")}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={saving}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                {saving ? "Vinculando..." : "Vincular TV"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
