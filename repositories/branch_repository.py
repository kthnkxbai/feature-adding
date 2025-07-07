from extensions import db
from models import Branch
from errors import DatabaseOperationError
from sqlalchemy import exc

class BranchRepository:
    def get_all(self):
        """Retrieves all Branch records."""
        try:
            return Branch.query.all()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve all branches: {e}") from e

    def get_by_id(self, branch_id):
        """Retrieves a Branch record by its primary key."""
        try:
            return db.session.get(Branch, branch_id)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve branch with ID {branch_id}: {e}") from e

    def get_by_tenant_id(self, tenant_id):
        """Retrieves all Branch records for a given tenant_id."""
        try:
            return Branch.query.filter_by(tenant_id=tenant_id).all()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve branches for tenant ID {tenant_id}: {e}") from e

    def get_by_code_and_tenant(self, code, tenant_id):
        """Retrieves a Branch by its code and tenant_id."""
        try:
            return Branch.query.filter_by(code=code, tenant_id=tenant_id).first()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve branch with code '{code}' for tenant {tenant_id}: {e}") from e

    def add(self, branch):
        """Adds a new Branch record to the session."""
        try:
            db.session.add(branch)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error adding branch '{branch.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to add branch '{branch.name}': {e}") from e

    def delete(self, branch):
        """Deletes a Branch record from the session."""
        try:
            db.session.delete(branch)
        except exc.IntegrityError as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Integrity error deleting branch '{branch.name}': {e.orig}") from e
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete branch '{branch.name}': {e}") from e

    def save_changes(self):
        """Commits changes to the database."""
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Failed to commit branch changes: {e}") from e

    def rollback_changes(self):
        """Rolls back changes in the database session."""
        db.session.rollback()

branch_repository = BranchRepository()
