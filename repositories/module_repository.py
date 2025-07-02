
from extensions import db
from models import Module
from errors import DatabaseOperationError
from sqlalchemy import exc

class ModuleRepository:
    def get_all(self):
        """Retrieves all Module records."""
        try:
            return Module.query.all()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve all modules: {e}") from e

    def get_by_id(self, module_id):
        """Retrieves a Module record by its primary key."""
        try:
            return db.session.get(Module, module_id)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve module with ID {module_id}: {e}") from e

    def get_by_name(self, name):
        """Retrieves a Module record by its name."""
        try:
            return Module.query.filter_by(name=name).first()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve module with name '{name}': {e}") from e

    def get_by_code(self, code):
        """Retrieves a Module record by its code."""
        try:
            return Module.query.filter_by(code=code).first()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve module with code '{code}': {e}") from e

    def add(self, module):
        """Adds a new Module record to the session."""
        try:
            db.session.add(module)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error adding module '{module.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to add module '{module.name}': {e}") from e

    def delete(self, module):
        """Deletes a Module record from the session."""
        try:
            db.session.delete(module)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error deleting module '{module.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete module '{module.name}': {e}") from e

    def save_changes(self):
        """Commits changes to the database."""
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Failed to commit module changes: {e}") from e

    def rollback_changes(self):
        """Rolls back changes in the database session."""
        db.session.rollback()

module_repository = ModuleRepository()
