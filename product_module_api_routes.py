from flask import Blueprint, jsonify, current_app

from services.product_services import product_service
from schemas.message_schemas import MessageSchema
from schemas.product_schemas import ProductMinimalOutputSchema

from errors import NotFoundError, ApplicationError

product_api_bp = Blueprint('api_product', __name__, url_prefix='/products')

message_schema = MessageSchema()
product_minimal_schema = ProductMinimalOutputSchema(many=True) 
@product_api_bp.route('', methods=['GET'])
def get_all_products():
    """
    API route to get all products (minimal info: id, name).
    """
    try:
        products = product_service.get_all_products(minimal=True)
        return jsonify(products), 200
    except ApplicationError as e:
        current_app.logger.error(f"Error getting all products: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error getting all products: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500

@product_api_bp.route("/<int:product_id>/delete", methods=["DELETE"])
def delete_product(product_id):
    """
    API route to delete a product by ID.
    """
    try:
        result = product_service.delete_product(product_id)
        return jsonify(message_schema.dump({"status": "success", "message": result['message'], "code": 204})), 204
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error deleting product: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error deleting product ID {product_id}: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500