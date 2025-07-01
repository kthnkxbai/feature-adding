from flask import Blueprint, jsonify, current_app

from services.branch_service import branch_service
from services.branch_product_module_services import branch_product_module_service
from schemas.message_schemas import MessageSchema
from schemas.branch_product_module_schemas import ConfiguredBranchProductModuleOutputSchema 

from errors import NotFoundError, ApplicationError

branch_api_bp = Blueprint('api_branch', __name__, url_prefix='/branches')

message_schema = MessageSchema()
configured_modules_schema = ConfiguredBranchProductModuleOutputSchema(many=True) 

@branch_api_bp.route('/<int:branch_id>/delete', methods=["DELETE"])
def delete_branch(branch_id):
    """
    API route to delete a branch by ID.
    """
    try:
        result = branch_service.delete_branch(branch_id)
        return jsonify(message_schema.dump({"status": "success", "message": result['message'], "code": 204})), 204
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error deleting branch: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error deleting branch ID {branch_id}: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500

@branch_api_bp.route('/<int:branch_id>/products/<int:product_id>/configured-modules', methods=['GET'])
def get_branch_product_configured_modules(branch_id, product_id):
    """
    API route to get configured modules for a specific branch and product.
    """
    try:
        configured_modules = branch_product_module_service.get_configured_modules_for_branch_product(
            branch_id,
            product_id,
            current_app.config['MODULE_ID_SEQUENCES'] 
        )
        return jsonify(configured_modules), 200
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error getting configured modules for branch {branch_id}, product {product_id}: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error getting branch product configured modules: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500