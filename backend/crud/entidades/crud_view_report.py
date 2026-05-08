from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from core.models import ViewReport, Device, Campaign, Media, Tenant
from core.schemas_completos import ViewReportCreate, ViewReportUpdate, ViewReportResponse
from .crud_base import CRUDBase


class CRUDViewReport(CRUDBase[ViewReport, ViewReportCreate, ViewReportUpdate]):
    def get_by_device(self, db: Session, *, device_id: str) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.device_id == device_id).order_by(ViewReport.date.desc()).all()
    
    def get_by_campaign(self, db: Session, *, campaign_id: str) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.campaign_id == campaign_id).order_by(ViewReport.date.desc()).all()
    
    def get_by_media(self, db: Session, *, media_id: str) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.media_id == media_id).order_by(ViewReport.date.desc()).all()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.tenant_id == tenant_id).order_by(ViewReport.date.desc()).all()
    
    def get_by_date_range(self, db: Session, *, start_date, end_date) -> List[ViewReport]:
        return db.query(ViewReport).filter(
            and_(
                ViewReport.date >= start_date,
                ViewReport.date <= end_date
            )
        ).order_by(ViewReport.date.desc()).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.status == status).order_by(ViewReport.date.desc()).all()
    
    def get_successful(self, db: Session) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.status == "success").order_by(ViewReport.date.desc()).all()
    
    def get_with_errors(self, db: Session) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.status == "error").order_by(ViewReport.date.desc()).all()
    
    def get_partial(self, db: Session) -> List[ViewReport]:
        return db.query(ViewReport).filter(ViewReport.status == "partial").order_by(ViewReport.date.desc()).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[ViewReport]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(ViewReport)
            .filter(
                or_(
                    ViewReport.device_name.ilike(f"%{query}%"),
                    ViewReport.campaign_name.ilike(f"%{query}%"),
                    ViewReport.media_name.ilike(f"%{query}%")
                )
            )
            .order_by(ViewReport.date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def aggregate_by_date(self, db: Session, *, start_date, end_date, tenant_id: str = None) -> List[dict]:
        query = db.query(ViewReport).filter(
            and_(
                ViewReport.date >= start_date,
                ViewReport.date <= end_date
            )
        )
        
        if tenant_id:
            query = query.filter(ViewReport.tenant_id == tenant_id)
        
        # Agrupa por data
        results = (
            query.with_entities(
                ViewReport.date,
                func.sum(ViewReport.views).label('total_views'),
                func.count(ViewReport.id).label('report_count')
            )
            .group_by(ViewReport.date)
            .order_by(ViewReport.date.desc())
            .all()
        )
        
        return [
            {
                "date": result.date,
                "total_views": result.total_views or 0,
                "report_count": result.report_count
            }
            for result in results
        ]
    
    def aggregate_by_device(self, db: Session, *, start_date, end_date, tenant_id: str = None) -> List[dict]:
        query = db.query(ViewReport).filter(
            and_(
                ViewReport.date >= start_date,
                ViewReport.date <= end_date
            )
        )
        
        if tenant_id:
            query = query.filter(ViewReport.tenant_id == tenant_id)
        
        # Agrupa por dispositivo
        results = (
            query.with_entities(
                ViewReport.device_id,
                ViewReport.device_name,
                func.sum(ViewReport.views).label('total_views'),
                func.count(ViewReport.id).label('report_count')
            )
            .group_by(ViewReport.device_id, ViewReport.device_name)
            .order_by(func.sum(ViewReport.views).desc())
            .all()
        )
        
        return [
            {
                "device_id": result.device_id,
                "device_name": result.device_name,
                "total_views": result.total_views or 0,
                "report_count": result.report_count
            }
            for result in results
        ]
    
    def aggregate_by_campaign(self, db: Session, *, start_date, end_date, tenant_id: str = None) -> List[dict]:
        query = db.query(ViewReport).filter(
            and_(
                ViewReport.date >= start_date,
                ViewReport.date <= end_date
            )
        )
        
        if tenant_id:
            query = query.filter(ViewReport.tenant_id == tenant_id)
        
        # Agrupa por campanha
        results = (
            query.with_entities(
                ViewReport.campaign_id,
                ViewReport.campaign_name,
                func.sum(ViewReport.views).label('total_views'),
                func.count(ViewReport.id).label('report_count')
            )
            .group_by(ViewReport.campaign_id, ViewReport.campaign_name)
            .order_by(func.sum(ViewReport.views).desc())
            .all()
        )
        
        return [
            {
                "campaign_id": result.campaign_id,
                "campaign_name": result.campaign_name,
                "total_views": result.total_views or 0,
                "report_count": result.report_count
            }
            for result in results
        ]
    
    def get_statistics(self, db: Session, *, tenant_id: str = None, days: int = 7) -> dict:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(ViewReport).filter(ViewReport.created_at >= cutoff_date)
        if tenant_id:
            query = query.filter(ViewReport.tenant_id == tenant_id)
        
        total = query.count()
        success = query.filter(ViewReport.status == "success").count()
        error = query.filter(ViewReport.status == "error").count()
        partial = query.filter(ViewReport.status == "partial").count()
        
        # Total de visualizações no período
        total_views = query.with_entities(func.sum(ViewReport.views)).scalar() or 0
        
        return {
            "total_reports": total,
            "success": success,
            "error": error,
            "partial": partial,
            "total_views": total_views,
            "period_days": days
        }


# Instância única do CRUD
crud_view_report = CRUDViewReport(ViewReport)
