import datetime
import logging

from repositories.tenant_repository import tenant_repository
from repositories.country_repository import country_repository

from schemas.tenant_schemas import TenantInputSchema, TenantOutputSchema, TenantMinimalOutputSchema

from errors import ApplicationError, NotFoundError, ValidationError, DuplicateOrganizationCodeError, DuplicateSubDomainError




log = logging.getLogger(__name__)

class TenantService:
    def __init__(self):
        self.repository = tenant_repository
        self.country_repo = country_repository
        self.input_schema = TenantInputSchema()
        self.output_schema_many = TenantOutputSchema(many=True)
        self.tenant_minimal_schema = TenantMinimalOutputSchema(many=True)

    def get_all_tenants(self, minimal=False):
        """
        Retrieves all tenant records.
        If minimal is True, returns only minimal fields.
        """
        try:
            
            tenants = self.repository.get_all()
            

            if minimal:
                result = self.tenant_minimal_schema.dump(tenants)
                
                return result
            else:
                dumped_tenants = self.output_schema_many.dump(tenants)
                
                return dumped_tenants

        except ApplicationError:
            raise 
        except Exception as e:
            log.exception(f"Unexpected error in get_all_tenants: {e}")
            raise ApplicationError("Failed to retrieve all tenants.", status_code=500)


    def get_tenant_by_id(self, tenant_id):
        """
        Retrieves a single tenant record by its ID.
        """
        try:
            tenant = self.repository.get_by_id(tenant_id)
            dumped_tenant = TenantOutputSchema().dump(tenant)
            print(f"DEBUG: TenantService.get_tenant_by_id({tenant_id}) returning: {dumped_tenant}")
            return dumped_tenant
        except NotFoundError:
            raise 
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_tenant_by_id({tenant_id}): {e}")
            raise ApplicationError("Failed to retrieve tenant by ID.", status_code=500)

    def get_tenant_by_composite_pk(self, tenant_id, organization_code, sub_domain):
        """
        Retrieves a tenant by its composite primary key components.
        """
        try:
            tenant = self.repository.get_by_composite_pk(tenant_id, organization_code, sub_domain)
            dumped_tenant = TenantOutputSchema().dump(tenant)
            return dumped_tenant
        except NotFoundError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_tenant_by_composite_pk({tenant_id}, {organization_code}, {sub_domain}): {e}")
            raise ApplicationError("Failed to retrieve tenant by composite key.", status_code=500)

    def create_tenant(self, data):
        """
        Creates a new tenant record.
        Validates input, checks for unique organization code and sub-domain,
        and checks for existence of the associated country.
        """
        try:
            validated_data = self.input_schema.load(data)

            organization_code = validated_data['organization_code']
            sub_domain = validated_data['sub_domain']
            country_id = validated_data['country_id']

            existing_org_tenant = self.repository.get_by_organization_code(organization_code)
            if existing_org_tenant:
                raise DuplicateOrganizationCodeError(f"Organization code '{organization_code}' already exists.")

            existing_sub_domain_tenant = self.repository.get_by_sub_domain(sub_domain)
            if existing_sub_domain_tenant:
                raise DuplicateSubDomainError(f"Sub-domain '{sub_domain}' already exists.")

            self.country_repo.get_by_id(country_id) 

            new_tenant_obj = self.repository.create(
                organization_code=organization_code,
                tenant_name=validated_data['tenant_name'],
                sub_domain=sub_domain,
                default_currency=validated_data['default_currency'],
                description=validated_data.get('description'),
                status=validated_data['status'],
                country_id=country_id,
                
            )
            dumped_new_tenant = TenantOutputSchema().dump(new_tenant_obj)
            return dumped_new_tenant
        except ValidationError: 
            raise
        except NotFoundError as e: 
            raise ValidationError(f"Related country not found: {e.message}", errors={"country_id": e.message})
        except (DuplicateOrganizationCodeError, DuplicateSubDomainError): 
            raise
        except ApplicationError: 
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_tenant with data {data}: {e}")
            raise ApplicationError("Failed to create tenant due to an internal error.", status_code=500)

    def update_tenant(self, tenant_id, organization_code_param, sub_domain_param, data):
        """
        Updates an existing tenant record.
        Validates input, checks for existence, and handles duplicate code/sub-domain checks.
        """
        try:
            validated_data = self.input_schema.load(data, partial=True)

            tenant_obj = self.repository.get_by_composite_pk(tenant_id, organization_code_param, sub_domain_param)

            if 'organization_code' in validated_data and validated_data['organization_code'] != tenant_obj.organization_code:
                existing_org_tenant = self.repository.get_by_organization_code(validated_data['organization_code'])
                if existing_org_tenant and existing_org_tenant.tenant_id != tenant_id:
                    raise DuplicateOrganizationCodeError(f"Organization code '{validated_data['organization_code']}' already exists for another tenant.")

            if 'sub_domain' in validated_data and validated_data['sub_domain'] != tenant_obj.sub_domain:
                existing_sub_domain_tenant = self.repository.get_by_sub_domain(validated_data['sub_domain'])
                if existing_sub_domain_tenant and existing_sub_domain_tenant.tenant_id != tenant_id:
                    raise DuplicateSubDomainError(f"Sub-domain '{validated_data['sub_domain']}' already exists for another tenant.")

            if 'country_id' in validated_data and validated_data['country_id'] != tenant_obj.country_id:
                self.country_repo.get_by_id(validated_data['country_id']) 

            
            updated_tenant_obj = self.repository.update(tenant_obj, **validated_data)
            dumped_updated_tenant = TenantOutputSchema().dump(updated_tenant_obj)
            return dumped_updated_tenant
        except ValidationError:
            raise
        except NotFoundError: 
            raise
        except (DuplicateOrganizationCodeError, DuplicateSubDomainError):
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_tenant({tenant_id}, {organization_code_param}, {sub_domain_param}) with data {data}: {e}")
            raise ApplicationError("Failed to update tenant due to an internal error.", status_code=500)

    def delete_tenant(self, tenant_id, organization_code, sub_domain):
        """
        Deletes a tenant record by its composite primary key.
        """
        try:
            tenant_obj = self.repository.get_by_composite_pk(tenant_id, organization_code, sub_domain) 
            self.repository.delete(tenant_obj)
            return {"message": f"Tenant with ID {tenant_id} deleted successfully."}
        except NotFoundError:
            raise
        except ApplicationError: 
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_tenant({tenant_id}, {organization_code}, {sub_domain}): {e}")
            raise ApplicationError("Failed to delete tenant due to an internal error.", status_code=500)

tenant_service = TenantService()
