
from repositories.branch_repository import branch_repository
from schemas.branch_schemas import BranchBaseSchema, BranchInputSchema, BranchOutputSchema
from errors import BranchNotFoundError, DuplicateBranchCodeError, DatabaseOperationError, ValidationError
from models import Branch 
class BranchService:
    def __init__(self, repository=branch_repository, schema=BranchBaseSchema(), input_schema=BranchInputSchema()):
        self.repository = repository
        self.schema = BranchOutputSchema()
        self.input_schema = input_schema

    def get_all_branches(self):
        """Retrieves and serializes all Branch records."""
        try:
            branches = self.repository.get_all()
            return self.schema.dump(branches, many=True)
        except DatabaseOperationError as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting all branches: {e}")

    def get_branch_by_id(self, branch_id):
        """Retrieves and serializes a single Branch record by ID."""
        try:
            branch = self.repository.get_by_id(branch_id)
            if not branch:
                raise BranchNotFoundError(f"Branch with ID {branch_id} not found.")
            return self.schema.dump(branch)
        except (BranchNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting branch by ID {branch_id}: {e}")

    def get_branches_by_tenant(self, tenant_id):
        """Retrieves and serializes all Branch records for a given tenant_id."""
        try:
            branches = self.repository.get_by_tenant_id(tenant_id)
            return self.schema.dump(branches, many=True)
        except DatabaseOperationError as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting branches for tenant {tenant_id}: {e}")

    def create_branch(self, tenant_id, branch_data):
        """Validates and creates a new Branch record for a specific tenant."""
        try:
            validated_data = self.input_schema.load(branch_data)
            validated_data['tenant_id'] = tenant_id 
            existing_branch = self.repository.get_by_code_and_tenant(validated_data['code'], tenant_id)
            if existing_branch:
                raise DuplicateBranchCodeError(validated_data['code'], tenant_id)

            branch = Branch(**validated_data)
            self.repository.add(branch)
            self.repository.save_changes()
            return self.schema.dump(branch)
        except (ValidationError, DuplicateBranchCodeError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while creating branch for tenant {tenant_id}: {e}")

    def update_branch(self, branch_id, update_data):
        """Updates an existing Branch record."""
        try:
            branch = self.repository.get_by_id(branch_id)
            if not branch:
                raise BranchNotFoundError(f"Branch with ID {branch_id} not found.")

            validated_data = self.input_schema.load(update_data, partial=True)

            if 'code' in validated_data and validated_data['code'] != branch.code:
                existing_branch = self.repository.get_by_code_and_tenant(validated_data['code'], branch.tenant_id)
                if existing_branch and existing_branch.branch_id != branch_id:
                    raise DuplicateBranchCodeError(validated_data['code'], branch.tenant_id)

            for key, value in validated_data.items():
                setattr(branch, key, value)

            self.repository.save_changes()
            return self.schema.dump(branch)
        except (BranchNotFoundError, ValidationError, DuplicateBranchCodeError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while updating branch ID {branch_id}: {e}")

    def delete_branch(self, branch_id):
        """Deletes a Branch record."""
        try:
            branch = self.repository.get_by_id(branch_id)
            if not branch:
                raise BranchNotFoundError(f"Branch with ID {branch_id} not found.")

            self.repository.delete(branch)
            self.repository.save_changes()
            return {"message": f"Branch '{branch.name}' deleted successfully."}
        except (BranchNotFoundError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while deleting branch ID {branch_id}: {e}")

branch_service = BranchService()
