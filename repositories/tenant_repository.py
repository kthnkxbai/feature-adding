
from .base_repository import BaseRepository
from models import Tenant
from errors import ApplicationError, NotFoundError, TenantNotFoundError, DatabaseOperationError
import logging

log = logging.getLogger(__name__)

class TenantRepository(BaseRepository):
    def __init__(self):
        super().__init__(Tenant)

    def get_by_id(self, tenant_id):
        """
        Retrieves a Tenant record by its tenant_id.
        Raises TenantNotFoundError if not found.
        Note: This is an override for models with composite PKs where tenant_id might not be the sole PK.
        It uses filter_by to find by tenant_id.
        """
        try:
            print(f"DEBUG: TenantRepository.get_by_id - Attempting to get Tenant with ID {tenant_id}")
            tenant = self.model.query.filter_by(tenant_id=tenant_id).first()
            if not tenant:
                raise TenantNotFoundError(f"Tenant with ID {tenant_id} not found.")
            print(f"DEBUG: TenantRepository.get_by_id - Found Tenant: {tenant}")
            return tenant
        except TenantNotFoundError:
            raise
        except Exception as e:
            log.exception(f"Database error fetching Tenant by ID {tenant_id}: {e}")
            raise DatabaseOperationError(f"Could not retrieve Tenant by ID {tenant_id}.")



    def get_by_organization_code(self, organization_code):
        try:
            return self.model.query.filter_by(organization_code=organization_code).first()
        except Exception as e:
            log.exception(f"Database error fetching Tenant by organization_code '{organization_code}': {e}")
            raise ApplicationError("Could not retrieve Tenant by organization code.", status_code=500)

    def get_by_sub_domain(self, sub_domain):
        try:
            return self.model.query.filter_by(sub_domain=sub_domain).first()
        except Exception as e:
            log.exception(f"Database error fetching Tenant by sub_domain '{sub_domain}': {e}")
            raise ApplicationError("Could not retrieve Tenant by sub-domain.", status_code=500)

    def get_by_composite_pk(self, tenant_id, organization_code, sub_domain):
        """
        Retrieves a tenant by its composite primary key components.
        """
        try:
            tenant = self.model.query.filter_by(
                tenant_id=tenant_id,
                organization_code=organization_code,
                sub_domain=sub_domain
            ).first()
            if not tenant:
                raise NotFoundError(f"Tenant with ID {tenant_id}, code '{organization_code}', and sub-domain '{sub_domain}' not found.")
            return tenant
        except NotFoundError: 
            raise
        except Exception as e:
            log.exception(f"Database error fetching Tenant by composite PK ({tenant_id}, {organization_code}, {sub_domain}): {e}")
            raise ApplicationError("Could not retrieve Tenant by composite key.", status_code=500)

tenant_repository = TenantRepository()
