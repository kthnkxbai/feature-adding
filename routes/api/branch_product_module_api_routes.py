# routes/api/branch_product_module_api_routes.py
from flask import Blueprint, request, jsonify, current_app

# Import services and schemas
from services.product_module_services import product_module_service
from services.branch_product_module_services import branch_product_module_service
from schemas.message_schemas import MessageSchema
from schemas.branch_product_module_schemas import AvailableProductModuleOutputSchema

# Import custom errors
from errors import NotFoundError, ApplicationError, DatabaseOperationError, ProductNotFoundError, BranchNotFoundError, ProductModuleNotFoundError

branch_product_module_api_bp = Blueprint('api_branch_product_module', __name__, url_prefix='/branch-product-modules')

message_schema = MessageSchema()
available_product_modules_schema = AvailableProductModuleOutputSchema(many=True)

@branch_product_module_api_bp.route('/product/<int:product_id>/modules', methods=['GET'])
def get_available_product_modules_for_product(product_id):
    """
    API route to get modules available for a product, with their configured status for a given branch.
    ---
    parameters:
      - in: query
        name: branch_id
        type: integer
        required: true
        description: The ID of the branch.
      - in: path
        name: product_id
        type: integer
        required: true
        description: The ID of the product.
    responses:
      200:
        description: A list of modules with their configuration status for the branch.
        schema:
          type: array
          items:
            $ref: '#/definitions/AvailableProductModuleOutputSchema'
    """
    try:
        branch_id = request.args.get('branch_id', type=int)
        if branch_id is None:
            return jsonify(message_schema.dump({"status": "error", "message": "Branch ID is required as a query parameter.", "code": 400})), 400

        modules = branch_product_module_service.get_available_modules_for_product_with_status(
            product_id,
            branch_id,
            current_app.config['MODULE_ID_SEQUENCES']
        )
        return jsonify(modules), 200
    except (ProductNotFoundError, BranchNotFoundError, NotFoundError) as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except (DatabaseOperationError, ApplicationError) as e:
        current_app.logger.error(f"Error in /api/products/{product_id}/modules: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in get_available_modules_for_product_with_status: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500

@branch_product_module_api_bp.route('/branches/<int:branch_id>/products/<int:product_id>/modules/<int:module_id>', methods=['DELETE'])
def api_delete_branch_product_module(branch_id, product_id, module_id):
    """
    API endpoint to delete a specific BranchProductModule entry (unconfigure a module).
    ---
    parameters:
      - in: path
        name: branch_id
        type: integer
        required: true
        description: The ID of the branch.
      - in: path
        name: product_id
        type: integer
        required: true
        description: The ID of the product.
      - in: path
        name: module_id
        type: integer
        required: true
        description: The ID of the module to unconfigure.
    responses:
      200:
        description: Module successfully unconfigured.
        schema:
          $ref: '#/definitions/MessageSchema'
      404:
        description: Product-Module combination or BPM not found.
        schema:
          $ref: '#/definitions/MessageSchema'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/MessageSchema'
    """
    try:
        # The service method will handle finding the product_module_id and then deleting the BPM
        result = branch_product_module_service.delete_branch_product_module_by_composite_keys(
            branch_id,
            product_id,
            module_id
        )
        return jsonify(message_schema.dump(result)), 200
    except (ProductModuleNotFoundError, BranchNotFoundError, ProductNotFoundError, NotFoundError) as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except (DatabaseOperationError, ApplicationError) as e:
        current_app.logger.error(f"Error deleting BranchProductModule: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error deleting BranchProductModule: {str(e)}")
        return jsonify({'status': 'error', 'message': f"An error occurred during module unconfiguration: {str(e)}", 'details': str(e)}), 500