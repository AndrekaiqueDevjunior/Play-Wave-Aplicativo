from core.database import SessionLocal, Base, engine
from core.models import User, Tenant, UserRole
from core.auth import get_password_hash
from core.config import settings


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
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
