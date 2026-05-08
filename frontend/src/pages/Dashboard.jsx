import React from "react";
import { Monitor, Wifi, WifiOff, Megaphone, Image, Eye } from "lucide-react";
import StatsCard from "@/components/shared/StatsCard";
import ViewsChart from "@/components/dashboard/ViewChart";
import RecentDevices from "@/components/dashboard/RecentDevices";
import ActiveCampaigns from "@/components/dashboard/ActiveCampaigns";
import AlertsList from "@/components/dashboard/AlertsList";
import { useQuery } from "@tanstack/react-query";
import { buscarStats } from "@/api/dashboard";

export default function Dashboard() {
  const { data: stats = {}, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: buscarStats,
  });

  const devices = stats.devices || {};
  const campaigns = stats.campaigns || {};
  const media = stats.media || {};
  const today = stats.today || {};

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatsCard title="Total TVs" value={isLoading ? "..." : devices.total || 0} icon={Monitor} />
        <StatsCard
          title="TVs Online"
          value={isLoading ? "..." : devices.online || 0}
          icon={Wifi}
          iconClassName="bg-emerald-100"
        />
        <StatsCard
          title="TVs Offline"
          value={isLoading ? "..." : devices.offline || 0}
          icon={WifiOff}
          iconClassName="bg-red-100"
        />
        <StatsCard
          title="Campanhas Ativas"
          value={isLoading ? "..." : campaigns.active || 0}
          icon={Megaphone}
        />
        <StatsCard title="Mídias" value={isLoading ? "..." : media.total || 0} icon={Image} />
        <StatsCard
          title="Exibições Hoje"
          value={isLoading ? "..." : today.playbacks || 0}
          icon={Eye}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ViewsChart data={stats.views_per_day || []} />
        </div>
        <AlertsList alerts={stats.alerts || []} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentDevices devices={stats.recent_devices || []} />
        <ActiveCampaigns campaigns={stats.active_campaigns || []} />
      </div>
    </div>
  );
}
