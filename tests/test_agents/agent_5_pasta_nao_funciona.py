#!/usr/bin/env python3
"""
🤖 AGENTE #5: PASTA NÃO FUNCIONA

Testa se pastas de música estão funcionando corretamente.

Bug: Criar pasta de música e agendar, mas não toca nada.
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

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_USERNAME = os.getenv("API_USERNAME", "admin@playwave.com")
API_PASSWORD = os.getenv("API_PASSWORD", "admin123")


@dataclass
class TestScenario:
    name: str
    status: str = "PENDING"
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
    status: str
    scenarios: List[TestScenario]
    recommendations: List[str]
    debug_info: Dict


class Agent5PastaNaoFunciona:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.folder_id = None
        self.track_ids = []
        self.playlist_id = None
        self.scenarios = []
        self.recommendations = []
        self.debug_info = {}

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "DEBUG": "🔍"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")

    def run_scenario(self, name: str, func):
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
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": API_USERNAME, "password": API_PASSWORD}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token

    def create_folder(self, name: str = "Manhã") -> str:
        """Cria pasta de música"""
        now = datetime.now()
        folder_data = {
            "name": f"🤖 {name} - Agent 5",
            "description": "Pasta de teste criada pelo agente",
            "status": "active",
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(days=30)).isoformat()
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/audio/folders",
            json=folder_data
        )
        response.raise_for_status()
        self.folder_id = response.json()["id"]
        self.debug_info["folder"] = response.json()
        return self.folder_id

    def create_tracks(self, count: int = 3) -> List[str]:
        """Cria faixas de teste"""
        track_ids = []
        for i in range(count):
            track_data = {
                "name": f"Música Manhã {i+1}",
                "file_url": f"/audio/morning_{i+1}.mp3",
                "duration_seconds": 180,
                "status": "active",
                "category": "music"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/audio/tracks",
                json=track_data
            )
            response.raise_for_status()
            track_ids.append(response.json()["id"])
        
        self.track_ids = track_ids
        return track_ids

    def add_tracks_to_folder(self) -> int:
        """Adiciona faixas à pasta"""
        for idx, track_id in enumerate(self.track_ids):
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/audio/folders/{self.folder_id}/tracks",
                json={"track_id": track_id, "order_index": idx}
            )
            response.raise_for_status()
        
        return len(self.track_ids)

    def validate_folder_has_tracks(self) -> bool:
        """Valida se pasta tem faixas"""
        response = self.session.get(
            f"{API_BASE_URL}/api/v1/audio/folders/{self.folder_id}/tracks"
        )
        response.raise_for_status()
        tracks = response.json()
        
        assert len(tracks) > 0, "Pasta está vazia (sem faixas)!"
        assert len(tracks) == len(self.track_ids), \
            f"Quantidade incorreta. Esperado: {len(self.track_ids)}, Atual: {len(tracks)}"
        
        # Validar status das faixas
        for track in tracks:
            assert track["track"]["status"] == "active", \
                f"Faixa {track['track']['name']} não está ativa"
        
        self.debug_info["folder_tracks"] = tracks
        return True

    def create_playlist(self) -> str:
        """Cria playlist para vincular a pasta"""
        playlist_data = {
            "name": "🤖 Playlist Agent 5",
            "status": "active",
            "shuffle_enabled": False
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/audio/playlists",
            json=playlist_data
        )
        response.raise_for_status()
        self.playlist_id = response.json()["id"]
        return self.playlist_id

    def schedule_folder(self) -> str:
        """Agenda pasta para horário específico"""
        now = datetime.now()
        
        # Agenda para horário atual (06:00-12:00, Seg-Sex)
        # Mas ajusta para garantir que está ativo AGORA
        schedule_data = {
            "folder_id": self.folder_id,
            "start_time": "00:00",  # Todo o dia para teste
            "end_time": "23:59",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7],  # Todos os dias
            "priority": 1,
            "play_mode": "sequential",
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(days=30)).isoformat()
        }
        
        response = self.session.post(
            f"{API_BASE_URL}/api/v1/audio/playlists/{self.playlist_id}/folder-schedules",
            json=schedule_data
        )
        response.raise_for_status()
        
        schedule = response.json()
        self.debug_info["folder_schedule"] = schedule
        return schedule["id"]

    def validate_schedule(self) -> bool:
        """Valida agendamento da pasta"""
        response = self.session.get(
            f"{API_BASE_URL}/api/v1/audio/playlists/{self.playlist_id}/folder-schedules"
        )
        response.raise_for_status()
        schedules = response.json()
        
        assert len(schedules) > 0, "Nenhum agendamento encontrado!"
        
        schedule = schedules[0]
        assert schedule["folder_id"] == self.folder_id, "Pasta não corresponde"
        assert schedule.get("start_time"), "Horário de início não definido"
        assert schedule.get("end_time"), "Horário de fim não definido"
        assert schedule.get("days_of_week"), "Dias da semana não definidos"
        
        return True

    def simulate_folder_resolution(self) -> Dict:
        """Simula resolução de pasta ativa (lógica do frontend)"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.isoweekday()  # 1 = Segunda, 7 = Domingo
        
        schedule = self.debug_info.get("folder_schedule", {})
        
        # Validar horário
        start_time = schedule.get("start_time", "00:00")
        end_time = schedule.get("end_time", "23:59")
        
        in_time_range = start_time <= current_time <= end_time
        
        # Validar dia da semana
        days_of_week = schedule.get("days_of_week", [])
        in_day_range = current_day in days_of_week if days_of_week else True
        
        # Validar período
        starts_at = schedule.get("starts_at")
        ends_at = schedule.get("ends_at")
        
        in_date_range = True
        if starts_at:
            in_date_range = in_date_range and (now >= datetime.fromisoformat(starts_at.replace("Z", "+00:00")))
        if ends_at:
            in_date_range = in_date_range and (now <= datetime.fromisoformat(ends_at.replace("Z", "+00:00")))
        
        is_active = in_time_range and in_day_range and in_date_range
        
        result = {
            "current_time": current_time,
            "current_day": current_day,
            "in_time_range": in_time_range,
            "in_day_range": in_day_range,
            "in_date_range": in_date_range,
            "is_active": is_active,
            "should_play": is_active and len(self.debug_info.get("folder_tracks", [])) > 0
        }
        
        self.debug_info["resolution"] = result
        return result

    def validate_resolution(self, resolution: Dict) -> bool:
        """Valida se pasta deveria estar ativa"""
        assert resolution["is_active"], \
            f"Pasta não está ativa! Motivo: " \
            f"Horário: {resolution['in_time_range']}, " \
            f"Dia: {resolution['in_day_range']}, " \
            f"Período: {resolution['in_date_range']}"
        
        assert resolution["should_play"], \
            "Pasta deveria estar tocando mas não está configurada corretamente"
        
        return True

    def test_tracks_status(self) -> bool:
        """Testa se todas as faixas estão ativas"""
        tracks = self.debug_info.get("folder_tracks", [])
        
        for track in tracks:
            track_obj = track["track"]
            assert track_obj["status"] == "active", \
                f"Faixa '{track_obj['name']}' está {track_obj['status']}, deveria estar 'active'"
        
        return True

    def cleanup(self):
        """Limpa recursos de teste"""
        try:
            if self.folder_id:
                self.session.delete(f"{API_BASE_URL}/api/v1/audio/folders/{self.folder_id}")
            if self.playlist_id:
                self.session.delete(f"{API_BASE_URL}/api/v1/audio/playlists/{self.playlist_id}")
            for track_id in self.track_ids:
                self.session.delete(f"{API_BASE_URL}/api/v1/audio/tracks/{track_id}")
            self.log("Limpeza concluída", "DEBUG")
        except Exception as e:
            self.log(f"Erro na limpeza: {e}", "WARNING")

    def run(self) -> AgentReport:
        self.log("=" * 60, "INFO")
        self.log("🤖 AGENTE #5: PASTA NÃO FUNCIONA", "INFO")
        self.log("=" * 60, "INFO")
        
        try:
            self.run_scenario("Autenticar na API", self.authenticate)
            self.run_scenario("Criar pasta 'Manhã'", lambda: self.create_folder("Manhã"))
            self.run_scenario("Criar 3 faixas de teste", lambda: self.create_tracks(3))
            self.run_scenario("Adicionar faixas à pasta", self.add_tracks_to_folder)
            self.run_scenario("Validar pasta tem faixas", self.validate_folder_has_tracks)
            self.run_scenario("Criar playlist", self.create_playlist)
            self.run_scenario("Agendar pasta (00:00-23:59, todos os dias)", self.schedule_folder)
            self.run_scenario("Validar agendamento", self.validate_schedule)
            
            # Resolução (lógica frontend)
            resolution = self.simulate_folder_resolution()
            self.run_scenario(
                "Simular resolução de pasta ativa",
                lambda: resolution
            )
            
            self.run_scenario(
                "Validar pasta deveria estar ativa",
                lambda: self.validate_resolution(resolution)
            )
            
            self.run_scenario(
                "Validar status das faixas",
                self.test_tracks_status
            )
            
        except Exception as e:
            self.log(f"Erro crítico: {e}", "ERROR")
        finally:
            self.cleanup()
        
        self.generate_recommendations()
        status = self.determine_status()
        
        report = AgentReport(
            agent_id=5,
            bug_name="Pasta não funciona",
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
        failed = [s for s in self.scenarios if s.status == "FAILED"]
        
        if not failed:
            self.recommendations.append("✅ Pasta funcionando corretamente!")
            return
        
        for scenario in failed:
            if "pasta está vazia" in scenario.error.lower():
                self.recommendations.append(
                    "❌ Pasta sem faixas! Verificar associação de tracks na pasta"
                )
            
            if "não está ativa" in scenario.error.lower():
                self.recommendations.append(
                    "❌ Pasta fora do período! Verificar:"
                )
                self.recommendations.append(
                    "  • Horário (start_time/end_time)"
                )
                self.recommendations.append(
                    "  • Dias da semana (days_of_week)"
                )
                self.recommendations.append(
                    "  • Período (starts_at/ends_at)"
                )
            
            if "faixa" in scenario.error.lower() and "status" in scenario.error.lower():
                self.recommendations.append(
                    "Verificar status das faixas (devem estar 'active')"
                )
            
            if "agendamento" in scenario.error.lower():
                self.recommendations.append(
                    "Verificar endpoint de folder-schedules"
                )
                self.recommendations.append(
                    "Validar lógica do resolveActiveFolderForNow()"
                )

    def determine_status(self) -> str:
        failed = sum(1 for s in self.scenarios if s.status == "FAILED")
        total = len(self.scenarios)
        
        if failed == 0:
            return "PASSED"
        elif failed < total // 2:
            return "WARNING"
        else:
            return "FAILED"

    def print_summary(self, report: AgentReport):
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
        
        # Info da resolução
        if "resolution" in report.debug_info:
            res = report.debug_info["resolution"]
            self.log(f"\n🔍 Resolução de Pasta:", "INFO")
            self.log(f"  Horário atual: {res['current_time']}", "INFO")
            self.log(f"  Dia atual: {res['current_day']}", "INFO")
            self.log(f"  Está ativa: {res['is_active']}", "INFO")
            self.log(f"  Deveria tocar: {res['should_play']}", "INFO")
        
        if report.recommendations:
            self.log("\n💡 RECOMENDAÇÕES:", "INFO")
            for rec in report.recommendations:
                self.log(f"  • {rec}", "INFO")

    def save_report(self, report: AgentReport):
        os.makedirs("reports", exist_ok=True)
        filepath = "reports/agent_5_report.json"
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        self.log(f"Relatório salvo em: {filepath}", "SUCCESS")


if __name__ == "__main__":
    agent = Agent5PastaNaoFunciona()
    report = agent.run()
    sys.exit(0 if report.status == "PASSED" else 1)
