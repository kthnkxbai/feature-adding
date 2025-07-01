from .base_repository import BaseRepository
from models import Product 
from errors import ApplicationError, NotFoundError
import logging

log = logging.getLogger(__name__)

class ProductRepository(BaseRepository):
    def __init__(self):
        super().__init__(Product)

    def get_by_code(self, code):
        """
        Retrieves a Product record by its unique code.
        """
        try:
            return self.model.query.filter_by(code=code).first()
        except Exception as e:
            log.exception(f"Database error fetching Product by code '{code}': {e}")
            raise ApplicationError("Could not retrieve Product by code.", status_code=500)

    def get_all_products_with_tags_and_parents(self):
        """
        Retrieves all Product records with joined ProductTag and Parent Product details.
        (Example of a more complex query if needed for specific use cases)
        """
        
        try:
            return self.model.query.all() 
        except Exception as e:
            log.exception(f"Database error fetching all Products with details: {e}")
            raise ApplicationError("Could not retrieve Product data with details.", status_code=500)


product_repository = ProductRepository()
