import datetime
import logging

from repositories.feature_repository import feature_repository
from schemas.feature_schemas import FeatureInputSchema, FeatureOutputSchema
from errors import ApplicationError, DatabaseOperationError, FeatureNotFoundError, ValidationError, DuplicateError

log = logging.getLogger(__name__)

class FeatureService:
    def __init__(self):
        self.repository = feature_repository
        self.input_schema = FeatureInputSchema()
        self.output_schema = FeatureOutputSchema(many=True) 

    def get_all_features(self):
        """
        Retrieves all feature records.
        """
        try:
            features = self.repository.get_all()
            return self.output_schema.dump(features)
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_all_features: {e}")
            raise ApplicationError("Failed to retrieve all features.", status_code=500)

    def get_feature_by_id(self, feature_id):
        """
        Retrieves a single feature record by its ID.
        """
        try:
            feature = self.repository.get_by_id(feature_id)
            return FeatureOutputSchema().dump(feature) 
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in get_feature_by_id({feature_id}): {e}")
            raise ApplicationError("Failed to retrieve feature by ID.", status_code=500)

    def create_feature(self, data):
        """
        Creates a new feature record.
        """
        try:
            validated_data = self.input_schema.load(data)
            feature_code = validated_data['code']

            existing_feature = self.repository.get_by_code(feature_code)
            if existing_feature:
                raise DuplicateError(f"Feature with code '{feature_code}' already exists.")

            new_feature_obj = self.repository.create(
                name=validated_data['name'],
                code=feature_code,
                description=validated_data.get('description'),
                is_active=validated_data.get('is_active', True),
                created_at=datetime.datetime.utcnow()
            )
            return FeatureOutputSchema().dump(new_feature_obj)
        except ValidationError:
            raise
        except DuplicateError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in create_feature with data {data}: {e}")
            raise ApplicationError("Failed to create feature due to an internal error.", status_code=500)

    def update_feature(self, feature_id, data):
        """
        Updates an existing feature record.
        """
        try:
            validated_data = self.input_schema.load(data, partial=True)
            feature_obj = self.repository.get_by_id(feature_id)

            if 'code' in validated_data and validated_data['code'] != feature_obj.code:
                existing_feature = self.repository.get_by_code(validated_data['code'])
                if existing_feature and existing_feature.feature_id != feature_id:
                    raise DuplicateError(f"Feature with code '{validated_data['code']}' already exists.")

            updated_feature_obj = self.repository.update(feature_obj, **validated_data)
            return FeatureOutputSchema().dump(updated_feature_obj)
        except ValidationError:
            raise
        except FeatureNotFoundError:
            raise
        except DuplicateError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in update_feature({feature_id}) with data {data}: {e}")
            raise ApplicationError("Failed to update feature due to an internal error.", status_code=500)

    def delete_feature(self, feature_id):
        """
        Deletes a feature record.
        """
        try:
            feature_obj = self.repository.get_by_id(feature_id)
            self.repository.delete(feature_obj)
            return {"message": f"Feature with ID {feature_id} deleted successfully."}
        except FeatureNotFoundError:
            raise
        except DatabaseOperationError:
            raise
        except ApplicationError:
            raise
        except Exception as e:
            log.exception(f"Unexpected error in delete_feature({feature_id}): {e}")
            raise ApplicationError("Failed to delete feature due to an internal error.", status_code=500)

feature_service = FeatureService()