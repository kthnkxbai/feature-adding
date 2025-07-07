from extensions import db
from errors import NotFoundError, ApplicationError, DatabaseOperationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

log = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_all(self):
        try:
            
            result = self.model.query.all()
            
            return result
        except SQLAlchemyError as e:
            log.exception(f"SQLAlchemyError in BaseRepository.get_all for {self.model.__name__}: {e}")
            raise DatabaseOperationError(f"Database error retrieving all {self.model.__name__} data: {e}")
        except Exception as e:
            log.exception(f"Unexpected error in BaseRepository.get_all for {self.model.__name__}: {e}")
            raise ApplicationError(f"An unexpected error occurred while retrieving all {self.model.__name__} data.", status_code=500)

    def get_by_id(self, item_id):
        try:
            print(f"DEBUG: BaseRepository.get_by_id - Attempting to get {self.model.__name__} with ID {item_id}")
            item = db.session.get(self.model, item_id)
            if not item:
                raise NotFoundError(f"{self.model.__name__} with ID {item_id} not found.")
            print(f"DEBUG: BaseRepository.get_by_id - Found {self.model.__name__}: {item}")
            return item
        except NotFoundError: 
            raise
        except SQLAlchemyError as e:
            log.exception(f"SQLAlchemyError in BaseRepository.get_by_id for {self.model.__name__} (ID {item_id}): {e}")
            raise DatabaseOperationError(f"Database error retrieving {self.model.__name__}.")
        except Exception as e:
            log.exception(f"Unexpected error in BaseRepository.get_by_id for {self.model.__name__} (ID {item_id}): {e}")
            raise ApplicationError(f"An unexpected error occurred while retrieving {self.model.__name__}.", status_code=500)

    def create(self, **kwargs):
        try:
            print(f"DEBUG: BaseRepository.create - Attempting to create {self.model.__name__} with data: {kwargs}")
            item = self.model(**kwargs)
            db.session.add(item)
            db.session.commit()
            print(f"DEBUG: BaseRepository.create - Successfully created {self.model.__name__}: {item}")
            return item
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error creating {self.model.__name__}: {e}")
            raise DatabaseOperationError(f"Duplicate entry or related record missing for {self.model.__name__}.")
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"SQLAlchemyError in BaseRepository.create for {self.model.__name__}: {e}")
            raise DatabaseOperationError(f"Database error creating {self.model.__name__}.")
        except Exception as e:
            db.session.rollback()
            log.exception(f"Unexpected error in BaseRepository.create for {self.model.__name__}: {e}")
            raise ApplicationError(f"An unexpected error occurred while creating {self.model.__name__}.", status_code=500)

    def update(self, item, **kwargs):
        try:
            print(f"DEBUG: BaseRepository.update - Attempting to update {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}) with data: {kwargs}")
            for key, value in kwargs.items():
                setattr(item, key, value)
            db.session.commit()
            print(f"DEBUG: BaseRepository.update - Successfully updated {self.model.__name__}: {item}")
            return item
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error updating {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise DatabaseOperationError(f"Duplicate entry or related record missing when updating {self.model.__name__}.")
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"SQLAlchemyError in BaseRepository.update for {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise DatabaseOperationError(f"Could not update {self.model.__name__}.")
        except Exception as e:
            db.session.rollback()
            log.exception(f"Unexpected error in BaseRepository.update for {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"An unexpected error occurred while updating {self.model.__name__}.", status_code=500)

    def delete(self, item):
        try:
            print(f"DEBUG: BaseRepository.delete - Attempting to delete {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')})")
            db.session.delete(item)
            db.session.commit()
            print(f"DEBUG: BaseRepository.delete - Successfully deleted {self.model.__name__}.")
            return True
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error deleting {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise DatabaseOperationError(f"Cannot delete {self.model.__name__} due to existing related records.")
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"SQLAlchemyError in BaseRepository.delete for {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise DatabaseOperationError(f"Could not delete {self.model.__name__}.")
        except Exception as e:
            db.session.rollback()
            log.exception(f"Unexpected error in BaseRepository.delete for {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"An unexpected error occurred while deleting {self.model.__name__}.", status_code=500)
