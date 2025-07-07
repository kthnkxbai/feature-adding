from repositories.module_repository import module_repository
from schemas.module_schemas import ModuleBaseSchema, ModuleInputSchema
from errors import ModuleNotFoundError, DatabaseOperationError, ValidationError
from models import Module

class ModuleService:
    def __init__(self, repository=module_repository, schema=ModuleBaseSchema(), input_schema=ModuleInputSchema()):
        self.repository = repository
        self.schema = schema
        self.input_schema = input_schema

    def get_all_modules(self):
        """Retrieves and serializes all Module records."""
        try:
            modules = self.repository.get_all()
            return self.schema.dump(modules, many=True)
        except DatabaseOperationError as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting all modules: {e}")

    def get_module_by_id(self, module_id):
        """Retrieves and serializes a single Module record by ID."""
        try:
            module = self.repository.get_by_id(module_id)
            if not module:
                raise ModuleNotFoundError(f"Module with ID {module_id} not found.")
            return self.schema.dump(module)
        except (ModuleNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting module by ID {module_id}: {e}")

    def create_module(self, module_data):
        """Validates and creates a new Module record."""
        try:
            validated_data = self.input_schema.load(module_data)

            if self.repository.get_by_name(validated_data['name']):
                raise ValidationError(f"Module with name '{validated_data['name']}' already exists.")
            if self.repository.get_by_code(validated_data['code']):
                raise ValidationError(f"Module with code '{validated_data['code']}' already exists.")

            module = Module(**validated_data)
            self.repository.add(module)
            self.repository.save_changes()
            return self.schema.dump(module)
        except (ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while creating module: {e}")

    def update_module(self, module_id, update_data):
        """Updates an existing Module record."""
        try:
            module = self.repository.get_by_id(module_id)
            if not module:
                raise ModuleNotFoundError(f"Module with ID {module_id} not found.")

            validated_data = self.input_schema.load(update_data, partial=True)

            if 'name' in validated_data and validated_data['name'] != module.name:
                existing_module = self.repository.get_by_name(validated_data['name'])
                if existing_module and existing_module.module_id != module_id:
                    raise ValidationError(f"Module with name '{validated_data['name']}' already exists.")
            if 'code' in validated_data and validated_data['code'] != module.code:
                existing_module = self.repository.get_by_code(validated_data['code'])
                if existing_module and existing_module.module_id != module_id:
                    raise ValidationError(f"Module with code '{validated_data['code']}' already exists.")

            for key, value in validated_data.items():
                setattr(module, key, value)

            self.repository.save_changes()
            return self.schema.dump(module)
        except (ModuleNotFoundError, ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while updating module ID {module_id}: {e}")

    def delete_module(self, module_id):
        """Deletes a Module record."""
        try:
            module = self.repository.get_by_id(module_id)
            if not module:
                raise ModuleNotFoundError(f"Module with ID {module_id} not found.")

            self.repository.delete(module)
            self.repository.save_changes()
            return {"message": f"Module '{module.name}' deleted successfully."}
        except (ModuleNotFoundError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while deleting module ID {module_id}: {e}")

module_service = ModuleService()
