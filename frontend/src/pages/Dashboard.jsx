import React from "react";
import { Monitor, Wifi, WifiOff, Megaphone, Image, Eye } from "lucide-react";
import StatsCard from "@/components/shared/StatsCard";
import ViewsChart from "@/components/dashboard/ViewChart";
import RecentDevices from "@/components/dashboard/RecentDevices";
import ActiveCampaigns from "@/components/dashboard/ActiveCampaigns";
import AlertsList from "@/components/dashboard/AlertsList";
import { useQuery } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";

export default function Dashboard() {
  const { data: devices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => base44.entities.Device.list(),
  });
  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => base44.entities.Campaign.list(),
  });
  const { data: media = [] } = useQuery({
    queryKey: ["media"],
    queryFn: () => base44.entities.Media.list(),
  });

  const onlineCount = devices.filter((d) => d.status === "online").length;
  const offlineCount = devices.filter((d) => d.status !== "online").length;
  const activeCampaigns = campaigns.filter((c) => c.status === "active").length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatsCard title="Total TVs" value={devices.length} icon={Monitor} />
        <StatsCard
          title="TVs Online"
          value={onlineCount}
          icon={Wifi}
          iconClassName="bg-emerald-100"
        />
        <StatsCard
          title="TVs Offline"
          value={offlineCount}
          icon={WifiOff}
          iconClassName="bg-red-100"
        />
        <StatsCard
          title="Campanhas Ativas"
          value={activeCampaigns}
          icon={Megaphone}
        />
        <StatsCard title="Mídias" value={media.length} icon={Image} />
        <StatsCard
          title="Exibições Hoje"
          value="1.890"
          icon={Eye}
          trend={12}
          trendLabel="vs ontem"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ViewsChart />
        </div>
        <AlertsList />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentDevices />
        <ActiveCampaigns />
      </div>
    </div>
  );
}
