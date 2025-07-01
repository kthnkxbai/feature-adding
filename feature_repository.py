
from extensions import db
from models import Feature
from errors import DatabaseOperationError
from sqlalchemy import exc

class FeatureRepository:
    def get_all(self):
        """Retrieves all Feature records."""
        try:
            return Feature.query.all()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve all features: {e}") from e

    def get_by_id(self, feature_id):
        """Retrieves a Feature record by its primary key."""
        try:
            return db.session.get(Feature, feature_id)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve feature with ID {feature_id}: {e}") from e

    def get_by_name(self, name):
        """Retrieves a Feature record by its name."""
        try:
            return Feature.query.filter_by(name=name).first()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve feature with name '{name}': {e}") from e

    def add(self, feature):
        """Adds a new Feature record to the session."""
        try:
            db.session.add(feature)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error adding feature '{feature.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to add feature '{feature.name}': {e}") from e

    def delete(self, feature):
        """Deletes a Feature record from the session."""
        try:
            db.session.delete(feature)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error deleting feature '{feature.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete feature '{feature.name}': {e}") from e

    def save_changes(self):
        """Commits changes to the database."""
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Failed to commit feature changes: {e}") from e

    def rollback_changes(self):
        """Rolls back changes in the database session."""
        db.session.rollback()

feature_repository = FeatureRepository()
