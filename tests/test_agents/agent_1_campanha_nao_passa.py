#!/usr/bin/env python3
"""
🤖 AGENTE #1: CAMPANHA NÃO PASSA NO PLAYER

Testa se campanhas criadas aparecem corretamente no player.

Bug: Ao criar campanha e adicionar mídias, o player não exibe nada.
Prioridade: P0 (BLOQUEADOR)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

# Configurações
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_USERNAME = os.getenv("API_USERNAME", "admin@playwave.com")
API_PASSWORD = os.getenv("API_PASSWORD", "admin123")


@dataclass
class TestScenario:
    name: str
    status: str = "PENDING"  # PASSED, FAILED, SKIPPED
    duration_ms: int = 0
    error: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class AgentReport:
    agent_id: int
    bug_name: str
    priority: str
    timestamp: str
    status: str  # PASSED, FAILED, WARNING
    scenarios: List[TestScenario]
    recommendations: List[str]
    debug_info: Dict


class Agent1CampanhaNaoPassa:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.device_id = None
        self.campaign_id = None
        self.media_ids = []
        self.scenarios = []
        self.recommendations = []
        self.debug_info = {}

    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "DEBUG": "🔍"
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")

    def run_scenario(self, name: str, func):
        """Executa um cenário de teste"""
        self.log(f"Cenário: {name}", "INFO")
        scenario = TestScenario(name=name)
        start = time.time()
        
        try:
            result = func()
            scenario.status = "PASSED"
            scenario.actual = str(result)
            self.log(f"✓ {name}", "SUCCESS")
        except AssertionError as e:
            scenario.status = "FAILED"
            scenario.error = str(e)
            self.log(f"✗ {name}: {e}", "ERROR")
        except Exception as e:
            scenario.status = "FAILED"
            scenario.error = f"Erro inesperado: {str(e)}"
            self.log(f"✗ {name}: {e}", "ERROR")
        finally:
            scenario.duration_ms = int((time.time() - start) * 1000)
            self.scenarios.append(scenario)

    def authenticate(self) -> str:
        """Autentica na API"""
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": API_USERNAME, "password": API_PASSWORD}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token

    def create_test_campaign(self) -> str:
        """Cria campanha de teste"""
        now = datetime.now()
        campaign_data = {
            "name": f"🤖 Teste Agent 1 - {now.strftime('%H:%M:%S')}",
            "status": "active",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
            "schedule_start_time": "00:00",
            "schedule_end_time": "23:59"
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/campaigns",
            json=campaign_data
        )
        response.raise_for_status()
        self.campaign_id = response.json()["id"]
        self.debug_info["campaign"] = response.json()
        return self.campaign_id

    def upload_test_media(self, count: int = 3) -> List[str]:
        """Cria mídias de teste (mock)"""
        media_ids = []
        for i in range(count):
            media_data = {
                "name": f"Mídia Teste {i+1}",
                "type": "video",
                "file_url": f"/media/test_{i+1}.mp4",
                "duration_seconds": 30,
                "status": "active"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/media",
                json=media_data
            )
            response.raise_for_status()
            media_ids.append(response.json()["id"])
        
        self.media_ids = media_ids
        return media_ids

    def add_media_to_campaign(self) -> int:
        """Adiciona mídias à campanha"""
        items = [
            {
                "media_id": media_id,
                "order_index": idx,
                "display_duration_seconds": 30
            }
            for idx, media_id in enumerate(self.media_ids)
        ]
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/campaigns/{self.campaign_id}/items/bulk",
            json={"items": items}
        )
        response.raise_for_status()
        added = len(response.json().get("items", []))
        self.debug_info["playlist_items"] = response.json()
        return added

    def create_test_device(self) -> str:
        """Cria dispositivo de teste"""
        device_data = {
            "name": f"🤖 Device Agent 1",
            "status": "online",
            "is_active": True,
            "location": "Teste",
            "group": "Agentes"
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/devices",
            json=device_data
        )
        response.raise_for_status()
        self.device_id = response.json()["id"]
        self.debug_info["device"] = response.json()
        return self.device_id

    def associate_device_to_campaign(self) -> bool:
        """Associa dispositivo à campanha"""
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/campaigns/{self.campaign_id}/devices",
            json={"device_ids": [self.device_id]}
        )
        response.raise_for_status()
        return True

    def get_device_playlist(self) -> Dict:
        """Busca playlist que o player receberia"""
        pairing_code = self.debug_info["device"]["pairing_code"]
        
        # Simula player solicitando playlist
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/devices/pair",
            json={"pairing_code": pairing_code}
        )
        response.raise_for_status()
        device_token = response.json()["device_token"]
        
        # Busca playlist com token do device
        headers = {"X-Device-Token": device_token}
        response = self.session.get(
            f"{API_BASE_URL}/api/v1/devices/{self.device_id}/playlist",
            headers=headers
        )
        response.raise_for_status()
        playlist = response.json()
        self.debug_info["playlist"] = playlist
        return playlist

    def validate_playlist(self, playlist: Dict) -> bool:
        """Valida se playlist está correta"""
        assert playlist is not None, "Playlist é None"
        
        campaign = playlist.get("campaign")
        assert campaign is not None, "Campanha não retornada"
        assert campaign["id"] == self.campaign_id, "ID da campanha diferente"
        
        items = playlist.get("playlist", {}).get("items", [])
        assert len(items) > 0, f"Playlist vazia! Esperado: {len(self.media_ids)}, Atual: 0"
        assert len(items) == len(self.media_ids), \
            f"Quantidade incorreta. Esperado: {len(self.media_ids)}, Atual: {len(items)}"
        
        # Valida cada item
        for idx, item in enumerate(items):
            assert item["media"]["status"] == "active", \
                f"Mídia {idx} não está ativa: {item['media']['status']}"
            assert item["media"]["id"] in self.media_ids, \
                f"Mídia {idx} não pertence à campanha"
        
        return True

    def test_filters(self, playlist: Dict) -> bool:
        """Testa se filtros de agendamento estão corretos"""
        campaign = playlist["campaign"]
        
        # Valida período da campanha
        now = datetime.now()
        if campaign.get("start_date"):
            start_date = datetime.fromisoformat(campaign["start_date"].replace("Z", "+00:00"))
            assert start_date <= now, "Campanha ainda não começou"
        
        if campaign.get("end_date"):
            end_date = datetime.fromisoformat(campaign["end_date"].replace("Z", "+00:00"))
            assert end_date >= now, "Campanha já terminou"
        
        # Valida horário diário
        current_time = now.strftime("%H:%M")
        if campaign.get("schedule_start_time"):
            assert current_time >= campaign["schedule_start_time"], \
                "Fora do horário de início"
        
        if campaign.get("schedule_end_time"):
            assert current_time <= campaign["schedule_end_time"], \
                "Fora do horário de término"
        
        return True

    def cleanup(self):
        """Limpa recursos de teste"""
        try:
            if self.campaign_id:
                self.session.delete(f"{API_BASE_URL}/api/v1/campaigns/{self.campaign_id}")
            if self.device_id:
                self.session.delete(f"{API_BASE_URL}/api/v1/devices/{self.device_id}")
            for media_id in self.media_ids:
                self.session.delete(f"{API_BASE_URL}/api/v1/media/{media_id}")
            self.log("Limpeza concluída", "DEBUG")
        except Exception as e:
            self.log(f"Erro na limpeza: {e}", "WARNING")

    def run(self) -> AgentReport:
        """Executa todos os testes"""
        self.log("=" * 60, "INFO")
        self.log("🤖 AGENTE #1: CAMPANHA NÃO PASSA NO PLAYER", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            # Autenticação
            self.run_scenario("Autenticar na API", self.authenticate)
            
            # Criar campanha
            self.run_scenario("Criar campanha de teste", self.create_test_campaign)
            
            # Upload de mídias
            self.run_scenario(
                "Criar 3 mídias de teste",
                lambda: self.upload_test_media(3)
            )
            
            # Adicionar mídias na campanha
            self.run_scenario(
                "Adicionar mídias à campanha",
                self.add_media_to_campaign
            )
            
            # Criar dispositivo
            self.run_scenario("Criar dispositivo de teste", self.create_test_device)
            
            # Associar dispositivo
            self.run_scenario(
                "Associar dispositivo à campanha",
                self.associate_device_to_campaign
            )
            
            # Buscar playlist
            self.run_scenario(
                "Buscar playlist do player",
                self.get_device_playlist
            )
            
            # Validar playlist
            playlist = self.debug_info.get("playlist")
            if playlist:
                self.run_scenario(
                    "Validar conteúdo da playlist",
                    lambda: self.validate_playlist(playlist)
                )
                
                self.run_scenario(
                    "Validar filtros de agendamento",
                    lambda: self.test_filters(playlist)
                )
            
        except Exception as e:
            self.log(f"Erro crítico: {e}", "ERROR")
        finally:
            self.cleanup()
        
        # Gerar recomendações
        self.generate_recommendations()
        
        # Determinar status geral
        status = self.determine_status()
        
        # Criar relatório
        report = AgentReport(
            agent_id=1,
            bug_name="Campanha não passa no player",
            priority="P0",
            timestamp=datetime.now().isoformat(),
            status=status,
            scenarios=self.scenarios,
            recommendations=self.recommendations,
            debug_info=self.debug_info
        )
        
        self.print_summary(report)
        self.save_report(report)
        
        return report

    def generate_recommendations(self):
        """Gera recomendações baseado nos resultados"""
        failed = [s for s in self.scenarios if s.status == "FAILED"]
        
        if not failed:
            self.recommendations.append("✅ Todos os cenários passaram! Bug corrigido.")
            return
        
        for scenario in failed:
            if "playlist vazia" in scenario.error.lower():
                self.recommendations.append(
                    "Verificar se dispositivo está corretamente associado à campanha"
                )
                self.recommendations.append(
                    "Verificar se mídias estão em status 'active'"
                )
            
            if "campanha não retornada" in scenario.error.lower():
                self.recommendations.append(
                    "Verificar lógica de associação dispositivo ↔ campanha"
                )
            
            if "fora do horário" in scenario.error.lower():
                self.recommendations.append(
                    "Ajustar agendamento da campanha (start_time/end_time)"
                )
                self.recommendations.append(
                    "Verificar timezone do servidor vs cliente"
                )
            
            if "campanha já terminou" in scenario.error.lower():
                self.recommendations.append(
                    "Verificar end_date da campanha (pode estar no passado)"
                )

    def determine_status(self) -> str:
        """Determina status geral do agente"""
        failed = sum(1 for s in self.scenarios if s.status == "FAILED")
        total = len(self.scenarios)
        
        if failed == 0:
            return "PASSED"
        elif failed < total // 2:
            return "WARNING"
        else:
            return "FAILED"

    def print_summary(self, report: AgentReport):
        """Imprime resumo dos testes"""
        self.log("=" * 60, "INFO")
        self.log("📊 RESUMO DO TESTE", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for s in report.scenarios if s.status == "PASSED")
        failed = sum(1 for s in report.scenarios if s.status == "FAILED")
        total = len(report.scenarios)
        
        self.log(f"Status Geral: {report.status}", "INFO")
        self.log(f"Aprovados: {passed}/{total}", "SUCCESS")
        if failed > 0:
            self.log(f"Falhados: {failed}/{total}", "ERROR")
        
        if report.recommendations:
            self.log("\n💡 RECOMENDAÇÕES:", "INFO")
            for rec in report.recommendations:
                self.log(f"  • {rec}", "INFO")

    def save_report(self, report: AgentReport):
        """Salva relatório em JSON"""
        os.makedirs("reports", exist_ok=True)
        filepath = "reports/agent_1_report.json"
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        self.log(f"Relatório salvo em: {filepath}", "SUCCESS")


if __name__ == "__main__":
    agent = Agent1CampanhaNaoPassa()
    report = agent.run()
    
    # Exit code baseado no resultado
    sys.exit(0 if report.status == "PASSED" else 1)
