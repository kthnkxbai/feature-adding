import datetime
import logging
import json 

from repositories.branch_product_module_repository import branch_product_module_repository
from repositories.branch_repository import branch_repository
from repositories.product_repository import product_repository
from repositories.product_module_repository import product_module_repository 
from schemas.message_schemas import MessageSchema
from schemas.branch_product_module_schemas import ConfiguredBranchProductModuleOutputSchema, AvailableProductModuleOutputSchema

from errors import ApplicationError, NotFoundError, ValidationError, DuplicateModuleConfigurationError

log = logging.getLogger(__name__)

class BranchProductModuleService:
    def __init__(self):
        self.repository = branch_product_module_repository
        self.branch_repo = branch_repository
        self.product_repo = product_repository
        self.product_module_repo = product_module_repository 
        self.configured_output_schema = ConfiguredBranchProductModuleOutputSchema()
        self.available_output_schema = AvailableProductModuleOutputSchema()
        self.message_schema = MessageSchema() 

    def get_bpm_by_id(self, tenant_product_module):
        """
        Retrieves a BranchProductModule record by its primary key ID.
        Returns a dictionary representation.
        """
        try:
            bpm_obj = self.repository.get_by_id(tenant_product_module)
            return {
                'tenant_product_module': bpm_obj.tenant_product_module,
                'branch_id': bpm_obj.branch_id,
                'product_module_id': bpm_obj.product_module_id,
                'eligibility_config': json.loads(bpm_obj.eligibility_config) if bpm_obj.eligibility_config else {},
                'created_by': bpm_obj.created_by,
                'created_at': bpm_obj.created_at.isoformat() if bpm_obj.created_at else None,
                'updated_at': bpm_obj.updated_at.isoformat() if bpm_obj.updated_at else None
            }
        except NotFoundError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_bpm_by_id({tenant_product_module}): {e}")
            raise ApplicationError("Failed to retrieve BranchProductModule by ID.", status_code=500)

    def get_bpm_by_branch_and_product_module(self, branch_id, product_module_id):
        """
        Retrieves a BranchProductModule record by composite key (branch_id, product_module_id).
        Returns a dictionary representation.
        """
        try:
            bpm_obj = self.repository.get_by_branch_and_product_module(branch_id, product_module_id)
            if not bpm_obj:
                raise NotFoundError(f"BranchProductModule for branch {branch_id} and product_module {product_module_id} not found.")
            return {
                'tenant_product_module': bpm_obj.tenant_product_module,
                'branch_id': bpm_obj.branch_id,
                'product_module_id': bpm_obj.product_module_id,
                'eligibility_config': json.loads(bpm_obj.eligibility_config) if bpm_obj.eligibility_config else {},
                'created_by': bpm_obj.created_by,
                'created_at': bpm_obj.created_at.isoformat() if bpm_obj.created_at else None,
                'updated_at': bpm_obj.updated_at.isoformat() if bpm_obj.updated_at else None
            }
        except NotFoundError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_bpm_by_branch_and_product_module({branch_id}, {product_module_id}): {e}")
            raise ApplicationError("Failed to retrieve BranchProductModule by branch and product module.", status_code=500)


    def get_configured_modules_for_branch_product(self, branch_id, product_id, module_id_sequences: dict):
        """
        Retrieves all modules configured for a specific branch and product, sorted by sequence.
        This services the /api/branches/<int:branch_id>/products/<int:product_id>/configured-modules endpoint.
        Returns a list of dictionaries as per the ConfiguredBranchProductModuleOutputSchema.
        """
        try:
            self.branch_repo.get_by_id(branch_id) 
            self.product_repo.get_by_id(product_id) 

            configured_modules_objs = self.repository.get_configured_modules_for_branch_product(branch_id, product_id)

            configured_list = []
            for bpm in configured_modules_objs:
                if bpm.product_module and bpm.product_module.module:
                    configured_list.append(self.configured_output_schema.dump({
                        'branch_id': bpm.branch_id,
                        'product_id': bpm.product_module.product_id,
                        'module_id': bpm.product_module.module.module_id,
                        'module_name': bpm.product_module.module.name
                    }))

            sorted_configured_list = sorted(
                configured_list,
                key=lambda item: module_id_sequences.get(item['module_id'], 9999)
            )
            return sorted_configured_list
        except NotFoundError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_configured_modules_for_branch_product({branch_id}, {product_id}): {e}")
            raise ApplicationError("Failed to retrieve configured modules for branch product.", status_code=500)


    def get_available_modules_for_product_with_status(self, product_id, branch_id: int | None, module_id_sequences: dict):
        """
        Retrieves all modules available for a specific product and indicates
        if they are configured for a given branch.
        This services the /api/products/<int:product_id>/modules endpoint.
        Returns a list of dictionaries as per the AvailableProductModuleOutputSchema.
        """
        try:
            self.product_repo.get_by_id(product_id) 

            all_product_modules_for_product = self.product_module_repo.get_all_for_product_with_module_details(product_id)

            available_modules_info = {pm.module.module_id: pm.module for pm in all_product_modules_for_product if pm.module}

            configured_module_ids = set()
            if branch_id is not None: 
                self.branch_repo.get_by_id(branch_id) 

                configured_bpms_for_product_modules = self.repository.get_configured_modules_for_branch_product(branch_id, product_id)

                configured_module_ids = {
                    bpm.product_module.module_id
                    for bpm in configured_bpms_for_product_modules
                    if bpm.product_module and bpm.product_module.module 
                }

            modules_data = []
            for module_pk_id, module_obj in available_modules_info.items():
                is_configured = module_pk_id in configured_module_ids
                modules_data.append(self.available_output_schema.dump({
                    'id': module_obj.module_id,
                    'name': module_obj.name,
                    'is_configured': is_configured
                }))

            sorted_modules = sorted(
                modules_data,
                key=lambda item: module_id_sequences.get(item['id'], 9999) 
            )
            return sorted_modules
        except NotFoundError:
            raise 
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_available_modules_for_product_with_status({product_id}, {branch_id}): {e}")
            raise ApplicationError("Failed to retrieve available product modules with status.", status_code=500)


    def create_bpm_record(self, branch_id: int, product_module_id: int, eligibility_config: str | None = None, created_by: str = "System"):
        """
        Creates a single BranchProductModule record.
        This is a helper for the bulk update method or for direct creation if needed.
        """
        try:
            self.branch_repo.get_by_id(branch_id)
            self.product_module_repo.get_by_id(product_module_id)

            existing_bpm = self.repository.get_by_branch_and_product_module(branch_id, product_module_id)
            if existing_bpm:
                raise DuplicateModuleConfigurationError()

            new_bpm_obj = self.repository.create(
                branch_id=branch_id,
                product_module_id=product_module_id,
                eligibility_config=eligibility_config or json.dumps({}),
                created_by=created_by,
                created_at=datetime.datetime.utcnow()
            )
            return new_bpm_obj 
        except (NotFoundError, DuplicateModuleConfigurationError, ApplicationError):
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_bpm_record for branch {branch_id}, pm {product_module_id}: {e}")
            raise ApplicationError("Failed to create BranchProductModule record.", status_code=500)


    def delete_bpm_record(self, bpm_obj):
        """
        Deletes a single BranchProductModule record (model object).
        This is a helper for the bulk update method or for direct deletion if needed.
        """
        try:
            self.repository.delete(bpm_obj)
            return {"message": f"BranchProductModule with ID {bpm_obj.bpm_id} deleted."}
        except ApplicationError: 
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_bpm_record for ID {bpm_obj.bpm_id}: {e}")
            raise ApplicationError("Failed to delete BranchProductModule record.", status_code=500)


    def update_branch_product_module_configuration(self, branch_id: int, product_id: int, submitted_module_ids: set):
        """
        Complex logic for updating multiple BPMs for a given branch and product.
        This replaces the original logic from the Flask route's index_post.
        It handles adding new configurations and removing old ones based on submitted_module_ids.
        """
        try:
            self.branch_repo.get_by_id(branch_id) 
            self.product_repo.get_by_id(product_id) 

            all_product_modules_for_product = self.product_module_repo.get_all_for_product(product_id)
            product_module_id_lookup_by_module_id = {
                pm.module_id: pm.product_module_id
                for pm in all_product_modules_for_product
            }
            valid_submitted_product_module_ids = {
                product_module_id_lookup_by_module_id[mid]
                for mid in submitted_module_ids
                if mid in product_module_id_lookup_by_module_id
            }

            existing_bpms_for_branch_product = self.repository.get_configured_modules_for_branch_product(branch_id, product_id)
            existing_bpm_lookup_by_product_module_id = {
                bpm.product_module_id: bpm for bpm in existing_bpms_for_branch_product
            }
            existing_product_module_ids_configured = set(existing_bpm_lookup_by_product_module_id.keys())

            product_module_ids_to_add = valid_submitted_product_module_ids - existing_product_module_ids_configured
            product_module_ids_to_remove = existing_product_module_ids_configured - valid_submitted_product_module_ids

            updates_made = False

            for pm_id_to_add in product_module_ids_to_add:
                self.create_bpm_record(
                    branch_id=branch_id,
                    product_module_id=pm_id_to_add,
                    eligibility_config=json.dumps({}),
                    created_by="WebForm" 
                )
                updates_made = True
                log.info(f"Added BranchProductModule: branch_id={branch_id}, product_module_id={pm_id_to_add}")

            for pm_id_to_remove in product_module_ids_to_remove:
                bpm_to_delete_obj = existing_bpm_lookup_by_product_module_id.get(pm_id_to_remove)
                if bpm_to_delete_obj:
                    self.delete_bpm_record(bpm_to_delete_obj)
                    updates_made = True
                    log.info(f"Removed BranchProductModule: branch_id={branch_id}, product_module_id={pm_id_to_remove}")
                else:
                    log.warning(f"Attempted to remove non-existent BPM for product_module_id {pm_id_to_remove} for branch {branch_id}.")

            if updates_made:
                return self.message_schema.dump({"status": "success", "message": "Module configuration updated successfully!"})
            else:
                return self.message_schema.dump({"status": "info", "message": "No changes made to module configuration."})

        except NotFoundError as e:
            raise ApplicationError(e.message, status_code=404)
        except ApplicationError:
            raise 
        except Exception as e:
            log.exception(f"Unexpected error in update_branch_product_module_configuration for branch {branch_id}, product {product_id}: {e}")
            raise ApplicationError("Failed to update module configuration due to an internal error.", status_code=500)

branch_product_module_service = BranchProductModuleService()
