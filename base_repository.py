from extensions import db
from errors import NotFoundError, ApplicationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

log = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_all(self):
        try:
            return self.model.query.all()
        except SQLAlchemyError as e:
            log.exception(f"Database error fetching all {self.model.__name__}: {e}")
            raise ApplicationError(f"Could not retrieve {self.model.__name__} data.", status_code=500)

    def get_by_id(self, item_id):
        try:
            item = db.session.get(self.model, item_id)
            if not item:
                raise NotFoundError(f"{self.model.__name__} with ID {item_id} not found.")
            return item
        except NotFoundError: 
            raise
        except SQLAlchemyError as e:
            log.exception(f"Database error fetching {self.model.__name__} by ID {item_id}: {e}")
            raise ApplicationError(f"Could not retrieve {self.model.__name__}.", status_code=500)

    def create(self, **kwargs):
        try:
            item = self.model(**kwargs)
            db.session.add(item)
            db.session.commit()
            return item
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error creating {self.model.__name__}: {e}")
            raise ApplicationError(f"Duplicate entry or related record missing for {self.model.__name__}.", status_code=409)
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"Database error creating {self.model.__name__}: {e}")
            raise ApplicationError(f"Could not create {self.model.__name__}.", status_code=500)

    def update(self, item, **kwargs):
        try:
            for key, value in kwargs.items():
                setattr(item, key, value)
            db.session.commit()
            return item
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error updating {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"Duplicate entry or related record missing when updating {self.model.__name__}.", status_code=409)
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"Database error updating {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"Could not update {self.model.__name__}.", status_code=500)

    def delete(self, item):
        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except IntegrityError as e:
            db.session.rollback()
            log.exception(f"Integrity error deleting {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"Cannot delete {self.model.__name__} due to existing related records.", status_code=409)
        except SQLAlchemyError as e:
            db.session.rollback()
            log.exception(f"Database error deleting {self.model.__name__} (ID: {getattr(item, 'id', 'N/A')}): {e}")
            raise ApplicationError(f"Could not delete {self.model.__name__}.", status_code=500)

