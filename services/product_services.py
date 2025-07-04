import datetime
import logging

from repositories.product_repository import product_repository
from repositories.product_tag_repository import product_tag_repository 

from schemas.product_schemas import ProductInputSchema, ProductOutputSchema, ProductMinimalOutputSchema

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
            print(f"Loaded from DB: {products}")
            if minimal:
                return self.minimal_output_schema.dump(products)
            return self.output_schema.dump(products)
        except ApplicationError:
            raise 
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
            raise 
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
            validated_data = self.input_schema.load(data)

            code = validated_data['code']
            parent_product_id = validated_data.get('parent_product_id')
            product_tag_id = validated_data.get('product_tag_id')

            existing_product = self.repository.get_by_code(code)
            if existing_product:
                raise DuplicateProductCodeError(f"Product with code '{code}' already exists.")

            if parent_product_id:
                if parent_product_id == validated_data.get('product_id'): 
                     raise ValidationError("A product cannot be its own parent.")
                self.repository.get_by_id(parent_product_id) 

            if product_tag_id:
                self.product_tag_repo.get_by_id(product_tag_id) 

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
                
            )
            return self.output_schema.dump(new_product_obj)
        except ValidationError: 
            raise
        except NotFoundError as e:
            raise ValidationError(f"Related entity not found: {e.message}", errors={"general": e.message})
        except DuplicateProductCodeError: 
            raise
        except ApplicationError: 
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
            validated_data = self.input_schema.load(data, partial=True)

            product_obj = self.repository.get_by_id(product_id)

            if 'code' in validated_data and validated_data['code'] != product_obj.code:
                existing_product_with_new_code = self.repository.get_by_code(validated_data['code'])
                if existing_product_with_new_code and existing_product_with_new_code.product_id != product_id:
                    raise DuplicateProductCodeError(f"Product with code '{validated_data['code']}' already exists for another product.")

            if 'parent_product_id' in validated_data and validated_data['parent_product_id'] is not None:
                if validated_data['parent_product_id'] == product_id:
                     raise ValidationError("A product cannot be its own parent.")
                self.repository.get_by_id(validated_data['parent_product_id']) 
            elif 'parent_product_id' in validated_data and validated_data['parent_product_id'] is None:
                pass


            if 'product_tag_id' in validated_data and validated_data['product_tag_id'] is not None:
                self.product_tag_repo.get_by_id(validated_data['product_tag_id']) 
            elif 'product_tag_id' in validated_data and validated_data['product_tag_id'] is None:
                pass

            
            updated_product_obj = self.repository.update(product_obj, **validated_data)
            return self.output_schema.dump(updated_product_obj)
        except ValidationError:
            raise
        except NotFoundError: 
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
            product_obj = self.repository.get_by_id(product_id) 
            self.repository.delete(product_obj)
            return {"message": f"Product with ID {product_id} deleted successfully."}
        except NotFoundError:
            raise
        except ApplicationError: 
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_product({product_id}): {e}")
            raise ApplicationError("Failed to delete product due to an internal error.", status_code=500)

product_service = ProductService()
