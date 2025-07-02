from flask import Blueprint, request, jsonify, current_app

from services.tenant_feature_service import tenant_feature_service
from schemas.message_schemas import MessageSchema
from schemas.tenant_feature_schemas import FeatureStatusOutputSchema 
from schemas.tenant_feature_schemas import TenantFeatureInputSchema 

from errors import NotFoundError, ApplicationError, TenantNotFoundError, FeatureNotFoundError, ValidationError, DatabaseOperationError

tenant_feature_api_bp = Blueprint('api_tenant_feature', __name__, url_prefix='/tenant-features')

message_schema = MessageSchema()
feature_status_output_schema = FeatureStatusOutputSchema(many=True) 

@tenant_feature_api_bp.route('/<int:tenant_id>', methods=['GET'])
def get_tenant_features_api(tenant_id):
    """
    API endpoint to get all master features and their enabled/disabled status for a specific tenant.
    ---
    parameters:
      - in: path
        name: tenant_id
        type: integer
        required: true
        description: The ID of the tenant.
    responses:
      200:
        description: A dictionary containing lists of enabled and disabled features.
        schema:
          type: object
          properties:
            enabled_features:
              type: array
              items:
                $ref: '#/definitions/FeatureStatusOutputSchema'
            disabled_features:
              type: array
              items:
                $ref: '#/definitions/FeatureStatusOutputSchema'
      404:
        description: Tenant not found.
        schema:
          $ref: '#/definitions/MessageSchema'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/MessageSchema'
    """
    try:
        features_data = tenant_feature_service.get_features_for_tenant_with_status(tenant_id)
        return jsonify(features_data), 200
    except (TenantNotFoundError, NotFoundError) as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except (DatabaseOperationError, ApplicationError) as e:
        current_app.logger.error(f"Error getting tenant features for tenant {tenant_id}: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in get_tenant_features_api for tenant {tenant_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An internal server error occurred', 'details': str(e)}), 500

@tenant_feature_api_bp.route('/configure', methods=['POST'])
def configure_tenant_features_api():
    """
    API endpoint to configure (enable/disable) multiple features for a tenant.
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - tenant_id
          properties:
            tenant_id:
              type: integer
              description: The ID of the tenant.
            enabled_feature_ids:
              type: array
              items:
                type: integer
              description: List of feature IDs to be enabled.
            disabled_feature_ids:
              type: array
              items:
                type: integer
              description: List of feature IDs to be disabled.
    responses:
      200:
        description: Feature configurations updated successfully or no changes made.
        schema:
          $ref: '#/definitions/MessageSchema'
      400:
        description: Invalid request data.
        schema:
          $ref: '#/definitions/MessageSchema'
      404:
        description: Tenant or Feature not found.
        schema:
          $ref: '#/definitions/MessageSchema'
      500:
        description: Internal server error.
        schema:
          $ref: '#/definitions/MessageSchema'
    """
    data = request.get_json()

    if not data:
        return jsonify(message_schema.dump({'status': 'error', 'message': 'Request body must be JSON and not empty', 'code': 400})), 400

    selected_tenant_id = data.get('tenant_id')
    enabled_feature_ids = data.get('enabled_feature_ids', [])
    disabled_feature_ids = data.get('disabled_feature_ids', [])

    # Basic type validation (more detailed validation in service/schema)
    if not isinstance(selected_tenant_id, int):
        return jsonify(message_schema.dump({'status': 'error', 'message': 'tenant_id must be an integer', 'code': 400})), 400
    if not isinstance(enabled_feature_ids, list):
        return jsonify(message_schema.dump({'status': 'error', 'message': 'enabled_feature_ids must be a list', 'code': 400})), 400
    if not isinstance(disabled_feature_ids, list):
        return jsonify(message_schema.dump({'status': 'error', 'message': 'disabled_feature_ids must be a list', 'code': 400})), 400

    try:
        # Convert list elements to int, filtering out non-integers if any
        enabled_feature_ids = [int(fid) for fid in enabled_feature_ids if isinstance(fid, int) or (isinstance(fid, str) and fid.isdigit())]
        disabled_feature_ids = [int(fid) for fid in disabled_feature_ids if isinstance(fid, int) or (isinstance(fid, str) and fid.isdigit())]
    except ValueError:
        return jsonify(message_schema.dump({'status': 'error', 'message': 'Feature ID lists must contain only integers or string representations of integers', 'code': 400})), 400

    try:
        result = tenant_feature_service.update_tenant_feature_configuration(
            selected_tenant_id,
            enabled_feature_ids,
            disabled_feature_ids
        )
        return jsonify(message_schema.dump(result)), 200
    except (TenantNotFoundError, FeatureNotFoundError, NotFoundError) as e:
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except (ValidationError, DatabaseOperationError, ApplicationError) as e:
        current_app.logger.error(f"Error configuring tenant features: {e.message}", exc_info=True)
        return jsonify(message_schema.dump({"status": "error", "message": e.message, "code": e.status_code})), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error configuring tenant features: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An internal server error occurred', 'details': str(e)}), 500