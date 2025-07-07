
from repositories.tenant_feature_repository import tenant_feature_repository
from repositories.tenant_repository import tenant_repository
from repositories.feature_repository import feature_repository
from schemas.tenant_feature_schemas import TenantFeatureBaseSchema, TenantFeatureInputSchema
from errors import TenantFeatureNotFoundError, DuplicateTenantFeatureError, TenantNotFoundError, FeatureNotFoundError, DatabaseOperationError, ValidationError
from models import TenantFeature 
class TenantFeatureService:
    def __init__(self, repository=tenant_feature_repository, schema=TenantFeatureBaseSchema(), input_schema=TenantFeatureInputSchema(),
                 tenant_repo=tenant_repository, feature_repo=feature_repository):
        self.repository = repository
        self.schema = schema
        self.input_schema = input_schema
        self.tenant_repo = tenant_repo
        self.feature_repo = feature_repo

    def get_tenant_feature_by_id(self, tenant_feature_id):
        """Retrieves and serializes a single TenantFeature record by ID."""
        try:
            tf = self.repository.get_by_id(tenant_feature_id)
            if not tf:
                raise TenantFeatureNotFoundError(tenant_feature_id, "N/A") 
            return self.schema.dump(tf)
        except (TenantFeatureNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting tenant feature by ID {tenant_feature_id}: {e}")

    def get_tenant_feature_by_tenant_and_feature(self, tenant_id, feature_id):
        """Retrieves and serializes a TenantFeature record by tenant_id and feature_id."""
        try:
            tf = self.repository.get_by_tenant_and_feature(tenant_id, feature_id)
            if not tf:
                raise TenantFeatureNotFoundError(tenant_id, feature_id)
            return self.schema.dump(tf)
        except (TenantFeatureNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting tenant feature for tenant {tenant_id}, feature {feature_id}: {e}")

    def get_all_tenant_features_for_tenant(self, tenant_id):
        """Retrieves and serializes all TenantFeature records for a specific tenant."""
        try:
            tenant = self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise TenantNotFoundError(tenant_id)

            tfs = self.repository.get_all_for_tenant(tenant_id)
            return self.schema.dump(tfs, many=True)
        except (TenantNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting all tenant features for tenant {tenant_id}: {e}")

    def create_tenant_feature(self, tenant_feature_data):
        """Validates and creates a new TenantFeature record."""
        try:
            validated_data = self.input_schema.load(tenant_feature_data)

            # Ensure tenant and feature exist
            tenant = self.tenant_repo.get_by_id(validated_data['tenant_id'])
            if not tenant:
                raise TenantNotFoundError(validated_data['tenant_id'])
            feature = self.feature_repo.get_by_id(validated_data['feature_id'])
            if not feature:
                raise FeatureNotFoundError(validated_data['feature_id'])

            # Check for existing configuration to prevent duplicates
            existing_tf = self.repository.get_by_tenant_and_feature(
                validated_data['tenant_id'], validated_data['feature_id']
            )
            if existing_tf:
                raise DuplicateTenantFeatureError(validated_data['tenant_id'], validated_data['feature_id'])

            tf = TenantFeature(**validated_data)
            self.repository.add(tf)
            self.repository.save_changes()
            return self.schema.dump(tf)
        except (ValidationError, TenantNotFoundError, FeatureNotFoundError, DuplicateTenantFeatureError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while creating tenant feature: {e}")

    def update_tenant_feature(self, tenant_id, feature_id, update_data):
        """Updates an existing TenantFeature record."""
        try:
            tf = self.repository.get_by_tenant_and_feature(tenant_id, feature_id)
            if not tf:
                raise TenantFeatureNotFoundError(tenant_id, feature_id)

            validated_data = self.input_schema.load(update_data, partial=True)


            for key, value in validated_data.items():
                setattr(tf, key, value)

            self.repository.save_changes()
            return self.schema.dump(tf)
        except (TenantFeatureNotFoundError, ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while updating tenant feature for tenant {tenant_id}, feature {feature_id}: {e}")

    def delete_tenant_feature(self, tenant_id, feature_id):
        """Deletes a TenantFeature record."""
        try:
            tf = self.repository.get_by_tenant_and_feature(tenant_id, feature_id)
            if not tf:
                raise TenantFeatureNotFoundError(tenant_id, feature_id)

            self.repository.delete(tf)
            self.repository.save_changes()
            return {"message": f"TenantFeature for tenant {tenant_id}, feature {feature_id} deleted successfully."}
        except (TenantFeatureNotFoundError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while deleting tenant feature for tenant {tenant_id}, feature {feature_id}: {e}")

tenant_feature_service = TenantFeatureService()
