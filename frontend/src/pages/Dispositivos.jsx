import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Search,
  Monitor,
  MoreHorizontal,
  Eye,
  Pencil,
  Power,
  Trash2,
  Tv,
  Tablet,
  Smartphone,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import DeviceFormModal from "@/components/devices/DeviceFormModal";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import { useToast } from "@/components/ui/use-toast";
import moment from "moment";
import { cn } from "@/lib/utils";

const TYPE_ICON = {
  tv: Tv,
  tablet: Tablet,
  smartphone: Smartphone,
  totem: Monitor,
  panel: Monitor,
  other: Monitor,
};
const TYPE_LABEL = {
  tv: "TV",
  tablet: "Tablet",
  totem: "Totem",
  smartphone: "Celular",
  panel: "Painel",
  other: "Outro",
};

export default function Dispositivos() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editDevice, setEditDevice] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: devices = [], isLoading } = useQuery({
    queryKey: ["devices"],
    queryFn: () => base44.entities.Device.list("-created_date"),
  });

  const filtered = devices.filter((d) => {
    const q = search.toLowerCase();
    const matchSearch =
      d.name.toLowerCase().includes(q) ||
      (d.pairing_code || "").toLowerCase().includes(q) ||
      (d.location || "").toLowerCase().includes(q);
    const matchStatus = statusFilter === "all" || d.status === statusFilter;
    const matchType = typeFilter === "all" || d.device_type === typeFilter;
    return matchSearch && matchStatus && matchType;
  });

  const handleSave = async (form) => {
    if (editDevice) {
      await base44.entities.Device.update(editDevice.id, form);
      toast({ title: "Dispositivo atualizado!" });
    } else {
      await base44.entities.Device.create({
        ...form,
        status: "offline",
        is_active: true,
      });
      toast({
        title: "Dispositivo cadastrado!",
        description: `${form.name} foi vinculado.`,
      });
    }
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    setModalOpen(false);
    setEditDevice(null);
  };

  const handleToggleActive = async (device) => {
    await base44.entities.Device.update(device.id, {
      is_active: !device.is_active,
    });
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    toast({
      title: device.is_active
        ? "Dispositivo desativado."
        : "Dispositivo ativado.",
    });
  };

  const handleDelete = async () => {
    await base44.entities.Device.delete(deleteTarget.id);
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    toast({ title: "Dispositivo removido." });
    setDeleteTarget(null);
  };

  const handleChangeStatus = async (device, status) => {
    await base44.entities.Device.update(device.id, { status });
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    toast({ title: `Status alterado para "${status}".` });
  };

  const openEdit = (device) => {
    setEditDevice(device);
    setModalOpen(true);
  };
  const openNew = () => {
    setEditDevice(null);
    setModalOpen(true);
  };

  const online = devices.filter((d) => d.status === "online").length;
  const offline = devices.filter((d) => d.status === "offline").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Dispositivos</h2>
          <p className="text-sm text-muted-foreground">
            {devices.length} cadastrados ·{" "}
            <span className="text-emerald-600 font-medium">
              {online} online
            </span>{" "}
            · <span className="text-red-500">{offline} offline</span>
          </p>
        </div>
        <Button onClick={openNew}>
          <Plus className="w-4 h-4 mr-2" />
          Adicionar Dispositivo
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome, código ou localização..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos status</SelectItem>
              <SelectItem value="online">Online</SelectItem>
              <SelectItem value="offline">Offline</SelectItem>
              <SelectItem value="syncing">Sincronizando</SelectItem>
              <SelectItem value="error">Erro</SelectItem>
            </SelectContent>
          </Select>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos tipos</SelectItem>
              <SelectItem value="tv">TV</SelectItem>
              <SelectItem value="tablet">Tablet</SelectItem>
              <SelectItem value="totem">Totem</SelectItem>
              <SelectItem value="smartphone">Celular</SelectItem>
              <SelectItem value="panel">Painel</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Monitor}
            title="Nenhum dispositivo encontrado"
            description="Adicione um dispositivo ou ajuste os filtros."
          />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Dispositivo</TableHead>
                  <TableHead>Código</TableHead>
                  <TableHead className="hidden md:table-cell">Tipo</TableHead>
                  <TableHead className="hidden md:table-cell">
                    Localização
                  </TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden lg:table-cell">
                    Última conexão
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">
                    Campanha
                  </TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((device) => {
                  const TypeIcon = TYPE_ICON[device.device_type] || Monitor;
                  return (
                    <TableRow
                      key={device.id}
                      className={cn(!device.is_active && "opacity-50")}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                            <TypeIcon className="w-4 h-4 text-muted-foreground" />
                          </div>
                          <div>
                            <span className="font-medium text-sm block">
                              {device.name}
                            </span>
                            {!device.is_active && (
                              <span className="text-xs text-destructive">
                                Inativo
                              </span>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {device.pairing_code}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <Badge variant="outline" className="text-xs">
                          {TYPE_LABEL[device.device_type] || "—"}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                        {device.location || "—"}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={device.status} />
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                        {device.last_connection
                          ? moment(device.last_connection).fromNow()
                          : "—"}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell text-sm">
                        {device.current_campaign || "—"}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link to={`/dispositivos/${device.id}`}>
                                <Eye className="w-4 h-4 mr-2" />
                                Ver detalhes
                              </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openEdit(device)}>
                              <Pencil className="w-4 h-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() =>
                                handleChangeStatus(
                                  device,
                                  device.status === "online"
                                    ? "offline"
                                    : "online",
                                )
                              }
                            >
                              <Power className="w-4 h-4 mr-2" />
                              {device.status === "online"
                                ? "Marcar Offline"
                                : "Marcar Online"}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleToggleActive(device)}
                            >
                              <Power className="w-4 h-4 mr-2" />
                              {device.is_active ? "Desativar" : "Ativar"}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => setDeleteTarget(device)}
                            >
                              <Trash2 className="w-4 h-4 mr-2" />
                              Excluir
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      <DeviceFormModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditDevice(null);
        }}
        onSave={handleSave}
        device={editDevice}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Excluir dispositivo?"
        description={`"${deleteTarget?.name}" será removido permanentemente. Esta ação não pode ser desfeita.`}
      />
    </div>
  );
}
