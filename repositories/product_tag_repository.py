
from .base_repository import BaseRepository
from models import ProductTag 
from errors import ApplicationError, DatabaseOperationError, ProductTagNotFoundError
import logging

log = logging.getLogger(__name__)

class ProductTagRepository(BaseRepository):
    def __init__(self):
        super().__init__(ProductTag)

    def get_by_id(self, item_id):
        """
        Overrides BaseRepository's get_by_id to raise ProductTagNotFoundError.
        """
        try:
            item = self.model.query.get(item_id)
            if not item:
                raise ProductTagNotFoundError(f"Product Tag with ID {item_id} not found.")
            return item
        except ProductTagNotFoundError: 
            raise
        except Exception as e:
            log.exception(f"Database error fetching ProductTag by ID {item_id}: {e}")
            raise DatabaseOperationError(f"Could not retrieve Product Tag.")

    def get_by_name(self, name):
        """
        Retrieves a ProductTag record by its unique name.
        Raises ProductTagNotFoundError if not found.
        """
        try:
            product_tag = self.model.query.filter_by(name=name).first()
            if not product_tag:
                raise ProductTagNotFoundError(f"Product Tag with name '{name}' not found.")
            return product_tag
        except ProductTagNotFoundError:
            raise
        except Exception as e:
            log.exception(f"Database error fetching ProductTag by name '{name}': {e}")
            raise DatabaseOperationError("Could not retrieve Product Tag by name.")

product_tag_repository = ProductTagRepository()
