import datetime
import logging
import json 

from repositories.tenant_feature_repository import tenant_feature_repository
from repositories.tenant_repository import tenant_repository
from repositories.feature_repository import feature_repository
from schemas.tenant_feature_schemas import TenantFeatureInputSchema, TenantFeatureOutputSchema, FeatureStatusOutputSchema
from schemas.message_schemas import MessageSchema 
from errors import ApplicationError, DatabaseOperationError, TenantNotFoundError, FeatureNotFoundError, DuplicateTenantFeatureError, ValidationError, NotFoundError

log = logging.getLogger(__name__)

class TenantFeatureService:
    def __init__(self):
        self.repository = tenant_feature_repository
        self.tenant_repo = tenant_repository
        self.feature_repo = feature_repository
        self.input_schema = TenantFeatureInputSchema()
        self.output_schema = TenantFeatureOutputSchema(many=True) 
        self.feature_status_output_schema = FeatureStatusOutputSchema(many=True) 
        self.message_schema = MessageSchema()

    def get_all_tenant_features_for_tenant(self, tenant_id):
        """
        Retrieves all TenantFeature records for a specific tenant.
        """
        try:
            self.tenant_repo.get_by_id(tenant_id) 

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
            self.tenant_repo.get_by_id(tenant_id) 

            all_features_objs = self.feature_repo.get_all() 
            existing_tenant_features_objs = self.repository.get_all_for_tenant(tenant_id)

            existing_tf_map = {tf.feature_id: tf for tf in existing_tenant_features_objs}

            enabled_features_data = []
            disabled_features_data = []

            for feature_obj in all_features_objs:
                tf_entry = existing_tf_map.get(feature_obj.feature_id)
                
                
                is_enabled = True 
                if tf_entry:
                    is_enabled = tf_entry.is_enabled

                feature_dict = {
                    'feature_id': feature_obj.feature_id,
                    'name': feature_obj.name,
                    'is_enabled': is_enabled
                }

                if is_enabled:
                    enabled_features_data.append(feature_dict)
                else:
                    disabled_features_data.append(feature_dict)

            enabled_features_data.sort(key=lambda x: x['name'].lower())
            disabled_features_data.sort(key=lambda x: x['name'].lower())

            return {
                "enabled_features": enabled_features_data,  
                "disabled_features": disabled_features_data
            }
        except (TenantNotFoundError, DatabaseOperationError, ApplicationError):
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_features_for_tenant_with_status({tenant_id}): {e}")
            raise ApplicationError("Failed to retrieve feature status for tenant.", status_code=500)


    def update_tenant_feature_configuration(self, tenant_id: int, submitted_enabled_feature_ids: list, submitted_disabled_feature_ids: list):
        """
        Updates the feature configurations for a specific tenant.
        This handles enabling and disabling features based on provided lists.
        """
        print(f"DEBUG: TFService.update - Tenant ID: {tenant_id}")
        print(f"DEBUG: TFService.update - Submitted Enabled IDs: {submitted_enabled_feature_ids}")
        print(f"DEBUG: TFService.update - Submitted Disabled IDs: {submitted_disabled_feature_ids}")

        try:
            self.tenant_repo.get_by_id(tenant_id)

            current_tenant_features_objs = self.repository.get_all_for_tenant(tenant_id)
            existing_tf_map = {tf.feature_id: tf for tf in current_tenant_features_objs}

            current_enabled_db_ids = {tf.feature_id for tf in current_tenant_features_objs if tf.is_enabled}
            current_disabled_db_ids = {tf.feature_id for tf in current_tenant_features_objs if not tf.is_enabled}

            all_master_features = self.feature_repo.get_all()
            all_master_feature_ids = {f.feature_id for f in all_master_features}

            print(f"DEBUG: TFService.update - Current DB Enabled IDs: {current_enabled_db_ids}")
            print(f"DEBUG: TFService.update - Current DB Disabled IDs: {current_disabled_db_ids}")
            print(f"DEBUG: TFService.update - All Master Feature IDs: {all_master_feature_ids}")

            submitted_enabled_set = set(submitted_enabled_feature_ids)
            submitted_disabled_set = set(submitted_disabled_feature_ids)

            for fid in submitted_enabled_set.union(submitted_disabled_set):
                if fid not in all_master_feature_ids:
                    raise FeatureNotFoundError(f"Feature with ID {fid} does not exist.")

            features_to_enable_in_db = submitted_enabled_set - current_enabled_db_ids

            features_to_disable_in_db = submitted_disabled_set - current_disabled_db_ids

            features_to_switch_to_disabled = current_enabled_db_ids.intersection(submitted_disabled_set)

            features_to_switch_to_enabled = current_disabled_db_ids.intersection(submitted_enabled_set)

            print(f"DEBUG: TFService.update - Features to CREATE/UPDATE to ENABLED: {features_to_enable_in_db}")
            print(f"DEBUG: TFService.update - Features to CREATE/UPDATE to DISABLED: {features_to_disable_in_db}")
            print(f"DEBUG: TFService.update - Features to SWITCH FROM ENABLED TO DISABLED: {features_to_switch_to_disabled}")
            print(f"DEBUG: TFService.update - Features to SWITCH FROM DISABLED TO ENABLED: {features_to_switch_to_enabled}")

            updates_made = False

            for feature_id in features_to_enable_in_db.union(features_to_switch_to_enabled):
                tf_entry = existing_tf_map.get(feature_id)
                if not tf_entry: 
                    self.repository.create(
                        tenant_id=tenant_id,
                        feature_id=feature_id,
                        is_enabled=True,
                      
                        created_on=datetime.datetime.utcnow()
                    )
                    updates_made = True
                    print(f"DEBUG: TFService.update - Created new TF entry for feature {feature_id} (enabled)")
                elif not tf_entry.is_enabled: 
                    self.repository.update(tf_entry, is_enabled=True, updated_at=datetime.datetime.utcnow())
                    updates_made = True
                    print(f"DEBUG: TFService.update - Updated TF entry for feature {feature_id} (enabled from disabled)")

            for feature_id in features_to_disable_in_db.union(features_to_switch_to_disabled):
                tf_entry = existing_tf_map.get(feature_id)
                if not tf_entry: 
                    self.repository.create(
                        tenant_id=tenant_id,
                        feature_id=feature_id,
                        is_enabled=False,
               
                        created_on=datetime.datetime.utcnow()
                    )
                    updates_made = True
                    print(f"DEBUG: TFService.update - Created new TF entry for feature {feature_id} (disabled)")
                elif tf_entry.is_enabled: 
                    self.repository.update(tf_entry, is_enabled=False, updated_at=datetime.datetime.utcnow())
                    updates_made = True
                    print(f"DEBUG: TFService.update - Updated TF entry for feature {feature_id} (disabled from enabled)")


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