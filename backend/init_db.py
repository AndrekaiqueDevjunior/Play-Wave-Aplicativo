from core.database import SessionLocal, Base, engine
from core.models import Plan, User, Tenant, UserRole
from core.auth import get_password_hash
from core.config import settings


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        default_plans = [
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
                "is_active": True,
                "is_popular": False,
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
                "is_active": True,
                "is_popular": True,
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
                "is_active": True,
                "is_popular": False,
            },
        ]
        for plan_data in default_plans:
            plan = db.query(Plan).filter(Plan.id == plan_data["id"]).first()
            if not plan:
                db.add(Plan(**plan_data))
        db.commit()

        # Criar tenant padrão
        tenant = db.query(Tenant).filter(Tenant.name == "Empresa Padrão").first()
        if not tenant:
            tenant = Tenant(
                name="Empresa Padrão",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"Tenant criado: {tenant.name} (ID: {tenant.id})")

        # Criar usuário admin
        admin_user = db.query(User).filter(
            User.email == settings.ADMIN_INITIAL_EMAIL
        ).first()
        if not admin_user:
            admin_user = User(
                name="Administrador",
                email=settings.ADMIN_INITIAL_EMAIL,
                password_hash=get_password_hash(settings.ADMIN_INITIAL_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
                tenant_id=tenant.id
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Usuário admin criado: {admin_user.email}")

        # Criar usuário operador
        operator_user = db.query(User).filter(
            User.email == settings.OPERATOR_INITIAL_EMAIL
        ).first()
        if not operator_user:
            operator_user = User(
                name="Operador",
                email=settings.OPERATOR_INITIAL_EMAIL,
                password_hash=get_password_hash(settings.OPERATOR_INITIAL_PASSWORD),
                role=UserRole.OPERATOR,
                is_active=True,
                tenant_id=tenant.id
            )
            db.add(operator_user)
            db.commit()
            db.refresh(operator_user)
            print(f"Usuário operador criado: {operator_user.email}")

        print("\nBanco de dados inicializado com sucesso!")

    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
