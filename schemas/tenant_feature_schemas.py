# schemas/tenant_feature_schemas.py
from marshmallow import Schema, fields, validate

class TenantFeatureInputSchema(Schema):
    tenant_id = fields.Integer(required=True)
    feature_id = fields.Integer(required=True)
    is_enabled = fields.Boolean(required=True)
    config_json = fields.String(allow_none=True) # Store as string, handle JSON parsing in service

class TenantFeatureOutputSchema(TenantFeatureInputSchema):
    tf_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class FeatureStatusOutputSchema(Schema):
    """Schema for outputting feature status (enabled/disabled) for a tenant."""
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    is_enabled = fields.Boolean(required=True) # Indicates if it's enabled for the tenant