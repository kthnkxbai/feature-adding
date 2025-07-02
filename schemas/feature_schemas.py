from marshmallow import Schema, fields, validate

class FeatureBaseSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    code = fields.String(required=True, validate=validate.Length(min=1, max=50))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    is_active = fields.Boolean(load_default=True)

class FeatureInputSchema(FeatureBaseSchema):
    """Schema for validating input when creating/updating Feature."""
    pass

class FeatureOutputSchema(FeatureBaseSchema):
    """Schema for serializing Feature for output, with dump_only fields."""
    feature_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

