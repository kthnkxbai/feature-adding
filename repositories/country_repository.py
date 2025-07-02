
from extensions import db
from models import Country
from errors import DatabaseOperationError, NotFoundError

class CountryRepository:
    def get_all(self):
        """Retrieves all Country records."""
        try:
            return Country.query.all()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve all countries: {e}") from e

    def get_by_id(self, country_id):
        """Retrieves a Country record by its primary key."""
        try:
            return db.session.get(Country, country_id)  
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve country with ID {country_id}: {e}") from e

    def get_by_code(self, country_code):
        """Retrieves a Country record by its country code."""
        try:
            return Country.query.filter_by(country_code=country_code).first()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to retrieve country with code {country_code}: {e}") from e

    def add(self, country):
        """Adds a new Country record to the session."""
        try:
            db.session.add(country)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to add country '{country.country_name}': {e}") from e

    def delete(self, country):
        """Deletes a Country record from the session."""
        try:
            db.session.delete(country)
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete country '{country.country_name}': {e}") from e

    def save_changes(self):
        """Commits changes to the database."""
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise DatabaseOperationError(f"Failed to commit country changes: {e}") from e

    def rollback_changes(self):
        """Rolls back changes in the database session."""
        db.session.rollback()

country_repository = CountryRepository()
