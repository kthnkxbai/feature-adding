from marshmallow import Schema, fields, validate
from .tenant_schemas import TenantOutputSchema 
from .feature_schemas import FeatureOutputSchema 
import json

class JSONField(fields.Field):
    """
    A custom Marshmallow field to handle JSON string serialization/deserialization.
    It loads from a JSON string to a Python dict and dumps from a Python dict to a JSON string.
    """
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value 
        return value 
    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value 

class TenantFeatureBaseSchema(Schema):
    """Base schema for TenantFeature, defines common fields."""
    tenant_id = fields.Integer(required=True)
    feature_id = fields.Integer(required=True)
    is_enabled = fields.Boolean(load_default=True)
    config_json = JSONField(allow_none=True)

class TenantFeatureInputSchema(TenantFeatureBaseSchema):
    """Schema for validating input when creating/updating TenantFeature."""
    class Meta:
        pass

class TenantFeatureOutputSchema(TenantFeatureBaseSchema):
    """Schema for serializing TenantFeature for output, with nested details."""
    tenant_feature_id = fields.Integer(dump_only=True)
    tenant = fields.Nested(TenantOutputSchema, dump_only=True)
    feature = fields.Nested(FeatureOutputSchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

