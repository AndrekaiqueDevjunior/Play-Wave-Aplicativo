import React from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  RefreshCw,
  Monitor,
  Wifi,
  WifiOff,
  AlertTriangle,
  Download,
} from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import { useQuery } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import moment from "moment";
import { cn } from "@/lib/utils";

const statusPriority = { error: 0, offline: 1, syncing: 2, online: 3 };

export default function Monitoramento() {
  const { data: devices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => base44.entities.Device.list(),
  });

  const sortedDevices = [...devices].sort(
    (a, b) => statusPriority[a.status] - statusPriority[b.status],
  );
  const online = devices.filter((d) => d.status === "online").length;
  const offline = devices.filter((d) => d.status === "offline").length;
  const errors = devices.filter((d) => d.status === "error").length;
  const syncing = devices.filter((d) => d.status === "syncing").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Monitoramento em Tempo Real</h2>
          <p className="text-sm text-muted-foreground">
            Acompanhe o status de todos os dispositivos
          </p>
        </div>
        <Button variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Forçar Sincronização
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-3">
            <Wifi className="w-5 h-5 text-emerald-500" />
            <div>
              <p className="text-2xl font-bold">{online}</p>
              <p className="text-xs text-muted-foreground">Online</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 border-l-4 border-l-red-500">
          <div className="flex items-center gap-3">
            <WifiOff className="w-5 h-5 text-red-500" />
            <div>
              <p className="text-2xl font-bold">{offline}</p>
              <p className="text-xs text-muted-foreground">Offline</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center gap-3">
            <Download className="w-5 h-5 text-amber-500" />
            <div>
              <p className="text-2xl font-bold">{syncing}</p>
              <p className="text-xs text-muted-foreground">Sincronizando</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 border-l-4 border-l-red-400">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-2xl font-bold">{errors}</p>
              <p className="text-xs text-muted-foreground">Com Erro</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedDevices.map((device) => (
          <Card
            key={device.id}
            className={cn(
              "p-4 border-l-4",
              device.status === "online"
                ? "border-l-emerald-500"
                : device.status === "error"
                  ? "border-l-red-500"
                  : device.status === "syncing"
                    ? "border-l-amber-500"
                    : "border-l-red-400",
            )}
          >
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
                <Monitor className="w-5 h-5 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold truncate">
                    {device.name}
                  </h3>
                  <StatusBadge status={device.status} />
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  <div>
                    <span className="text-muted-foreground">Último ping:</span>{" "}
                    <span className="font-medium">
                      {moment(device.last_connection).fromNow()}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Campanha:</span>{" "}
                    <span className="font-medium">
                      {device.current_campaign || "Nenhuma"}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Local:</span>{" "}
                    <span className="font-medium">{device.location}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">IP:</span>{" "}
                    <span className="font-medium font-mono">
                      {device.ip_address}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
