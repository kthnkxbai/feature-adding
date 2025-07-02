# repositories/tenant_feature_repository.py
from .base_repository import BaseRepository
from models import TenantFeature
from errors import DatabaseOperationError, TenantFeatureNotFoundError
import logging
from extensions import db # Import db for direct query

log = logging.getLogger(__name__)

class TenantFeatureRepository(BaseRepository):
    def __init__(self):
        super().__init__(TenantFeature)

    def get_by_id(self, item_id):
        """
        Overrides BaseRepository's get_by_id to raise TenantFeatureNotFoundError.
        """
        try:
            item = self.model.query.get(item_id)
            if not item:
                raise TenantFeatureNotFoundError(f"TenantFeature with ID {item_id} not found.")
            return item
        except TenantFeatureNotFoundError:
            raise
        except Exception as e:
            log.exception(f"Database error fetching TenantFeature by ID {item_id}: {e}")
            raise DatabaseOperationError(f"Could not retrieve TenantFeature.")

    def get_by_tenant_and_feature(self, tenant_id, feature_id):
        """
        Retrieves a TenantFeature record by tenant_id and feature_id.
        """
        try:
            return self.model.query.filter_by(tenant_id=tenant_id, feature_id=feature_id).first()
        except Exception as e:
            log.exception(f"Database error fetching TenantFeature by tenant_id {tenant_id} and feature_id {feature_id}: {e}")
            raise DatabaseOperationError("Could not retrieve TenantFeature by tenant and feature IDs.")

    def get_all_for_tenant(self, tenant_id):
        """
        Retrieves all TenantFeature records for a specific tenant.
        """
        try:
            return self.model.query.filter_by(tenant_id=tenant_id).all()
        except Exception as e:
            log.exception(f"Database error fetching all TenantFeatures for tenant {tenant_id}: {e}")
            raise DatabaseOperationError("Could not retrieve TenantFeatures for tenant.")

tenant_feature_repository = TenantFeatureRepository()