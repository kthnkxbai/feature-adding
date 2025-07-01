# services/product_module_service.py
import datetime
import logging
import json # Import json for eligibility_config if it's stored as JSON string

# Repositories
from repositories.product_module_repository import product_module_repository
from repositories.product_repository import product_repository
from repositories.module_repository import module_repository

# Schemas
from schemas.product_module_schemas import ProductModuleInputSchema, ProductModuleOutputSchema
# Assuming other necessary schemas like ProductOutputSchema, ModuleOutputSchema are defined and imported in product_module_schemas
# or imported directly if needed:
# from schemas.product_schemas import ProductOutputSchema
# from schemas.module_schemas import ModuleOutputSchema

# Custom Errors
from errors import ApplicationError, NotFoundError, ValidationError, DuplicateError

log = logging.getLogger(__name__)

class ProductModuleService:
    def __init__(self):
        self.repository = product_module_repository
        self.product_repo = product_repository
        self.module_repo = module_repository
        self.input_schema = ProductModuleInputSchema()
        self.output_schema = ProductModuleOutputSchema()

    def get_all_product_modules(self):
        """
        Retrieves all product module configurations with nested product and module details.
        """
        try:
            product_modules = self.repository.get_all_with_details()
            return self.output_schema.dump(product_modules)
        except ApplicationError:
            raise # Re-raise custom application errors
        except Exception as e:
            log.exception(f"Unexpected error in get_all_product_modules: {e}")
            raise ApplicationError("Failed to retrieve all product modules.", status_code=500)

    def get_product_module_by_id(self, product_module_id):
        """
        Retrieves a single product module configuration by its ID.
        """
        try:
            product_module = self.repository.get_by_id_with_details(product_module_id)
            return self.output_schema.dump(product_module)
        except NotFoundError:
            raise # Re-raise for specific 404 handling in the route
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_product_module_by_id({product_module_id}): {e}")
            raise ApplicationError("Failed to retrieve product module by ID.", status_code=500)

    def create_product_module(self, data):
        """
        Creates a new product module configuration.
        Validates input and checks for existence of related product and module.
        Checks for duplicate product-module combinations.
        """
        try:
            # 1. Validate input data using Marshmallow schema
            validated_data = self.input_schema.load(data)

            product_id = validated_data['product_id']
            module_id = validated_data['module_id']

            # 2. Check if the associated Product and Module exist
            # These calls will raise NotFoundError if entities are not found
            self.product_repo.get_by_id(product_id)
            self.module_repo.get_by_id(module_id)

            # 3. Check if a ProductModule with these product_id and module_id already exists
            existing_product_module = self.repository.get_by_product_and_module(product_id, module_id)
            if existing_product_module:
                raise DuplicateError("A configuration for this product and module already exists.")

            # 4. Create the ProductModule record in the database
            new_product_module_obj = self.repository.create(
                product_id=product_id,
                module_id=module_id,
                is_active=validated_data.get('is_active', True), # Use default if not provided
                notes=validated_data.get('notes'),
                created_at=datetime.datetime.utcnow()
            )
            # 5. Return the serialized new object
            return self.output_schema.dump(new_product_module_obj)
        except ValidationError: # Marshmallow validation error caught here
            raise
        except NotFoundError as e: # Product or Module not found (from repo calls)
            # Re-raise as ValidationError with details to give client clearer feedback
            raise ValidationError(f"Related entity not found: {e.message}", errors={"general": e.message})
        except DuplicateError: # Our custom duplicate error
            raise
        except ApplicationError: # Catching other application-level errors from repository
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_product_module with data {data}: {e}")
            raise ApplicationError("Failed to create product module due to an internal error.", status_code=500)

    def update_product_module(self, product_module_id, data):
        """
        Updates an existing product module configuration.
        Validates input, checks for existence, and handles duplicate checks
        if product_id or module_id are changed.
        """
        try:
            # 1. Validate input data (allow partial updates)
            validated_data = self.input_schema.load(data, partial=True)

            # 2. Retrieve the existing ProductModule object
            product_module_obj = self.repository.get_by_id(product_module_id)

            # 3. Handle potential changes to product_id or module_id and check for new duplicates
            new_product_id = validated_data.get('product_id', product_module_obj.product_id)
            new_module_id = validated_data.get('module_id', product_module_obj.module_id)

            # If either product_id or module_id is changing, check existence and potential duplicates
            if new_product_id != product_module_obj.product_id:
                self.product_repo.get_by_id(new_product_id) # Check if new product_id exists
            if new_module_id != product_module_obj.module_id:
                self.module_repo.get_by_id(new_module_id) # Check if new module_id exists

            # Check for duplicate combination if product_id or module_id changed
            if (new_product_id, new_module_id) != (product_module_obj.product_id, product_module_obj.module_id):
                existing_duplicate = self.repository.get_by_product_and_module(new_product_id, new_module_id)
                if existing_duplicate and existing_duplicate.product_module_id != product_module_id:
                    raise DuplicateError("A configuration for this updated product and module combination already exists.")

            # 4. Update the ProductModule record in the database
            validated_data['updated_at'] = datetime.datetime.utcnow() # Set updated timestamp
            updated_product_module_obj = self.repository.update(product_module_obj, **validated_data)
            return self.output_schema.dump(updated_product_module_obj)
        except ValidationError:
            raise
        except NotFoundError: # ProductModule itself not found, or related product/module not found during checks
            raise
        except DuplicateError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_product_module({product_module_id}) with data {data}: {e}")
            raise ApplicationError("Failed to update product module due to an internal error.", status_code=500)

    def delete_product_module(self, product_module_id):
        """
        Deletes a product module configuration.
        """
        try:
            product_module_obj = self.repository.get_by_id(product_module_id) # Ensures existence before delete
            self.repository.delete(product_module_obj)
            return {"message": f"ProductModule with ID {product_module_id} deleted successfully."}
        except NotFoundError:
            raise
        except ApplicationError: # Catches IntegrityError from repo if related records exist
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_product_module({product_module_id}): {e}")
            raise ApplicationError("Failed to delete product module due to an internal error.", status_code=500)

product_module_service = ProductModuleService()
