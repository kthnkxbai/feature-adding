
from extensions import db
from models import TenantFeature
from errors import DatabaseOperationError
from sqlalchemy import exc
from sqlalchemy.orm import joinedload 

class TenantFeatureRepository:
    def get_by_id(self, tenant_feature_id):
        """Retrieves a TenantFeature record by its primary key."""
        try:
            return db.session.get(TenantFeature, tenant_feature_id)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve tenant feature with ID {tenant_feature_id}: {e}") from e

    def get_by_tenant_and_feature(self, tenant_id, feature_id):
        """Retrieves a TenantFeature record by tenant_id and feature_id."""
        try:
            return TenantFeature.query.filter_by(
                tenant_id=tenant_id,
                feature_id=feature_id
            ).options(joinedload(TenantFeature.feature)).first() 
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve tenant feature for tenant {tenant_id}, feature {feature_id}: {e}") from e

    def get_all_for_tenant(self, tenant_id):
        """Retrieves all TenantFeature records for a specific tenant."""
        try:
            return TenantFeature.query.filter_by(tenant_id=tenant_id).options(
                joinedload(TenantFeature.feature)
            ).all() 
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve all tenant features for tenant {tenant_id}: {e}") from e

    def add(self, tenant_feature):
        """Adds a new TenantFeature record to the session."""
        try:
            db.session.add(tenant_feature)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error adding tenant feature: {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to add tenant feature: {e}") from e

    def delete(self, tenant_feature):
        """Deletes a TenantFeature record from the session."""
        try:
            db.session.delete(tenant_feature)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error deleting tenant feature: {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete tenant feature: {e}") from e

    def save_changes(self):
        """Commits changes to the database."""
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Failed to commit tenant feature changes: {e}") from e

    def rollback_changes(self):
        """Rolls back changes in the database session."""
        db.session.rollback()

tenant_feature_repository = TenantFeatureRepository()
