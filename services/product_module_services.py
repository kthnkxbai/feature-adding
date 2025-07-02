import datetime
import logging
import json 

from repositories.product_module_repository import product_module_repository
from repositories.product_repository import product_repository
from repositories.module_repository import module_repository

from schemas.product_module_schemas import ProductModuleInputSchema, ProductModuleOutputSchema

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
            raise 
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
            raise 
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
            validated_data = self.input_schema.load(data)

            product_id = validated_data['product_id']
            module_id = validated_data['module_id']

            self.product_repo.get_by_id(product_id)
            self.module_repo.get_by_id(module_id)

            existing_product_module = self.repository.get_by_product_and_module(product_id, module_id)
            if existing_product_module:
                raise DuplicateError("A configuration for this product and module already exists.")

            new_product_module_obj = self.repository.create(
                product_id=product_id,
                module_id=module_id,
                is_active=validated_data.get('is_active', True), 
                notes=validated_data.get('notes'),
                created_at=datetime.datetime.utcnow()
            )
            return self.output_schema.dump(new_product_module_obj)
        except ValidationError: 
            raise
        except NotFoundError as e: 
            raise ValidationError(f"Related entity not found: {e.message}", errors={"general": e.message})
        except DuplicateError: 
            raise
        except ApplicationError: 
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
            validated_data = self.input_schema.load(data, partial=True)

            product_module_obj = self.repository.get_by_id(product_module_id)

            new_product_id = validated_data.get('product_id', product_module_obj.product_id)
            new_module_id = validated_data.get('module_id', product_module_obj.module_id)

            if new_product_id != product_module_obj.product_id:
                self.product_repo.get_by_id(new_product_id) 
            if new_module_id != product_module_obj.module_id:
                self.module_repo.get_by_id(new_module_id) 

            if (new_product_id, new_module_id) != (product_module_obj.product_id, product_module_obj.module_id):
                existing_duplicate = self.repository.get_by_product_and_module(new_product_id, new_module_id)
                if existing_duplicate and existing_duplicate.product_module_id != product_module_id:
                    raise DuplicateError("A configuration for this updated product and module combination already exists.")

            validated_data['updated_at'] = datetime.datetime.utcnow() 
            updated_product_module_obj = self.repository.update(product_module_obj, **validated_data)
            return self.output_schema.dump(updated_product_module_obj)
        except ValidationError:
            raise
        except NotFoundError: 
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
            product_module_obj = self.repository.get_by_id(product_module_id) 
            self.repository.delete(product_module_obj)
            return {"message": f"ProductModule with ID {product_module_id} deleted successfully."}
        except NotFoundError:
            raise
        except ApplicationError: 
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_product_module({product_module_id}): {e}")
            raise ApplicationError("Failed to delete product module due to an internal error.", status_code=500)

product_module_service = ProductModuleService()
