from .base_repository import BaseRepository
from models import Feature
from errors import DatabaseOperationError, FeatureNotFoundError
import logging

log = logging.getLogger(__name__)

class FeatureRepository(BaseRepository):
    def __init__(self):
        super().__init__(Feature)

    def get_by_id(self, item_id):
        """
        Overrides BaseRepository's get_by_id to raise FeatureNotFoundError.
        """
        try:
            item = self.model.query.get(item_id)
            if not item:
                raise FeatureNotFoundError(f"Feature with ID {item_id} not found.")
            return item
        except FeatureNotFoundError:
            raise
        except Exception as e:
            log.exception(f"Database error fetching Feature by ID {item_id}: {e}")
            raise DatabaseOperationError(f"Could not retrieve Feature.")

    def get_by_code(self, code):
        """
        Retrieves a Feature record by its unique code.
        """
        try:
            return self.model.query.filter_by(code=code).first()
        except Exception as e:
            log.exception(f"Database error fetching Feature by code '{code}': {e}")
            raise DatabaseOperationError("Could not retrieve Feature by code.")

feature_repository = FeatureRepository()