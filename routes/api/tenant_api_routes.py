from flask import Blueprint, jsonify, request, current_app

from services.tenant_service import tenant_service
from services.branch_service import branch_service
from schemas.message_schemas import MessageSchema
from schemas.tenant_schemas import TenantBaseSchema,TenantOutputSchema, TenantMinimalOutputSchema
from schemas.branch_schemas import BranchBaseSchema 

from errors import NotFoundError, ApplicationError, ValidationError, DatabaseOperationError

tenant_api_bp = Blueprint('api_tenant', __name__, url_prefix='/tenants')

message_schema = MessageSchema()
tenant_schema = TenantBaseSchema()
tenant_output_schema = TenantOutputSchema()
tenant_minimal_output_schema = TenantMinimalOutputSchema(many=True)
branches_schema = BranchBaseSchema(many=True) 

@tenant_api_bp.route('/', methods=['GET'])
def get_all_tenants_api():
    """
    API route to retrieve all tenants (minimal info for dropdowns).
    ---
    responses:
      200:
        description: A list of minimal tenant data.
        schema:
          type: array
          items:
            $ref: '#/definitions/TenantMinimalOutputSchema'
    """
    try:
        tenants = tenant_service.get_all_tenants(minimal=True)
        return jsonify(tenants), 200
    except (DatabaseOperationError, ApplicationError) as e:
        current_app.logger.error(f"Error getting all tenants via API: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error getting all tenants via API: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500




@tenant_api_bp.route('/<int:tenant_id>/<organization_code>/<sub_domain>', methods=['GET'])
def get_tenant(tenant_id, organization_code, sub_domain):
    """
    API route to retrieve a single tenant by its composite primary key.
    """
    try:
        tenant = tenant_service.get_tenant_by_composite_pk(tenant_id, organization_code, sub_domain)
        print(f"DEBUG: API /tenants GET - Tenant data before jsonify: {tenant}")
        return jsonify(tenant), 200
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error getting tenant: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error getting tenant by composite PK: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500


@tenant_api_bp.route('/<int:tenant_id>/branches', methods=['GET'])
def get_branches_by_tenant(tenant_id):
    """
    API route to retrieve all branches for a specific tenant.
    """
    try:
        branches = branch_service.get_branches_by_tenant(tenant_id)
        print(f"DEBUG: API /tenants/{tenant_id}/branches GET - Branches data before jsonify: {branches}")
        return jsonify(branches), 200
    except NotFoundError as e: 
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error getting branches for tenant {tenant_id}: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error getting branches by tenant {tenant_id}: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500

@tenant_api_bp.route("/<int:tenant_id>/<organization_code>/<sub_domain>", methods=["DELETE"])
def delete_tenant(tenant_id, organization_code, sub_domain):
    """
    API route to delete a tenant by its composite primary key.
    """
    try:
        result = tenant_service.delete_tenant(tenant_id, organization_code, sub_domain)
        return jsonify(message_schema.dump({"status": "success", "message": result['message'], "code": 204})), 204
    except NotFoundError as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except ApplicationError as e:
        current_app.logger.error(f"Error deleting tenant: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error deleting tenant by composite PK: {str(e)}")
        return jsonify(message_schema.dump({"status": "error", "message": "Internal server error", "details": str(e), "code": 500})), 500