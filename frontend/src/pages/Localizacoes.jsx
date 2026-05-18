import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, MapPin, Pencil, Trash2, Monitor } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listarLocalizacoes,
  criarLocalizacao,
  deletarLocalizacao,
} from "@/api/localizacoes";
import { useToast } from "@/components/ui/use-toast";

export default function Localizacoes() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", address: "" });

  const [isSaving, setIsSaving] = useState(false);

  const { data: locations = [], isLoading, error } = useQuery({
    queryKey: ["locations"],
    queryFn: () => listarLocalizacoes(),
  });

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await criarLocalizacao(form);
      queryClient.invalidateQueries({ queryKey: ["locations"] });
      setForm({ name: "", description: "", address: "" });
      setOpen(false);
      toast({ title: "Localização criada!" });
    } catch (err) {
      toast({ variant: "destructive", title: "Erro ao criar localização", description: err?.message || "Tente novamente." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deletarLocalizacao(id);
      queryClient.invalidateQueries({ queryKey: ["locations"] });
      toast({ title: "Localização removida." });
    } catch (err) {
      toast({ variant: "destructive", title: "Erro ao remover localização", description: err?.message || "Tente novamente." });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Localizações</h2>
          <p className="text-sm text-muted-foreground">
            Organize suas TVs por locais
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Nova Localização
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova Localização</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Nome</Label>
                <Input
                  placeholder="Ex: Recepção"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Descrição</Label>
                <Textarea
                  placeholder="Descrição do local..."
                  value={form.description}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Endereço</Label>
                <Input
                  placeholder="Endereço do local"
                  value={form.address}
                  onChange={(e) =>
                    setForm({ ...form, address: e.target.value })
                  }
                />
              </div>
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleSave} disabled={!form.name || isSaving}>
                  Salvar
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {error.message || "Não foi possível carregar as localizações."}
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Local</TableHead>
                  <TableHead className="hidden md:table-cell">
                    Endereço
                  </TableHead>
                  <TableHead>TVs</TableHead>
                  <TableHead className="w-24"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-sm text-muted-foreground">
                      Carregando localizações...
                    </TableCell>
                  </TableRow>
                )}
                {!isLoading && locations.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-sm text-muted-foreground">
                      Nenhuma localização cadastrada.
                    </TableCell>
                  </TableRow>
                )}
                {locations.map((loc) => (
                  <TableRow key={loc.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                          <MapPin className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{loc.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {loc.description}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                      {loc.address}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Monitor className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="text-sm font-medium">
                          {loc.device_count}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive"
                          onClick={() => handleDelete(loc.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
