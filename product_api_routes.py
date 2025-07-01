from flask import Blueprint, request, jsonify, current_app

from services.product_module_services import product_module_service 
from services.branch_product_module_services import branch_product_module_service 
from schemas.message_schemas import MessageSchema
from schemas.product_module_schemas import AvailableProductModuleOutputSchema 
from errors import NotFoundError, ApplicationError

product_module_api_bp = Blueprint('api_product_module', __name__, url_prefix='/product-modules')

message_schema = MessageSchema()
available_product_modules_schema = AvailableProductModuleOutputSchema(many=True)

@product_module_api_bp.route('/product/<int:product_id>/modules', methods=['GET'])
def get_available_product_modules_for_product(product_id):
    """
    API route to get modules available for a product, with their configured status for a given branch.
    """
    try:
        branch_id = request.args.get('branch_id', type=int)
        
        modules = branch_product_module_service.get_available_modules_for_product_with_status(
            product_id,
            branch_id,
            current_app.config['MODULE_ID_SEQUENCES'] 
        )
       
        return jsonify(modules), 200
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error in /api/products/{product_id}/modules: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in get_available_product_modules_for_product: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500