import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  DialogFooter,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Trash2, Edit, Loader2, Clock } from "lucide-react";

const PLAY_MODES = {
  sequential: "Sequencial",
  shuffle: "Embaralhado",
  loop: "Loop",
};

export default function AudioScheduleBuilder({
  playlistId,
  schedules = [],
  folders = [],
  onAdd,
  onUpdate,
  onDelete,
  loading = false,
}) {
  const [open, setOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [form, setForm] = useState({
    folder_id: "",
    start_time: "00:00",
    end_time: "23:59",
    priority: 0,
    play_mode: "sequential",
    is_active: true,
  });

  const handleOpenNew = () => {
    setEditingSchedule(null);
    setForm({
      folder_id: "",
      start_time: "00:00",
      end_time: "23:59",
      priority: 0,
      play_mode: "sequential",
      is_active: true,
    });
    setOpen(true);
  };

  const handleOpenEdit = (schedule) => {
    setEditingSchedule(schedule);
    setForm({
      folder_id: schedule.folder_id,
      start_time: schedule.start_time,
      end_time: schedule.end_time,
      priority: schedule.priority,
      play_mode: schedule.play_mode,
      is_active: schedule.is_active,
    });
    setOpen(true);
  };

  const handleSave = async () => {
    if (!form.folder_id) {
      alert("Selecione uma pasta");
      return;
    }

    const payload = {
      ...form,
      priority: parseInt(form.priority),
    };

    if (editingSchedule) {
      await onUpdate?.(editingSchedule.id, payload);
    } else {
      await onAdd?.(payload);
    }

    setOpen(false);
  };

  const getFolderName = (folderId) => {
    return folders.find((f) => f.id === folderId)?.name || "—";
  };

  const sortedSchedules = [...schedules].sort(
    (a, b) => (b.priority || 0) - (a.priority || 0)
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-lg">Programação por Horário</h3>
          <p className="text-sm text-gray-600">
            Define qual pasta toca em cada hora do dia
          </p>
        </div>
        <Button onClick={handleOpenNew} disabled={loading || folders.length === 0}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Agendamento
        </Button>
      </div>

      {folders.length === 0 && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          Crie pastas de áudio primeiro antes de agendar
        </div>
      )}

      {sortedSchedules.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center border rounded-lg bg-gray-50">
          <Clock className="h-8 w-8 text-gray-300 mb-2" />
          <p className="text-gray-500 text-sm">Nenhum agendamento definido</p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Pasta</TableHead>
                <TableHead>Horário</TableHead>
                <TableHead>Modo</TableHead>
                <TableHead className="text-center">Prioridade</TableHead>
                <TableHead className="text-center">Ativo</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedSchedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell className="font-medium">
                    {getFolderName(schedule.folder_id)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {schedule.start_time} - {schedule.end_time}
                  </TableCell>
                  <TableCell className="text-sm">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                      {PLAY_MODES[schedule.play_mode] || schedule.play_mode}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-sm font-medium">
                      {schedule.priority}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <Checkbox checked={schedule.is_active} disabled />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenEdit(schedule)}
                        disabled={loading}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete?.(schedule.id)}
                        disabled={loading}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Dialog de criar/editar */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingSchedule ? "Editar" : "Novo"} Agendamento
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="folder">Pasta *</Label>
              <Select
                value={form.folder_id}
                onValueChange={(v) =>
                  setForm({ ...form, folder_id: v })
                }
              >
                <SelectTrigger id="folder">
                  <SelectValue placeholder="Selecione uma pasta" />
                </SelectTrigger>
                <SelectContent>
                  {folders.map((folder) => (
                    <SelectItem key={folder.id} value={folder.id}>
                      {folder.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-time">Início</Label>
                <Input
                  id="start-time"
                  type="time"
                  value={form.start_time}
                  onChange={(e) =>
                    setForm({ ...form, start_time: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="end-time">Fim</Label>
                <Input
                  id="end-time"
                  type="time"
                  value={form.end_time}
                  onChange={(e) =>
                    setForm({ ...form, end_time: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="priority">Prioridade (0-100)</Label>
                <Input
                  id="priority"
                  type="number"
                  min="0"
                  max="100"
                  value={form.priority}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      priority: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="play-mode">Modo de Reprodução</Label>
                <Select
                  value={form.play_mode}
                  onValueChange={(v) =>
                    setForm({ ...form, play_mode: v })
                  }
                >
                  <SelectTrigger id="play-mode">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PLAY_MODES).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="is-active"
                checked={form.is_active}
                onCheckedChange={(checked) =>
                  setForm({ ...form, is_active: checked })
                }
              />
              <Label htmlFor="is-active" className="cursor-pointer">
                Agendamento ativo
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={loading || !form.folder_id}>
              {loading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
