import datetime
import logging

from repositories.product_tag_repository import product_tag_repository

from schemas.product_tag_schemas import ProductTagInputSchema, ProductTagOutputSchema

from errors import ApplicationError, DatabaseOperationError, ProductTagNotFoundError, ValidationError, DuplicateError

log = logging.getLogger(__name__)

class ProductTagService:
    def __init__(self):
        self.repository = product_tag_repository
        self.input_schema = ProductTagInputSchema()
        self.output_schema = ProductTagOutputSchema()

    def get_all_product_tags(self):
        """
        Retrieves all product tag records.
        """
        try:
            product_tags = self.repository.get_all()
            return self.output_schema.dump(product_tags)
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_all_product_tags: {e}")
            raise ApplicationError("Failed to retrieve all product tags.", status_code=500)

    def get_product_tag_by_id(self, product_tag_id):
        """
        Retrieves a single product tag record by its ID.
        """
        try:
            product_tag = self.repository.get_by_id(product_tag_id) 
            return self.output_schema.dump(product_tag)
        except ProductTagNotFoundError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_product_tag_by_id({product_tag_id}): {e}")
            raise ApplicationError("Failed to retrieve product tag by ID.", status_code=500)

    def create_product_tag(self, data):
        """
        Creates a new product tag record.
        Validates input and checks for unique product tag name.
        """
        try:
            validated_data = self.input_schema.load(data)
            name = validated_data['name']

            existing_product_tag = self.repository.get_by_name(name)
            if existing_product_tag:
                raise DuplicateError(f"Product Tag with name '{name}' already exists.")

            new_product_tag_obj = self.repository.create(
                name=name,
                description=validated_data.get('description'),
                is_active=validated_data.get('is_active', True),
                created_at=datetime.datetime.utcnow()
            )
            return self.output_schema.dump(new_product_tag_obj)
        except ValidationError:
            raise
        except DuplicateError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_product_tag with data {data}: {e}")
            raise ApplicationError("Failed to create product tag due to an internal error.", status_code=500)

    def update_product_tag(self, product_tag_id, data):
        """
        Updates an existing product tag record.
        Validates input, checks for existence, and handles duplicate name checks.
        """
        try:
            validated_data = self.input_schema.load(data, partial=True)
            product_tag_obj = self.repository.get_by_id(product_tag_id) 
            if 'name' in validated_data and validated_data['name'] != product_tag_obj.name:
                existing_product_tag_with_new_name = self.repository.get_by_name(validated_data['name'])
                if existing_product_tag_with_new_name and existing_product_tag_with_new_name.product_tag_id != product_tag_id:
                    raise DuplicateError(f"Product Tag with name '{validated_data['name']}' already exists.")

            validated_data['updated_at'] = datetime.datetime.utcnow()
            updated_product_tag_obj = self.repository.update(product_tag_obj, **validated_data)
            return self.output_schema.dump(updated_product_tag_obj)
        except ValidationError:
            raise
        except ProductTagNotFoundError:
            raise
        except DuplicateError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_product_tag({product_tag_id}) with data {data}: {e}")
            raise ApplicationError("Failed to update product tag due to an internal error.", status_code=500)

    def delete_product_tag(self, product_tag_id):
        """
        Deletes a product tag record.
        """
        try:
            product_tag_obj = self.repository.get_by_id(product_tag_id) 
            self.repository.delete(product_tag_obj)
            return {"message": f"Product Tag with ID {product_tag_id} deleted successfully."}
        except ProductTagNotFoundError:
            raise
        except DatabaseOperationError: 
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_product_tag({product_tag_id}): {e}")
            raise ApplicationError("Failed to delete product tag due to an internal error.", status_code=500)

product_tag_service = ProductTagService()
