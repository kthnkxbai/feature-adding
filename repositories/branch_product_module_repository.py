from .base_repository import BaseRepository
from models import BranchProductModule, ProductModule 
from extensions import db 
from errors import NotFoundError, ApplicationError
from sqlalchemy.orm import joinedload
import logging

log = logging.getLogger(__name__)

class BranchProductModuleRepository(BaseRepository):
    def __init__(self):
        super().__init__(BranchProductModule)

    def get_by_branch_and_product_module(self, branch_id, product_module_id):
        """
        Retrieves a BranchProductModule record by branch_id and product_module_id.
        """
        try:
            bpm = self.model.query.filter_by(
                branch_id=branch_id,
                product_module_id=product_module_id
            ).first()
            return bpm
        except Exception as e:
            log.exception(f"Database error fetching BranchProductModule by branch_id={branch_id}, product_module_id={product_module_id}: {e}")
            raise ApplicationError("Could not retrieve BranchProductModule.", status_code=500)

    def get_configured_modules_for_branch_product(self, branch_id, product_id):
        """
        Retrieves BranchProductModule records configured for a specific branch and product.
        Includes joined ProductModule and Module details.
        """
        try:
            configured_modules = self.model.query.options(
                joinedload(BranchProductModule.product_module).joinedload(ProductModule.module)
            ).filter(
                BranchProductModule.branch_id == branch_id,
                BranchProductModule.product_module.has(product_id=product_id)
            ).join(ProductModule).all()
            return configured_modules
        except Exception as e:
            log.exception(f"Database error fetching configured modules for branch {branch_id}, product {product_id}: {e}")
            raise ApplicationError("Could not retrieve configured modules.", status_code=500)

    def get_all_for_branch_product_module_ids(self, branch_id, product_module_ids: list):
        """
        Retrieves BranchProductModule records for a specific branch and a list of product module IDs.
        """
        if not product_module_ids:
            return []
        try:
            return self.model.query.filter(
                BranchProductModule.branch_id == branch_id,
                BranchProductModule.product_module_id.in_(product_module_ids)
            ).all()
        except Exception as e:
            log.exception(f"Database error fetching BPMs for branch {branch_id} and product_module_ids {product_module_ids}: {e}")
            raise ApplicationError("Could not retrieve BPMs by multiple IDs.", status_code=500)

branch_product_module_repository = BranchProductModuleRepository()
