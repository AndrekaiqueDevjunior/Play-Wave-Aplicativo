#!/bin/bash

###############################################################################
# 🤖 EXECUTAR TODOS OS AGENTES DE TESTE
#
# Executa os agentes sequencialmente e gera relatório consolidado.
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🤖 EXECUTANDO AGENTES DE TESTE - BUGS CRÍTICOS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL=0
PASSED=0
FAILED=0

# Criar diretório de relatórios
mkdir -p reports

# Função para executar agente
run_agent() {
    local agent_num=$1
    local agent_name=$2
    local agent_file="agent_${agent_num}_*.py"
    
    TOTAL=$((TOTAL + 1))
    
    echo ""
    echo "───────────────────────────────────────────────────────────────"
    echo -e "${BLUE}Executando Agente #${agent_num}: ${agent_name}${NC}"
    echo "───────────────────────────────────────────────────────────────"
    
    if python3 $agent_file; then
        echo -e "${GREEN}✅ Agente #${agent_num} PASSOU${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ Agente #${agent_num} FALHOU${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Executar cada agente
echo "📋 Executando agentes P0 (bloqueadores)..."
echo ""

run_agent 1 "Campanha Não Passa"
run_agent 4 "Spot Bloqueia Playlist"
# run_agent 5 "Pasta Não Funciona"  # Implementar
# run_agent 6 "Comandos Não Funcionam"  # Implementar

echo ""
echo "📋 Executando agentes P1/P2..."
echo ""

# run_agent 2 "Player Reinicia"  # Implementar
# run_agent 3 "Hierarquia Agendamento"  # Implementar
# run_agent 7 "Prioridade"  # Implementar

# Gerar relatório consolidado
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 RELATÓRIO CONSOLIDADO"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Total de agentes: $TOTAL"
echo -e "${GREEN}✅ Passaram: $PASSED${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Falharam: $FAILED${NC}"
fi

echo ""

# Gerar HTML consolidado
python3 << 'PYTHON_SCRIPT'
import json
import glob
from datetime import datetime

reports = []
for filepath in glob.glob("reports/agent_*_report.json"):
    with open(filepath, "r") as f:
        reports.append(json.load(f))

reports.sort(key=lambda r: r["agent_id"])

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório de Testes - PlayWave</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .agent-card {{
            background: white;
            margin-bottom: 20px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .agent-header {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .agent-header.passed {{
            border-left: 4px solid #28a745;
        }}
        .agent-header.failed {{
            border-left: 4px solid #dc3545;
        }}
        .agent-header.warning {{
            border-left: 4px solid #ffc107;
        }}
        .scenario {{
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        .scenario:last-child {{
            border-bottom: none;
        }}
        .scenario-name {{
            font-weight: 500;
            margin-bottom: 5px;
        }}
        .scenario-meta {{
            font-size: 13px;
            color: #666;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge.passed {{
            background: #d4edda;
            color: #155724;
        }}
        .badge.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .badge.p0 {{
            background: #dc3545;
            color: white;
        }}
        .badge.p1 {{
            background: #ffc107;
            color: #333;
        }}
        .badge.p2 {{
            background: #17a2b8;
            color: white;
        }}
        .recommendations {{
            padding: 20px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            margin: 20px;
            border-radius: 4px;
        }}
        .recommendations h4 {{
            margin: 0 0 10px 0;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Relatório de Testes - PlayWave</h1>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <h3>Total de Agentes</h3>
            <div class="value">{len(reports)}</div>
        </div>
        <div class="stat-card">
            <h3>Aprovados</h3>
            <div class="value" style="color: #28a745;">{sum(1 for r in reports if r["status"] == "PASSED")}</div>
        </div>
        <div class="stat-card">
            <h3>Falhados</h3>
            <div class="value" style="color: #dc3545;">{sum(1 for r in reports if r["status"] == "FAILED")}</div>
        </div>
        <div class="stat-card">
            <h3>Avisos</h3>
            <div class="value" style="color: #ffc107;">{sum(1 for r in reports if r["status"] == "WARNING")}</div>
        </div>
    </div>
"""

for report in reports:
    status_class = report["status"].lower()
    priority_class = report["priority"].lower()
    
    html += f"""
    <div class="agent-card">
        <div class="agent-header {status_class}">
            <h2>
                Agente #{report["agent_id"]}: {report["bug_name"]}
                <span class="badge {priority_class}">{report["priority"]}</span>
                <span class="badge {status_class}">{report["status"]}</span>
            </h2>
        </div>
    """
    
    for scenario in report["scenarios"]:
        scenario_status = scenario["status"].lower()
        html += f"""
        <div class="scenario">
            <div class="scenario-name">
                <span class="badge {scenario_status}">{scenario["status"]}</span>
                {scenario["name"]}
            </div>
            <div class="scenario-meta">
                Duração: {scenario["duration_ms"]}ms
        """
        
        if scenario.get("error"):
            html += f" | ❌ Erro: {scenario['error']}"
        
        html += """
            </div>
        </div>
        """
    
    if report.get("recommendations"):
        html += """
        <div class="recommendations">
            <h4>💡 Recomendações</h4>
            <ul>
        """
        for rec in report["recommendations"]:
            html += f"<li>{rec}</li>"
        html += """
            </ul>
        </div>
        """
    
    html += "</div>"

html += """
</body>
</html>
"""

with open("reports/summary.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Relatório HTML gerado: reports/summary.html")
PYTHON_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Exit code
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  Alguns testes falharam. Verifique os relatórios.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Todos os testes passaram!${NC}"
    exit 0
fi
