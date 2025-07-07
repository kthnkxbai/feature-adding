# services/product_service.py
import datetime
import logging

# Repositories
from repositories.product_repository import product_repository
from repositories.product_tag_repository import product_tag_repository # For checking related entities

# Schemas
from schemas.product_schemas import ProductInputSchema, ProductOutputSchema, ProductMinimalOutputSchema

# Custom Errors
from errors import ApplicationError, NotFoundError, ValidationError, DuplicateProductCodeError

log = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.repository = product_repository
        self.product_tag_repo = product_tag_repository
        self.input_schema = ProductInputSchema()
        self.output_schema = ProductOutputSchema()
        self.minimal_output_schema = ProductMinimalOutputSchema()

    def get_all_products(self, minimal: bool = False):
        """
        Retrieves all product records.
        Args:
            minimal (bool): If True, returns minimal product data (id, name, code).
        Returns:
            list: A list of serialized product dictionaries.
        """
        try:
            products = self.repository.get_all()
            if minimal:
                return self.minimal_output_schema.dump(products)
            return self.output_schema.dump(products)
        except ApplicationError:
            raise # Re-raise custom application errors
        except Exception as e:
            log.exception(f"Unexpected error in get_all_products(minimal={minimal}): {e}")
            raise ApplicationError("Failed to retrieve all products.", status_code=500)

    def get_product_by_id(self, product_id):
        """
        Retrieves a single product record by its ID.
        """
        try:
            product = self.repository.get_by_id(product_id)
            return self.output_schema.dump(product)
        except NotFoundError:
            raise # Re-raise for specific 404 handling in the route
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_product_by_id({product_id}): {e}")
            raise ApplicationError("Failed to retrieve product by ID.", status_code=500)

    def create_product(self, data):
        """
        Creates a new product record.
        Validates input, checks for unique code, and checks for existence of related product tag or parent product.
        """
        try:
            # 1. Validate input data using Marshmallow schema
            validated_data = self.input_schema.load(data)

            code = validated_data['code']
            parent_product_id = validated_data.get('parent_product_id')
            product_tag_id = validated_data.get('product_tag_id')

            # 2. Check for duplicate product code
            existing_product = self.repository.get_by_code(code)
            if existing_product:
                raise DuplicateProductCodeError(f"Product with code '{code}' already exists.")

            # 3. Check if parent_product_id exists if provided
            if parent_product_id:
                if parent_product_id == validated_data.get('product_id'): # Prevent self-referencing if product_id is also in data
                     raise ValidationError("A product cannot be its own parent.")
                self.repository.get_by_id(parent_product_id) # This will raise NotFoundError if not found

            # 4. Check if product_tag_id exists if provided
            if product_tag_id:
                self.product_tag_repo.get_by_id(product_tag_id) # This will raise NotFoundError if not found

            # 5. Create the Product record in the database
            new_product_obj = self.repository.create(
                name=validated_data['name'],
                code=code,
                description=validated_data.get('description'),
                tag=validated_data.get('tag'),
                sequence=validated_data.get('sequence'),
                parent_product_id=parent_product_id,
                is_inbound=validated_data.get('is_inbound', False),
                product_tag_id=product_tag_id,
                supported_file_formats=validated_data.get('supported_file_formats'),
                created_at=datetime.datetime.utcnow()
            )
            # 6. Return the serialized new object
            return self.output_schema.dump(new_product_obj)
        except ValidationError: # Marshmallow or custom validation error
            raise
        except NotFoundError as e: # Parent Product or Product Tag not found
            raise ValidationError(f"Related entity not found: {e.message}", errors={"general": e.message})
        except DuplicateProductCodeError: # Our custom duplicate error
            raise
        except ApplicationError: # Catching other application-level errors from repository
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_product with data {data}: {e}")
            raise ApplicationError("Failed to create product due to an internal error.", status_code=500)

    def update_product(self, product_id, data):
        """
        Updates an existing product record.
        Validates input, checks for existence, and handles duplicate code checks.
        Handles parent_product_id and product_tag_id updates.
        """
        try:
            # 1. Validate input data (allow partial updates)
            validated_data = self.input_schema.load(data, partial=True)

            # 2. Retrieve the existing Product object
            product_obj = self.repository.get_by_id(product_id)

            # 3. Handle potential change in 'code' and check for duplicates
            if 'code' in validated_data and validated_data['code'] != product_obj.code:
                existing_product_with_new_code = self.repository.get_by_code(validated_data['code'])
                if existing_product_with_new_code and existing_product_with_new_code.product_id != product_id:
                    raise DuplicateProductCodeError(f"Product with code '{validated_data['code']}' already exists for another product.")

            # 4. Handle potential change in 'parent_product_id'
            if 'parent_product_id' in validated_data and validated_data['parent_product_id'] is not None:
                if validated_data['parent_product_id'] == product_id:
                     raise ValidationError("A product cannot be its own parent.")
                self.repository.get_by_id(validated_data['parent_product_id']) # Check if new parent_product_id exists
            elif 'parent_product_id' in validated_data and validated_data['parent_product_id'] is None:
                # If parent_product_id is explicitly set to None, allow it
                pass


            # 5. Handle potential change in 'product_tag_id'
            if 'product_tag_id' in validated_data and validated_data['product_tag_id'] is not None:
                self.product_tag_repo.get_by_id(validated_data['product_tag_id']) # Check if new product_tag_id exists
            elif 'product_tag_id' in validated_data and validated_data['product_tag_id'] is None:
                # If product_tag_id is explicitly set to None, allow it
                pass

            # 6. Update the Product record in the database
            validated_data['updated_at'] = datetime.datetime.utcnow() # Set updated timestamp
            updated_product_obj = self.repository.update(product_obj, **validated_data)
            return self.output_schema.dump(updated_product_obj)
        except ValidationError:
            raise
        except NotFoundError: # Product itself not found, or related parent/tag not found during checks
            raise
        except DuplicateProductCodeError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_product({product_id}) with data {data}: {e}")
            raise ApplicationError("Failed to update product due to an internal error.", status_code=500)

    def delete_product(self, product_id):
        """
        Deletes a product record.
        """
        try:
            product_obj = self.repository.get_by_id(product_id) # Ensures existence before delete
            self.repository.delete(product_obj)
            return {"message": f"Product with ID {product_id} deleted successfully."}
        except NotFoundError:
            raise
        except ApplicationError: # Catches IntegrityError from repo if related records exist
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_product({product_id}): {e}")
            raise ApplicationError("Failed to delete product due to an internal error.", status_code=500)

product_service = ProductService()
