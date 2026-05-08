/**
 * lib/api.js — LEGADO: mantido para compatibilidade com imports existentes.
 * Novos arquivos devem importar diretamente de '@/api'.
 *
 * @deprecated Use '@/api' ou os módulos específicos em '@/api/dispositivos', '@/api/campanhas', etc.
 */
export {
  apiFetch,
  isApiConfigurada as isApiConfigured,
  getBaseUrl as getApiBaseUrl,
  verificarSaude as checkApiHealth,
} from "@/api/http";

export {
  solicitarPareamento as pairRequest,
  verificarStatusPareamento as getPairStatus,
  confirmarPareamento as confirmPairing,
  buscarPlaylistDispositivo as getDevicePlaylist,
  enviarHeartbeat as sendHeartbeat,
  buscarMetricasDispositivo as getDeviceMetrics,
  enviarComando as sendDeviceCommand,
} from "@/api/dispositivos";

export { publicarCampanha as publishCampaign } from "@/api/campanhas";
