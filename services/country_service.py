from models import Country  

from repositories.country_repository import country_repository
from schemas.country_schemas import CountryBaseSchema, CountryInputSchema, CountryOutputSchema
from errors import NotFoundError, DatabaseOperationError, ValidationError

class CountryService:
    def __init__(self, repository=country_repository, schema=CountryBaseSchema(), input_schema=CountryInputSchema()):
        self.repository = repository
        self.schema = schema
        self.input_schema = input_schema
        self.output_schema = CountryOutputSchema(many=True)

    def get_all_countries(self):
        """Retrieves and serializes all Country records."""
        try:
            countries = self.repository.get_all()
            return self.output_schema.dump(countries, many=True)
        except DatabaseOperationError as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting all countries: {e}")

    def get_country_by_id(self, country_id):
        """Retrieves and serializes a single Country record by ID."""
        try:
            country = self.repository.get_by_id(country_id)
            if not country:
                raise NotFoundError(f"Country with ID {country_id} not found.")
            return CountryOutputSchema().dump(country)
        except (NotFoundError, DatabaseOperationError) as e:
            raise e
        except Exception as e:
            raise DatabaseOperationError(f"An unexpected error occurred while getting country by ID {country_id}: {e}")

    def create_country(self, country_data):
        """Validates and creates a new Country record."""
        try:
            
            validated_data = self.input_schema.load(country_data)

           
            existing_country = self.repository.get_by_code(validated_data['country_code'])
            if existing_country:
                raise ValidationError(f"Country with code '{validated_data['country_code']}' already exists.")

            country = Country(**validated_data)
            self.repository.add(country)
            self.repository.save_changes()
            return self.schema.dump(country)
        except ValidationError as e:
            self.repository.rollback_changes()
            raise e
        except DatabaseOperationError as e:
            
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while creating country: {e}")

    def update_country(self, country_id, update_data):
        """Updates an existing Country record."""
        try:
            country = self.repository.get_by_id(country_id)
            if not country:
                raise NotFoundError(f"Country with ID {country_id} not found.")

            validated_data = self.input_schema.load(update_data, partial=True) 

            if 'country_code' in validated_data and validated_data['country_code'] != country.country_code:
                existing_country = self.repository.get_by_code(validated_data['country_code'])
                if existing_country and existing_country.country_id != country_id:
                    raise ValidationError(f"Country with code '{validated_data['country_code']}' already exists.")

            for key, value in validated_data.items():
                setattr(country, key, value)

            self.repository.save_changes()
            return self.schema.dump(country)
        except (NotFoundError, ValidationError, DatabaseOperationError) as e:
            self.repository.rollback_changes() 
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while updating country ID {country_id}: {e}")

    def delete_country(self, country_id):
        """Deletes a Country record."""
        try:
            country = self.repository.get_by_id(country_id)
            if not country:
                raise NotFoundError(f"Country with ID {country_id} not found.")

            self.repository.delete(country)
            self.repository.save_changes()
            return {"message": f"Country '{country.country_name}' deleted successfully."}
        except (NotFoundError, DatabaseOperationError) as e:
            self.repository.rollback_changes()
            raise e
        except Exception as e:
            self.repository.rollback_changes()
            raise DatabaseOperationError(f"An unexpected error occurred while deleting country ID {country_id}: {e}")

country_service = CountryService()
