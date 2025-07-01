from flask import Blueprint, jsonify, current_app, request
from services.product_services import product_service
from services.branch_product_module_services import branch_product_module_service

from schemas.message_schemas    import MessageSchema
from schemas.product_schemas    import (
    ProductMinimalOutputSchema,
    ProductOutputSchema,         
)

from errors import NotFoundError, ApplicationError


product_api_bp = Blueprint(
    "api_product",
    __name__,
    url_prefix="/api/products"   
)


message_schema           = MessageSchema()
product_minimal_schema   = ProductMinimalOutputSchema(many=True)


@product_api_bp.route("", methods=["GET"])
def get_all_products():
    """
    Return **all** products in *minimal* form (id, name, code).
    GET /api/products
    """
    try:
        products = product_service.get_all_products(minimal=True)

        payload  = product_minimal_schema.dump(products)

        return jsonify(payload), 200

    except ApplicationError as e:
        current_app.logger.error(
            f"[products] ApplicationError: {e.message}", exc_info=True
        )
        return (
            jsonify(message_schema.dump(
                {"status": "error", "message": e.message, "code": e.status_code}
            )),
            e.status_code,
        )
    except Exception as e:
        current_app.logger.exception("[products] Unexpected server error")
        return (
            jsonify(message_schema.dump(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "details": str(e),
                    "code": 500,
                }
            )),
            500,
        )


@product_api_bp.route("/<int:product_id>/delete", methods=["DELETE"])
def delete_product(product_id):
    """
    Delete a single product by ID.
    DELETE /api/products/<product_id>/delete
    """
    try:
        result = product_service.delete_product(product_id)
        return (
            jsonify(
                message_schema.dump(
                    {
                        "status":  "success",
                        "message": result["message"],
                        "code":    204,
                    }
                )
            ),
            204,
        )

    except NotFoundError as e:
        return (
            jsonify(
                message_schema.dump(
                    {"status": "error", "message": e.message, "code": e.status_code}
                )
            ),
            e.status_code,
        )
    except ApplicationError as e:
        current_app.logger.error(
            f"[delete_product] ApplicationError: {e.message}", exc_info=True
        )
        return (
            jsonify(
                message_schema.dump(
                    {"status": "error", "message": e.message, "code": e.status_code}
                )
            ),
            e.status_code,
        )
    except Exception as e:
        current_app.logger.exception(
            f"[delete_product] Unexpected error while deleting product {product_id}"
        )
        return (
            jsonify(
                message_schema.dump(
                    {
                        "status": "error",
                        "message": "Internal server error",
                        "details": str(e),
                        "code": 500,
                    }
                )
            ),
            500,
        )

# In products_api_bp
@product_api_bp.route('/<int:product_id>/modules', methods=['GET'])
def get_modules_for_product(product_id):
    """
    API route to get modules available for a product, with their configured status for a given branch.
    """
    try:
        branch_id = request.args.get('branch_id', type=int)
        modules = branch_product_module_service.get_available_modules_for_product_with_status(
            product_id,
            branch_id,
            current_app.config.get('MODULE_ID_SEQUENCES', {})
        )
        return jsonify(modules), 200
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error in /api/products/{product_id}/modules: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error: {e}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal Server Error", "details": str(e), "code": 500})), 500
