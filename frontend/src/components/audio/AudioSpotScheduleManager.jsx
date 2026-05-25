import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, Trash2, Edit, Loader2, Volume2 } from "lucide-react";

const INSERTION_POLICIES = {
  interrupt: "Interrompe música",
  wait_silence: "Aguarda silêncio",
  fade_mix: "Mix com música",
};

const SPOT_STATUS = {
  active: "Ativo",
  inactive: "Inativo",
  archived: "Arquivado",
};

export default function AudioSpotScheduleManager({
  playlistId,
  spots = [],
  spotSchedules = [],
  tracks = [],
  onCreateSpot,
  onUpdateSpot,
  onDeleteSpot,
  onCreateSchedule,
  onUpdateSchedule,
  onDeleteSchedule,
  loading = false,
}) {
  const [tab, setTab] = useState("spots");
  const [openSpotDialog, setOpenSpotDialog] = useState(false);
  const [openScheduleDialog, setOpenScheduleDialog] = useState(false);
  const [editingSpot, setEditingSpot] = useState(null);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Spot form
  const [spotForm, setSpotForm] = useState({
    name: "",
    description: "",
    track_id: "",
    status: "active",
    insertion_policy: "wait_silence",
  });

  // Schedule form
  const [scheduleForm, setScheduleForm] = useState({
    spot_id: "",
    interval_seconds: 1800,
    start_time: "06:00",
    end_time: "22:00",
    priority: 0,
    is_active: true,
  });

  // Spot handlers
  const handleNewSpot = () => {
    setEditingSpot(null);
    setSpotForm({
      name: "",
      description: "",
      track_id: "",
      status: "active",
      insertion_policy: "wait_silence",
    });
    setOpenSpotDialog(true);
  };

  const handleEditSpot = (spot) => {
    setEditingSpot(spot);
    setSpotForm({
      name: spot.name,
      description: spot.description || "",
      track_id: spot.track_id,
      status: spot.status,
      insertion_policy: spot.insertion_policy,
    });
    setOpenSpotDialog(true);
  };

  const handleSaveSpot = async () => {
    if (!spotForm.name.trim()) {
      alert("Nome do spot é obrigatório");
      return;
    }
    if (!spotForm.track_id) {
      alert("Selecione uma faixa");
      return;
    }

    if (editingSpot) {
      await onUpdateSpot?.(editingSpot.id, spotForm);
    } else {
      await onCreateSpot?.(spotForm);
    }

    setOpenSpotDialog(false);
  };

  // Schedule handlers
  const handleNewSchedule = () => {
    setEditingSchedule(null);
    setScheduleForm({
      spot_id: "",
      interval_seconds: 1800,
      start_time: "06:00",
      end_time: "22:00",
      priority: 0,
      is_active: true,
    });
    setOpenScheduleDialog(true);
  };

  const handleEditSchedule = (schedule) => {
    setEditingSchedule(schedule);
    setScheduleForm({
      spot_id: schedule.spot_id,
      interval_seconds: schedule.interval_seconds,
      start_time: schedule.start_time,
      end_time: schedule.end_time,
      priority: schedule.priority,
      is_active: schedule.is_active,
    });
    setOpenScheduleDialog(true);
  };

  const handleSaveSchedule = async () => {
    if (!scheduleForm.spot_id) {
      alert("Selecione um spot");
      return;
    }

    const payload = {
      ...scheduleForm,
      interval_seconds: parseInt(scheduleForm.interval_seconds),
      priority: parseInt(scheduleForm.priority),
    };

    if (editingSchedule) {
      await onUpdateSchedule?.(editingSchedule.id, payload);
    } else {
      await onCreateSchedule?.(payload);
    }

    setOpenScheduleDialog(false);
  };

  const getSpotName = (spotId) => {
    return spots.find((s) => s.id === spotId)?.name || "—";
  };

  const getTrackName = (trackId) => {
    return tracks.find((t) => t.id === trackId)?.name || "—";
  };

  const formatInterval = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}min`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  return (
    <Tabs value={tab} onValueChange={setTab} className="space-y-4">
      <TabsList>
        <TabsTrigger value="spots">Spots ({spots.length})</TabsTrigger>
        <TabsTrigger value="schedules">
          Agendamentos ({spotSchedules.length})
        </TabsTrigger>
      </TabsList>

      {/* Spots Tab */}
      <TabsContent value="spots" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Spots de Áudio</h3>
            <p className="text-sm text-gray-600">
              Crie spots (anúncios/jingles) para inserir na programação
            </p>
          </div>
          <Button onClick={handleNewSpot} disabled={loading || tracks.length === 0}>
            <Plus className="mr-2 h-4 w-4" />
            Novo Spot
          </Button>
        </div>

        {tracks.length === 0 && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            Faça upload de faixas primeiro antes de criar spots
          </div>
        )}

        {spots.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center border rounded-lg bg-gray-50">
            <Volume2 className="h-8 w-8 text-gray-300 mb-2" />
            <p className="text-gray-500 text-sm">Nenhum spot criado</p>
          </div>
        ) : (
          <div className="space-y-2">
            {spots.map((spot) => (
              <div
                key={spot.id}
                className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex-1">
                  <h4 className="font-medium">{spot.name}</h4>
                  <p className="text-xs text-gray-500 line-clamp-1">
                    {spot.description}
                  </p>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                      {getTrackName(spot.track_id)}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                      {INSERTION_POLICIES[spot.insertion_policy]}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                      {SPOT_STATUS[spot.status]}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditSpot(spot)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteConfirm(spot)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </TabsContent>

      {/* Schedules Tab */}
      <TabsContent value="schedules" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Agendamento de Spots</h3>
            <p className="text-sm text-gray-600">
              Define quando e com que frequência cada spot toca
            </p>
          </div>
          <Button onClick={handleNewSchedule} disabled={loading || spots.length === 0}>
            <Plus className="mr-2 h-4 w-4" />
            Novo Agendamento
          </Button>
        </div>

        {spots.length === 0 && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            Crie spots primeiro antes de agendar
          </div>
        )}

        {spotSchedules.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center border rounded-lg bg-gray-50">
            <Volume2 className="h-8 w-8 text-gray-300 mb-2" />
            <p className="text-gray-500 text-sm">Nenhum agendamento criado</p>
          </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Spot</TableHead>
                  <TableHead>Intervalo</TableHead>
                  <TableHead>Horário</TableHead>
                  <TableHead className="text-center">Prioridade</TableHead>
                  <TableHead className="text-center">Ativo</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {spotSchedules.map((schedule) => (
                  <TableRow key={schedule.id}>
                    <TableCell className="font-medium">
                      {getSpotName(schedule.spot_id)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatInterval(schedule.interval_seconds)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {schedule.start_time} - {schedule.end_time}
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
                          onClick={() => handleEditSchedule(schedule)}
                          disabled={loading}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeleteSchedule?.(schedule.id)}
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
      </TabsContent>

      {/* Spot Dialog */}
      <Dialog open={openSpotDialog} onOpenChange={setOpenSpotDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSpot ? "Editar" : "Novo"} Spot</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="spot-name">Nome *</Label>
              <Input
                id="spot-name"
                value={spotForm.name}
                onChange={(e) =>
                  setSpotForm({ ...spotForm, name: e.target.value })
                }
                placeholder="Ex: Anúncio Rádio XYZ"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="spot-desc">Descrição</Label>
              <Textarea
                id="spot-desc"
                value={spotForm.description}
                onChange={(e) =>
                  setSpotForm({ ...spotForm, description: e.target.value })
                }
                placeholder="Descrição do spot"
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="spot-track">Faixa de Áudio *</Label>
              <Select
                value={spotForm.track_id}
                onValueChange={(v) =>
                  setSpotForm({ ...spotForm, track_id: v })
                }
              >
                <SelectTrigger id="spot-track">
                  <SelectValue placeholder="Selecione uma faixa" />
                </SelectTrigger>
                <SelectContent>
                  {tracks.map((track) => (
                    <SelectItem key={track.id} value={track.id}>
                      {track.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="spot-policy">Política de Inserção</Label>
                <Select
                  value={spotForm.insertion_policy}
                  onValueChange={(v) =>
                    setSpotForm({ ...spotForm, insertion_policy: v })
                  }
                >
                  <SelectTrigger id="spot-policy">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(INSERTION_POLICIES).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="spot-status">Status</Label>
                <Select
                  value={spotForm.status}
                  onValueChange={(v) =>
                    setSpotForm({ ...spotForm, status: v })
                  }
                >
                  <SelectTrigger id="spot-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(SPOT_STATUS).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenSpotDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveSpot} disabled={loading}>
              {loading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog open={openScheduleDialog} onOpenChange={setOpenScheduleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingSchedule ? "Editar" : "Novo"} Agendamento de Spot
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="schedule-spot">Spot *</Label>
              <Select
                value={scheduleForm.spot_id}
                onValueChange={(v) =>
                  setScheduleForm({ ...scheduleForm, spot_id: v })
                }
              >
                <SelectTrigger id="schedule-spot">
                  <SelectValue placeholder="Selecione um spot" />
                </SelectTrigger>
                <SelectContent>
                  {spots.map((spot) => (
                    <SelectItem key={spot.id} value={spot.id}>
                      {spot.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="interval">Intervalo (segundos)</Label>
              <Input
                id="interval"
                type="number"
                min="30"
                step="30"
                value={scheduleForm.interval_seconds}
                onChange={(e) =>
                  setScheduleForm({
                    ...scheduleForm,
                    interval_seconds: parseInt(e.target.value),
                  })
                }
                placeholder="1800 (30 minutos)"
              />
              <p className="text-xs text-gray-500">
                {formatInterval(scheduleForm.interval_seconds)}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="schedule-start">Início</Label>
                <Input
                  id="schedule-start"
                  type="time"
                  value={scheduleForm.start_time}
                  onChange={(e) =>
                    setScheduleForm({
                      ...scheduleForm,
                      start_time: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="schedule-end">Fim</Label>
                <Input
                  id="schedule-end"
                  type="time"
                  value={scheduleForm.end_time}
                  onChange={(e) =>
                    setScheduleForm({
                      ...scheduleForm,
                      end_time: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="schedule-priority">Prioridade (0-100)</Label>
              <Input
                id="schedule-priority"
                type="number"
                min="0"
                max="100"
                value={scheduleForm.priority}
                onChange={(e) =>
                  setScheduleForm({
                    ...scheduleForm,
                    priority: parseInt(e.target.value) || 0,
                  })
                }
              />
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="schedule-active"
                checked={scheduleForm.is_active}
                onCheckedChange={(checked) =>
                  setScheduleForm({
                    ...scheduleForm,
                    is_active: checked,
                  })
                }
              />
              <Label htmlFor="schedule-active" className="cursor-pointer">
                Agendamento ativo
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpenScheduleDialog(false)}
            >
              Cancelar
            </Button>
            <Button onClick={handleSaveSchedule} disabled={loading}>
              {loading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir spot?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir "<strong>{deleteConfirm?.name}</strong>"?
              Isso não deletará a faixa, apenas o spot.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex gap-2 justify-end">
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDeleteSpot?.(deleteConfirm.id);
                setDeleteConfirm(null);
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              Excluir
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </Tabs>
  );
}
