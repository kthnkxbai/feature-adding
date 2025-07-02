# services/branch_product_module_service.py
import datetime
import logging
import json # For handling eligibility_config as JSON string

# Repositories
from repositories.branch_product_module_repository import branch_product_module_repository
from repositories.branch_repository import branch_repository
from repositories.product_repository import product_repository
from repositories.product_module_repository import product_module_repository # Used to fetch product modules per product
from repositories.module_repository import module_repository # Ensure this is imported for module existence checks

# Schemas
from schemas.message_schemas import MessageSchema
from schemas.branch_product_module_schemas import ConfiguredBranchProductModuleOutputSchema, AvailableProductModuleOutputSchema

# Custom Errors
from errors import ApplicationError, NotFoundError, ValidationError, DuplicateModuleConfigurationError, \
    BranchNotFoundError, ProductNotFoundError, ProductModuleNotFoundError, ModuleNotFoundError, DatabaseOperationError

log = logging.getLogger(__name__)

class BranchProductModuleService:
    def __init__(self):
        self.repository = branch_product_module_repository
        self.branch_repo = branch_repository
        self.product_repo = product_repository
        self.product_module_repo = product_module_repository # Dependency for available modules logic
        self.module_repo = module_repository # Added for module existence checks
        self.configured_output_schema = ConfiguredBranchProductModuleOutputSchema(many=True) # Ensure many=True
        self.available_output_schema = AvailableProductModuleOutputSchema(many=True) # Ensure many=True
        self.message_schema = MessageSchema() # For returning standardized success/info messages

    # ... (existing methods like get_bpm_by_id, get_bpm_by_branch_and_product_module,
    #      get_configured_modules_for_branch_product, get_available_modules_for_product_with_status,
    #      create_bpm_record, delete_bpm_record, update_branch_product_module_configuration)

    def delete_branch_product_module_by_composite_keys(self, branch_id: int, product_id: int, module_id: int):
        """
        Deletes a BranchProductModule entry by its composite keys (branch_id, product_id, module_id).
        This involves finding the corresponding ProductModule first.
        """
        try:
            # 1. Validate branch existence
            self.branch_repo.get_by_id(branch_id) # Will raise BranchNotFoundError if not found

            # 2. Validate product existence
            self.product_repo.get_by_id(product_id) # Will raise ProductNotFoundError if not found

            # 3. Find the ProductModule entry for the given product_id and module_id
            product_module_obj = self.product_module_repo.get_by_product_and_module(product_id, module_id)
            if not product_module_obj:
                raise ProductModuleNotFoundError(f"Product-Module combination (Product ID: {product_id}, Module ID: {module_id}) not found.")

            # 4. Find the specific BranchProductModule to delete
            bpm_to_delete = self.repository.get_by_branch_and_product_module(branch_id, product_module_obj.product_module_id)
            if not bpm_to_delete:
                raise NotFoundError(f"Module {module_id} is not configured for Branch {branch_id} and Product {product_id}.")

            # 5. Delete the BPM record
            self.repository.delete(bpm_to_delete)
            return self.message_schema.dump({
                'status': 'success',
                'message': f"Module {module_id} successfully unconfigured from Branch {branch_id} for Product {product_id}."
            })
        except (BranchNotFoundError, ProductNotFoundError, ProductModuleNotFoundError, NotFoundError, DatabaseOperationError, ApplicationError):
            raise # Re-raise specific errors
        except Exception as e:
            log.exception(f"Unexpected error in delete_branch_product_module_by_composite_keys({branch_id}, {product_id}, {module_id}): {e}")
            raise ApplicationError("Failed to unconfigure module due to an internal error.", status_code=500)

branch_product_module_service = BranchProductModuleService()