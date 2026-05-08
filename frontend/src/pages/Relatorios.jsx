import React from "react";
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
import { Download, Eye, Megaphone, Monitor, AlertTriangle } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import StatsCard from "@/components/shared/StatsCard";
import StatusBadge from "@/components/shared/StatusBadge";
import { mockViewsPerDay, mockCampaigns, mockDevices } from "@/lib/mockData";

const viewsByCampaign = [
  { name: "Camp. Abril", views: 12450 },
  { name: "Institucional", views: 8200 },
  { name: "Cardápio", views: 5800 },
  { name: "Promoção", views: 3100 },
];

const deviceStatus = [
  { name: "Online", value: 3, color: "#10b981" },
  { name: "Offline", value: 1, color: "#ef4444" },
  { name: "Sincronizando", value: 1, color: "#f59e0b" },
  { name: "Erro", value: 1, color: "#f87171" },
];

const reportData = [
  {
    date: "27/04",
    device: "TV Recepção",
    campaign: "Campanha Abril",
    media: "Banner Promoção",
    views: 245,
    status: "success",
  },
  {
    date: "27/04",
    device: "TV Sala de Espera",
    campaign: "Institucional",
    media: "Vídeo Institucional",
    views: 180,
    status: "success",
  },
  {
    date: "27/04",
    device: "Totem Loja 01",
    campaign: "Promoção Especial",
    media: "Oferta Relâmpago",
    views: 0,
    status: "error",
  },
  {
    date: "26/04",
    device: "TV Restaurante",
    campaign: "Cardápio Digital",
    media: "Cardápio Almoço",
    views: 320,
    status: "success",
  },
  {
    date: "26/04",
    device: "TV Academia",
    campaign: "Treinos do Dia",
    media: "Slide Produtos",
    views: 95,
    status: "partial",
  },
];

export default function Relatorios() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h2 className="text-xl font-bold">Relatórios</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Exportar CSV
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Exportar PDF
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Input type="date" className="w-auto" defaultValue="2026-04-21" />
        <Input type="date" className="w-auto" defaultValue="2026-04-27" />
        <Select defaultValue="all">
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Campanha" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {mockCampaigns.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select defaultValue="all">
          <SelectTrigger className="w-40">
            <SelectValue placeholder="TV" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {mockDevices.map((d) => (
              <SelectItem key={d.id} value={d.id}>
                {d.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total de Exibições" value="29.550" icon={Eye} />
        <StatsCard
          title="Campanha Mais Exibida"
          value="Camp. Abril"
          icon={Megaphone}
        />
        <StatsCard
          title="TV Mais Ativa"
          value="TV Restaurante"
          icon={Monitor}
        />
        <StatsCard
          title="TVs com Falha"
          value="2"
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
                  data={mockViewsPerDay}
                  margin={{ top: 5, right: 5, left: -20, bottom: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(220, 13%, 91%)"
                  />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar
                    dataKey="views"
                    fill="hsl(221, 83%, 53%)"
                    radius={[4, 4, 0, 0]}
                  />
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
                    data={deviceStatus}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {deviceStatus.map((entry, i) => (
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
                  <TableHead className="hidden md:table-cell">
                    Campanha
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">Mídia</TableHead>
                  <TableHead>Exibições</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData.map((row, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-sm">{row.date}</TableCell>
                    <TableCell className="text-sm font-medium">
                      {row.device}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm">
                      {row.campaign}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm">
                      {row.media}
                    </TableCell>
                    <TableCell className="text-sm font-medium">
                      {row.views.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={row.status} />
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
