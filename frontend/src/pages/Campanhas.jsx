import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  Search,
  Megaphone,
  MoreHorizontal,
  Eye,
  Pencil,
  Copy,
  Pause,
  Trash2,
  Play,
  Archive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
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
import CampaignFormModal from "@/components/campaigns/CampaignFormModal";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import { useToast } from "@/components/ui/use-toast";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

const PRIORITY_LABEL = {
  1: "Baixa",
  2: "Normal",
  3: "Média",
  4: "Alta",
  5: "Urgente",
};
const PRIORITY_COLOR = {
  1: "text-slate-500",
  2: "text-slate-600",
  3: "text-amber-600",
  4: "text-orange-600",
  5: "text-red-600",
};

export default function Campanhas() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editCampaign, setEditCampaign] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => base44.entities.Campaign.list("-created_date"),
  });
  const { data: mediaList = [] } = useQuery({
    queryKey: ["media"],
    queryFn: () => base44.entities.Media.list(),
  });
  const { data: devices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => base44.entities.Device.list(),
  });

  const filtered = campaigns.filter((c) => {
    const matchSearch = (c.name || "")
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleSave = async (form) => {
    if (editCampaign) {
      await base44.entities.Campaign.update(editCampaign.id, form);
      toast({ title: "Campanha atualizada!" });
    } else {
      await base44.entities.Campaign.create({ ...form, total_views: 0 });
      toast({
        title: "Campanha criada!",
        description: `${form.name} foi adicionada.`,
      });
    }
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    setModalOpen(false);
    setEditCampaign(null);
  };

  const handleSetStatus = async (campaign, status) => {
    await base44.entities.Campaign.update(campaign.id, { status });
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    const labels = {
      active: "ativada",
      paused: "pausada",
      ended: "encerrada",
      draft: "movida para rascunho",
    };
    toast({ title: `Campanha ${labels[status] || status}.` });
  };

  const handleDuplicate = async (campaign) => {
    const { id, created_date, updated_date, ...rest } = campaign;
    await base44.entities.Campaign.create({
      ...rest,
      name: `${campaign.name} (cópia)`,
      status: "draft",
      total_views: 0,
    });
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    toast({ title: "Campanha duplicada!" });
  };

  const handleDelete = async () => {
    await base44.entities.Campaign.delete(deleteTarget.id);
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    toast({ title: "Campanha excluída." });
    setDeleteTarget(null);
  };

  const openEdit = (c) => {
    setEditCampaign(c);
    setModalOpen(true);
  };
  const openNew = () => {
    setEditCampaign(null);
    setModalOpen(true);
  };

  const counts = {
    active: campaigns.filter((c) => c.status === "active").length,
    draft: campaigns.filter((c) => c.status === "draft").length,
    paused: campaigns.filter((c) => c.status === "paused").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Campanhas</h2>
          <p className="text-sm text-muted-foreground">
            {campaigns.length} total ·{" "}
            <span className="text-emerald-600 font-medium">
              {counts.active} ativas
            </span>{" "}
            · <span className="text-slate-500">{counts.draft} rascunho</span>
          </p>
        </div>
        <Button onClick={openNew}>
          <Plus className="w-4 h-4 mr-2" />
          Nova Campanha
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Buscar campanha..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-44">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="draft">Rascunho</SelectItem>
              <SelectItem value="scheduled">Agendada</SelectItem>
              <SelectItem value="active">Ativa</SelectItem>
              <SelectItem value="paused">Pausada</SelectItem>
              <SelectItem value="ended">Encerrada</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Megaphone}
            title="Nenhuma campanha encontrada"
            description="Crie sua primeira campanha para começar."
          />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Campanha</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">
                    Período
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">
                    Prioridade
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">TVs</TableHead>
                  <TableHead className="hidden lg:table-cell">Mídias</TableHead>
                  <TableHead className="hidden xl:table-cell">
                    Exibições
                  </TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((campaign) => (
                  <TableRow key={campaign.id}>
                    <TableCell>
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Megaphone className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{campaign.name}</p>
                          {campaign.description && (
                            <p className="text-xs text-muted-foreground hidden sm:block truncate max-w-[200px]">
                              {campaign.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={campaign.status} />
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-xs text-muted-foreground">
                      {campaign.start_date
                        ? format(
                            new Date(campaign.start_date + "T00:00:00"),
                            "dd/MM/yy",
                          )
                        : "—"}
                      {campaign.end_date
                        ? ` → ${format(new Date(campaign.end_date + "T00:00:00"), "dd/MM/yy")}`
                        : ""}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell">
                      <span
                        className={cn(
                          "text-xs font-medium",
                          PRIORITY_COLOR[campaign.priority] || "text-slate-500",
                        )}
                      >
                        {PRIORITY_LABEL[campaign.priority] || "—"}
                      </span>
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm">
                      {campaign.device_ids?.length || 0}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm">
                      {campaign.media_ids?.length || 0}
                    </TableCell>
                    <TableCell className="hidden xl:table-cell text-sm font-medium">
                      {campaign.total_views?.toLocaleString() || 0}
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
                            <Link to={`/campanhas/${campaign.id}/preview`}>
                              <Eye className="w-4 h-4 mr-2" />
                              Preview
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEdit(campaign)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDuplicate(campaign)}
                          >
                            <Copy className="w-4 h-4 mr-2" />
                            Duplicar
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {campaign.status !== "active" && (
                            <DropdownMenuItem
                              onClick={() =>
                                handleSetStatus(campaign, "active")
                              }
                            >
                              <Play className="w-4 h-4 mr-2" />
                              Ativar
                            </DropdownMenuItem>
                          )}
                          {campaign.status === "active" && (
                            <DropdownMenuItem
                              onClick={() =>
                                handleSetStatus(campaign, "paused")
                              }
                            >
                              <Pause className="w-4 h-4 mr-2" />
                              Pausar
                            </DropdownMenuItem>
                          )}
                          {campaign.status !== "draft" && (
                            <DropdownMenuItem
                              onClick={() => handleSetStatus(campaign, "draft")}
                            >
                              <Archive className="w-4 h-4 mr-2" />
                              Mover p/ Rascunho
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            onClick={() => handleSetStatus(campaign, "ended")}
                          >
                            <Archive className="w-4 h-4 mr-2" />
                            Encerrar
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteTarget(campaign)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      <CampaignFormModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditCampaign(null);
        }}
        onSave={handleSave}
        campaign={editCampaign}
        mediaList={mediaList}
        devices={devices}
      />
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Excluir campanha?"
        description={`"${deleteTarget?.name}" será removida permanentemente, incluindo todo o histórico.`}
      />
    </div>
  );
}
