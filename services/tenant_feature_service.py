# services/tenant_feature_service.py
import datetime
import logging
import json # For handling config_json

from repositories.tenant_feature_repository import tenant_feature_repository
from repositories.tenant_repository import tenant_repository
from repositories.feature_repository import feature_repository
from schemas.tenant_feature_schemas import TenantFeatureInputSchema, TenantFeatureOutputSchema, FeatureStatusOutputSchema
from schemas.message_schemas import MessageSchema # For consistent messages
from errors import ApplicationError, DatabaseOperationError, TenantNotFoundError, FeatureNotFoundError, DuplicateTenantFeatureError, ValidationError, NotFoundError

log = logging.getLogger(__name__)

class TenantFeatureService:
    def __init__(self):
        self.repository = tenant_feature_repository
        self.tenant_repo = tenant_repository
        self.feature_repo = feature_repository
        self.input_schema = TenantFeatureInputSchema()
        self.output_schema = TenantFeatureOutputSchema(many=True) # For lists of TenantFeatures
        self.feature_status_output_schema = FeatureStatusOutputSchema(many=True) # For list of features with status
        self.message_schema = MessageSchema()

    def get_all_tenant_features_for_tenant(self, tenant_id):
        """
        Retrieves all TenantFeature records for a specific tenant.
        """
        try:
            # Validate tenant existence
            self.tenant_repo.get_by_id(tenant_id) # Will raise TenantNotFoundError if not found

            tenant_features = self.repository.get_all_for_tenant(tenant_id)
            return self.output_schema.dump(tenant_features)
        except (TenantNotFoundError, DatabaseOperationError, ApplicationError):
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_all_tenant_features_for_tenant({tenant_id}): {e}")
            raise ApplicationError("Failed to retrieve tenant features.", status_code=500)

    def get_features_for_tenant_with_status(self, tenant_id):
        """
        Retrieves all master features and indicates their enabled/disabled status for a given tenant.
        This services the /api/tenant_features/<int:tenant_id> endpoint.
        Returns a dictionary with 'enabled_features' and 'disabled_features' lists.
        """
        try:
            # Validate tenant existence
            self.tenant_repo.get_by_id(tenant_id) # Will raise TenantNotFoundError if not found

            all_features_objs = self.feature_repo.get_all() # Get all master features
            existing_tenant_features_objs = self.repository.get_all_for_tenant(tenant_id)

            # Create a lookup map for existing tenant features
            existing_tf_map = {tf.feature_id: tf for tf in existing_tenant_features_objs}

            enabled_features_data = []
            disabled_features_data = []

            for feature_obj in all_features_objs:
                tf_entry = existing_tf_map.get(feature_obj.feature_id)
                
                # Determine if feature is enabled for this tenant
                # If a TenantFeature entry exists and is_enabled is True, it's enabled.
                # If no TenantFeature entry exists, it's considered "default enabled" or available to be enabled.
                # If a TenantFeature entry exists and is_enabled is False, it's disabled.
                is_enabled = True # Default assumption: available features are enabled unless explicitly disabled
                if tf_entry:
                    is_enabled = tf_entry.is_enabled

                feature_dict = {
                    'id': feature_obj.feature_id,
                    'name': feature_obj.name,
                    'is_enabled': is_enabled
                }

                if is_enabled:
                    enabled_features_data.append(feature_dict)
                else:
                    disabled_features_data.append(feature_dict)

            # Sort by name for consistent display
            enabled_features_data.sort(key=lambda x: x['name'].lower())
            disabled_features_data.sort(key=lambda x: x['name'].lower())

            return {
                'enabled_features': self.feature_status_output_schema.dump(enabled_features_data),
                'disabled_features': self.feature_status_output_schema.dump(disabled_features_data)
            }
        except (TenantNotFoundError, DatabaseOperationError, ApplicationError):
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_features_for_tenant_with_status({tenant_id}): {e}")
            raise ApplicationError("Failed to retrieve feature status for tenant.", status_code=500)

    def update_tenant_feature_configuration(self, tenant_id: int, enabled_feature_ids: list, disabled_feature_ids: list):
        """
        Updates the feature configurations for a specific tenant.
        This handles enabling and disabling features based on provided lists.
        """
        try:
            # Validate tenant existence
            self.tenant_repo.get_by_id(tenant_id) # Will raise TenantNotFoundError if not found

            # Get all existing TenantFeature entries for this tenant
            existing_tenant_features = self.repository.get_all_for_tenant(tenant_id)
            existing_tf_map = {tf.feature_id: tf for tf in existing_tenant_features}

            updates_made = False

            # Process features to be enabled
            for feature_id in enabled_feature_ids:
                # Validate feature existence
                self.feature_repo.get_by_id(feature_id) # Will raise FeatureNotFoundError if not found

                if feature_id in existing_tf_map:
                    tf_entry = existing_tf_map[feature_id]
                    if tf_entry.is_enabled is not True:
                        tf_entry.is_enabled = True
                        tf_entry.updated_at = datetime.datetime.utcnow()
                        self.repository.update(tf_entry, is_enabled=True, updated_at=tf_entry.updated_at)
                        updates_made = True
                else:
                    # Create new TenantFeature entry if it doesn't exist
                    self.repository.create(
                        tenant_id=tenant_id,
                        feature_id=feature_id,
                        is_enabled=True,
                        config_json=json.dumps({}), # Default empty config
                        created_at=datetime.datetime.utcnow()
                    )
                    updates_made = True

            # Process features to be disabled
            for feature_id in disabled_feature_ids:
                # Validate feature existence
                self.feature_repo.get_by_id(feature_id) # Will raise FeatureNotFoundError if not found

                if feature_id in existing_tf_map:
                    tf_entry = existing_tf_map[feature_id]
                    if tf_entry.is_enabled is not False:
                        tf_entry.is_enabled = False
                        tf_entry.updated_at = datetime.datetime.utcnow()
                        self.repository.update(tf_entry, is_enabled=False, updated_at=tf_entry.updated_at)
                        updates_made = True
                else:
                    # Create new TenantFeature entry if it doesn't exist (and needs to be explicitly disabled)
                    self.repository.create(
                        tenant_id=tenant_id,
                        feature_id=feature_id,
                        is_enabled=False,
                        config_json=json.dumps({}), # Default empty config
                        created_at=datetime.datetime.utcnow()
                    )
                    updates_made = True

            if updates_made:
                return self.message_schema.dump({"status": "success", "message": f"Feature configurations updated successfully for Tenant ID {tenant_id}!"})
            else:
                return self.message_schema.dump({"status": "info", "message": f"No changes required or made for Tenant ID {tenant_id}."})

        except (TenantNotFoundError, FeatureNotFoundError, DuplicateTenantFeatureError, ValidationError, DatabaseOperationError, ApplicationError):
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_tenant_feature_configuration for tenant {tenant_id}: {e}")
            raise ApplicationError("Failed to update tenant feature configuration due to an internal error.", status_code=500)

tenant_feature_service = TenantFeatureService()