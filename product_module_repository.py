from .base_repository import BaseRepository
from models import ProductModule
from extensions import db
from errors import NotFoundError, ApplicationError
from sqlalchemy.orm import joinedload
import logging

log = logging.getLogger(__name__)

class ProductModuleRepository(BaseRepository):
    def __init__(self):
        super().__init__(ProductModule)

    def get_by_product_and_module(self, product_id, module_id):
        """
        Retrieves a ProductModule record by product_id and module_id.
        """
        try:
            product_module = self.model.query.filter_by(
                product_id=product_id,
                module_id=module_id
            ).first()
            return product_module
        except Exception as e:
            log.exception(f"Database error fetching ProductModule by product_id={product_id}, module_id={module_id}: {e}")
            raise ApplicationError("Could not retrieve ProductModule.", status_code=500)

    def get_all_with_details(self):
        """
        Retrieves all ProductModule records with joined Product and Module details.
        """
        try:
            return self.model.query.options(
                joinedload(ProductModule.product),
                joinedload(ProductModule.module)
            ).all()
        except Exception as e:
            log.exception(f"Database error fetching all ProductModules with details: {e}")
            raise ApplicationError("Could not retrieve ProductModule data with details.", status_code=500)

    def get_by_id_with_details(self, product_module_id):
        """
        Retrieves a single ProductModule record by ID with joined Product and Module details.
        """
        try:
            item = self.model.query.options(
                joinedload(ProductModule.product),
                joinedload(ProductModule.module)
            ).filter_by(product_module_id=product_module_id).first()
            if not item:
                raise NotFoundError(f"ProductModule with ID {product_module_id} not found.")
            return item
        except NotFoundError:
            raise
        except Exception as e:
            log.exception(f"Database error fetching ProductModule by ID {product_module_id} with details: {e}")
            raise ApplicationError("Could not retrieve ProductModule details.", status_code=500)

    def get_all_for_product(self, product_id):
        """
        Retrieves all ProductModule records linked to a specific product.
        """
        try:
            return self.model.query.filter_by(product_id=product_id).all()
        except Exception as e:
            log.exception(f"Database error fetching ProductModules for product {product_id}: {e}")
            raise ApplicationError("Could not retrieve ProductModules for product.", status_code=500)

    def get_all_for_product_with_module_details(self, product_id):
        """
        Retrieves all ProductModule records linked to a specific product,
        with associated module details.
        """
        try:
            return self.model.query.options(
                joinedload(ProductModule.module)
            ).filter_by(product_id=product_id).all()
        except Exception as e:
            log.exception(f"Database error fetching ProductModules with module details for product {product_id}: {e}")
            raise ApplicationError("Could not retrieve ProductModules with module details.", status_code=500)


product_module_repository = ProductModuleRepository()
