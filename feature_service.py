
from repositories.feature_repository import feature_repository
from schemas.feature_schemas import FeatureBaseSchema, FeatureInputSchema
from errors import FeatureNotFoundError, DatabaseOperationError, ValidationError
from models import Feature 

class FeatureService:
    def __init__(self, repository=feature_repository, schema=FeatureBaseSchema(), input_schema=FeatureInputSchema()):
        self.repository = repository
        self.schema = schema
        self.input_schema = input_schema

    def get_all_features(self):
        """Retrieves and serializes all Feature records."""
        try:
            features = self.repository.get_all()
            return self.schema.dump(features, many=True)
        except DatabaseOperationError as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting all features: {e}")

    def get_feature_by_id(self, feature_id):
        """Retrieves and serializes a single Feature record by ID."""
        try:
            feature = self.repository.get_by_id(feature_id)
            if not feature:
                raise FeatureNotFoundError(f"Feature with ID {feature_id} not found.")
            return self.schema.dump(feature)
        except (FeatureNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting feature by ID {feature_id}: {e}")

    def get_feature_by_name(self, name):
        """Retrieves and serializes a single Feature record by name."""
        try:
            feature = self.repository.get_by_name(name)
            if not feature:
                raise FeatureNotFoundError(f"Feature with name '{name}' not found.")
            return self.schema.dump(feature)
        except (FeatureNotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting feature by name '{name}': {e}")

    def create_feature(self, feature_data):
        """Validates and creates a new Feature record."""
        try:
            validated_data = self.input_schema.load(feature_data)

            
            if self.repository.get_by_name(validated_data['name']):
                raise ValidationError(f"Feature with name '{validated_data['name']}' already exists.")

            feature = Feature(**validated_data)
            self.repository.add(feature)
            self.repository.save_changes()
            return self.schema.dump(feature)
        except (ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while creating feature: {e}")

    def update_feature(self, feature_id, update_data):
        """Updates an existing Feature record."""
        try:
            feature = self.repository.get_by_id(feature_id)
            if not feature:
                raise FeatureNotFoundError(f"Feature with ID {feature_id} not found.")

            validated_data = self.input_schema.load(update_data, partial=True)

            
            if 'name' in validated_data and validated_data['name'] != feature.name:
                existing_feature = self.repository.get_by_name(validated_data['name'])
                if existing_feature and existing_feature.feature_id != feature_id:
                    raise ValidationError(f"Feature with name '{validated_data['name']}' already exists.")

            for key, value in validated_data.items():
                setattr(feature, key, value)

            self.repository.save_changes()
            return self.schema.dump(feature)
        except (FeatureNotFoundError, ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while updating feature ID {feature_id}: {e}")

    def delete_feature(self, feature_id):
        """Deletes a Feature record."""
        try:
            feature = self.repository.get_by_id(feature_id)
            if not feature:
                raise FeatureNotFoundError(f"Feature with ID {feature_id} not found.")

            self.repository.delete(feature)
            self.repository.save_changes()
            return {"message": f"Feature '{feature.name}' deleted successfully."}
        except (FeatureNotFoundError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while deleting feature ID {feature_id}: {e}")

feature_service = FeatureService()
