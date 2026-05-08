import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { AlertTriangle, Download, Eye, Megaphone, Monitor } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatsCard from "@/components/shared/StatsCard";
import StatusBadge from "@/components/shared/StatusBadge";
import { listarCampanhas } from "@/api/campanhas";
import { listarDispositivos } from "@/api/dispositivos";
import { buscarResumoRelatorio, exportarRelatorioCSV } from "@/api/relatorios";

function isoDate(date) {
  return date.toISOString().slice(0, 10);
}

function toBackendDate(value, endOfDay = false) {
  if (!value) return undefined;
  return `${value}T${endOfDay ? "23:59:59" : "00:00:00"}`;
}

function statusForBadge(status) {
  if (status === "completed") return "success";
  if (status === "interrupted") return "partial";
  return status || "success";
}

export default function Relatorios() {
  const today = useMemo(() => new Date(), []);
  const sevenDaysAgo = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() - 6);
    return d;
  }, []);

  const [dateFrom, setDateFrom] = useState(isoDate(sevenDaysAgo));
  const [dateTo, setDateTo] = useState(isoDate(today));
  const [campaignId, setCampaignId] = useState("all");
  const [deviceId, setDeviceId] = useState("all");

  const reportParams = useMemo(() => {
    const params = {
      date_from: toBackendDate(dateFrom),
      date_to: toBackendDate(dateTo, true),
    };
    if (campaignId !== "all") params.campaign_id = campaignId;
    if (deviceId !== "all") params.device_id = deviceId;
    return params;
  }, [campaignId, dateFrom, dateTo, deviceId]);

  const { data: summary = {}, isLoading, error } = useQuery({
    queryKey: ["reports-summary", reportParams],
    queryFn: () => buscarResumoRelatorio(reportParams),
  });
  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns-filter"],
    queryFn: () => listarCampanhas(),
  });
  const { data: devices = [] } = useQuery({
    queryKey: ["devices-filter"],
    queryFn: () => listarDispositivos(),
  });

  const details = summary.details || [];
  const viewsPerDay = summary.views_per_day?.length
    ? summary.views_per_day
    : [{ date: "Sem dados", views: 0 }];
  const deviceStatus = (summary.device_status || []).filter((item) => item.value > 0);

  const handleExportCsv = () => exportarRelatorioCSV(reportParams);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-xl font-bold">Relatórios</h2>
        <Button variant="outline" size="sm" onClick={handleExportCsv}>
          <Download className="w-4 h-4 mr-2" />
          Exportar CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          type="date"
          className="w-auto"
          value={dateFrom}
          onChange={(event) => setDateFrom(event.target.value)}
        />
        <Input
          type="date"
          className="w-auto"
          value={dateTo}
          onChange={(event) => setDateTo(event.target.value)}
        />
        <Select value={campaignId} onValueChange={setCampaignId}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Campanha" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {campaigns.map((campaign) => (
              <SelectItem key={campaign.id} value={campaign.id}>
                {campaign.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={deviceId} onValueChange={setDeviceId}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="TV" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {devices.map((device) => (
              <SelectItem key={device.id} value={device.id}>
                {device.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {error.message || "Não foi possível carregar os relatórios."}
        </Card>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total de Exibições"
          value={isLoading ? "..." : summary.total_views || 0}
          icon={Eye}
        />
        <StatsCard
          title="Campanha Mais Exibida"
          value={isLoading ? "..." : summary.top_campaign?.name || "Sem dados"}
          icon={Megaphone}
        />
        <StatsCard
          title="TV Mais Ativa"
          value={isLoading ? "..." : summary.top_device?.name || "Sem dados"}
          icon={Monitor}
        />
        <StatsCard
          title="TVs com Falha"
          value={isLoading ? "..." : summary.problem_devices || 0}
          icon={AlertTriangle}
          iconClassName="bg-red-100"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Exibições por Dia</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={viewsPerDay}
                  margin={{ top: 5, right: 5, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 13%, 91%)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="views" fill="hsl(221, 83%, 53%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Status dos Dispositivos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-52 flex items-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deviceStatus.length ? deviceStatus : [{ name: "Sem dados", value: 1, color: "#e5e7eb" }]}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${deviceStatus.length ? value : 0}`}
                  >
                    {(deviceStatus.length ? deviceStatus : [{ color: "#e5e7eb" }]).map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Detalhamento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>TV</TableHead>
                  <TableHead className="hidden md:table-cell">Campanha</TableHead>
                  <TableHead className="hidden lg:table-cell">Mídia</TableHead>
                  <TableHead>Exibições</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {details.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-sm text-muted-foreground text-center py-8">
                      Nenhuma exibição registrada no período selecionado.
                    </TableCell>
                  </TableRow>
                )}
                {details.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="text-sm">{row.date}</TableCell>
                    <TableCell className="text-sm font-medium">{row.device}</TableCell>
                    <TableCell className="hidden md:table-cell text-sm">{row.campaign}</TableCell>
                    <TableCell className="hidden lg:table-cell text-sm">{row.media}</TableCell>
                    <TableCell className="text-sm font-medium">
                      {(row.views || 0).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={statusForBadge(row.status)} />
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
