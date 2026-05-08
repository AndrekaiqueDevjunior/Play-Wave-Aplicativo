from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from core.models import User

router = APIRouter(prefix="/plans", tags=["plans"])

PLANS = [
    {
        "id": "starter",
        "name": "Starter",
        "description": "Ideal para negócios em crescimento",
        "price_brl": 199.0,
        "price_usd": 39.0,
        "max_devices": 5,
        "max_users": 3,
        "max_media_gb": 10,
        "features": [
            "Até 5 dispositivos",
            "3 usuários",
            "10 GB de mídia",
            "Suporte por e-mail",
            "Relatórios básicos",
        ],
    },
    {
        "id": "pro",
        "name": "Pro",
        "description": "Para empresas que precisam de mais controle",
        "price_brl": 499.0,
        "price_usd": 99.0,
        "max_devices": 25,
        "max_users": 10,
        "max_media_gb": 50,
        "features": [
            "Até 25 dispositivos",
            "10 usuários",
            "50 GB de mídia",
            "Suporte prioritário",
            "Relatórios avançados",
            "Agendamento de campanhas",
            "Rádio Indoor",
        ],
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "description": "Solução completa para grandes operações",
        "price_brl": 0.0,
        "price_usd": 0.0,
        "max_devices": -1,
        "max_users": -1,
        "max_media_gb": -1,
        "features": [
            "Dispositivos ilimitados",
            "Usuários ilimitados",
            "Armazenamento ilimitado",
            "SLA dedicado",
            "Suporte 24/7",
            "Onboarding personalizado",
            "API dedicada",
            "Multi-tenant",
        ],
    },
]


@router.get("/")
def list_plans(_: User = Depends(get_current_user)):
    return PLANS


@router.get("/{plan_id}")
def get_plan(plan_id: str, _: User = Depends(get_current_user)):
    for plan in PLANS:
        if plan["id"] == plan_id:
            return plan
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Plano não encontrado")
