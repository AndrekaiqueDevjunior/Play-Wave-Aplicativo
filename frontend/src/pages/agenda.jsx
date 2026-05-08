import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import CalendarCell from "@/components/schedule/CalendarCell";
import ScheduleSidebar from "@/components/schedule/ScheduleSidebar";
import CampaignDetailModal from "@/components/schedule/CampaignDetailModal";

const MONTHS = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];
const WEEKDAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

export default function Agenda() {
  const today = new Date();
  const [currentDate, setCurrentDate] = useState(
    new Date(today.getFullYear(), today.getMonth(), 1),
  );
  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState("all");

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const days = Array.from({ length: firstDay }, () => null).concat(
    Array.from({ length: daysInMonth }, (_, i) => i + 1),
  );

  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => base44.entities.Campaign.list(),
  });
  const { data: devices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => base44.entities.Device.list(),
  });
  const { data: media = [] } = useQuery({
    queryKey: ["media"],
    queryFn: () => base44.entities.Media.list(),
  });

  const filteredCampaigns =
    filterStatus === "all"
      ? campaigns
      : campaigns.filter((c) => c.status === filterStatus);

  const getCampaignsForDay = (day) => {
    if (!day) return [];
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return filteredCampaigns.filter((c) => {
      if (!c.start_date || !c.end_date) return false;
      return dateStr >= c.start_date && dateStr <= c.end_date;
    });
  };

  const getDateStr = (day) =>
    `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

  const isToday = (day) =>
    day === today.getDate() &&
    month === today.getMonth() &&
    year === today.getFullYear();

  const handleDrop = async (campaignId, newDateStr) => {
    const campaign = campaigns.find((c) => c.id === campaignId);
    if (!campaign) return;
    const oldStart = new Date(campaign.start_date + "T00:00:00");
    const oldEnd = new Date(campaign.end_date + "T00:00:00");
    const duration = Math.round((oldEnd - oldStart) / (1000 * 60 * 60 * 24));
    const newStart = new Date(newDateStr + "T00:00:00");
    const newEnd = new Date(newStart);
    newEnd.setDate(newEnd.getDate() + duration);
    const pad = (n) => String(n).padStart(2, "0");
    const fmt = (d) =>
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    await base44.entities.Campaign.update(campaignId, {
      start_date: fmt(newStart),
      end_date: fmt(newEnd),
    });
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    toast({
      title: "Campanha movida!",
      description: `"${campaign.name}" reagendada para ${newDateStr.split("-").reverse().join("/")}.`,
    });
  };

  const handleCampaignSaved = async (form) => {
    await base44.entities.Campaign.create({ ...form, total_views: 0 });
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    toast({
      title: "Campanha criada!",
      description: `"${form.name}" adicionada ao calendário.`,
    });
  };

  const handleCampaignUpdate = async (id, data) => {
    await base44.entities.Campaign.update(id, data);
    queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    setSelectedCampaign((prev) => (prev ? { ...prev, ...data } : prev));
    toast({ title: "Campanha atualizada!" });
  };

  const statusCounts = {
    active: campaigns.filter((c) => c.status === "active").length,
    draft: campaigns.filter((c) => c.status === "draft").length,
    paused: campaigns.filter((c) => c.status === "paused").length,
  };

  return (
    <div className={cn("flex gap-0 h-full transition-all")}>
      <div className="flex-1 min-w-0 space-y-4 pr-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">Calendário de Agendamento</h2>
            <p className="text-sm text-muted-foreground">
              Arraste campanhas para mover entre datas • clique em um dia para
              gerenciar
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-36 h-8 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="active">Ativas</SelectItem>
                <SelectItem value="draft">Rascunho</SelectItem>
                <SelectItem value="paused">Pausadas</SelectItem>
                <SelectItem value="ended">Encerradas</SelectItem>
              </SelectContent>
            </Select>
            <Button
              size="sm"
              onClick={() => {
                setSelectedDay(getDateStr(today.getDate()));
                setSidebarOpen(true);
              }}
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Nova Campanha
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 text-xs">
          {[
            {
              status: "active",
              color: "bg-emerald-500",
              label: "Ativas",
              count: statusCounts.active,
            },
            {
              status: "draft",
              color: "bg-slate-400",
              label: "Rascunho",
              count: statusCounts.draft,
            },
            {
              status: "paused",
              color: "bg-amber-500",
              label: "Pausadas",
              count: statusCounts.paused,
            },
          ].map((item) => (
            <button
              key={item.status}
              onClick={() =>
                setFilterStatus(
                  filterStatus === item.status ? "all" : item.status,
                )
              }
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-full border transition-colors",
                filterStatus === item.status
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40",
              )}
            >
              <span className={cn("w-2 h-2 rounded-full", item.color)} />
              {item.label}{" "}
              <span className="text-muted-foreground">({item.count})</span>
            </button>
          ))}
        </div>

        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setCurrentDate(new Date(year, month - 1, 1))}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="font-semibold text-sm">
              {MONTHS[month]} {year}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setCurrentDate(new Date(year, month + 1, 1))}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          <div className="grid grid-cols-7 border-b">
            {WEEKDAYS.map((day) => (
              <div
                key={day}
                className="p-2 text-center text-xs font-semibold text-muted-foreground bg-muted/20"
              >
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {days.map((day, i) => {
              const dateStr = day ? getDateStr(day) : null;
              return (
                <CalendarCell
                  key={i}
                  day={day}
                  dateStr={dateStr}
                  isToday={isToday(day)}
                  isSelected={selectedDay === dateStr}
                  campaigns={day ? getCampaignsForDay(day) : []}
                  onDayClick={(d) => {
                    setSelectedDay(d);
                    setSidebarOpen(true);
                  }}
                  onCampaignClick={(c) => setSelectedCampaign(c)}
                  onDrop={handleDrop}
                />
              );
            })}
          </div>
        </div>
      </div>

      {sidebarOpen && (
        <div
          className="w-80 shrink-0 border-l bg-card flex flex-col ml-4 rounded-xl shadow-sm overflow-hidden"
          style={{
            maxHeight: "calc(100vh - 120px)",
            position: "sticky",
            top: 0,
          }}
        >
          <ScheduleSidebar
            campaigns={campaigns}
            devices={devices}
            media={media}
            selectedDay={selectedDay}
            onClose={() => setSidebarOpen(false)}
            onCampaignSaved={handleCampaignSaved}
          />
        </div>
      )}

      <CampaignDetailModal
        campaign={selectedCampaign}
        onClose={() => setSelectedCampaign(null)}
        onUpdate={handleCampaignUpdate}
      />
    </div>
  );
}
