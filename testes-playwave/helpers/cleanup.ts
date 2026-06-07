/**
 * cleanup.ts — coletor de recursos criados nos testes para teardown.
 *
 * Cada teste registra IDs no Tracker; no afterEach/afterAll chamamos
 * `tracker.cleanup(api)` que remove na ordem inversa de dependência.
 * Falhas de remoção são logadas mas não derrubam o teste (best-effort).
 */
import type { Api } from "./api.js";

type Kind = "campaign" | "spotSchedule" | "device";

export class Tracker {
  private items: { kind: Kind; id: string }[] = [];

  add(kind: Kind, id: string) {
    if (id) this.items.unshift({ kind, id }); // LIFO
    return id;
  }

  campaign(id: string) {
    return this.add("campaign", id);
  }
  spotSchedule(id: string) {
    return this.add("spotSchedule", id);
  }
  device(id: string) {
    return this.add("device", id);
  }

  async cleanup(api: Api): Promise<void> {
    for (const it of this.items) {
      try {
        if (it.kind === "campaign") await api.deleteCampaign(it.id);
        else if (it.kind === "spotSchedule") await api.deleteSpotSchedule(it.id);
        else if (it.kind === "device") await api.deleteDevice(it.id);
      } catch (err: any) {
        console.warn(`[cleanup] falhou ${it.kind}=${it.id}: ${err?.message}`);
      }
    }
    this.items = [];
  }
}
