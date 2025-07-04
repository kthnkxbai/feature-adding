from marshmallow import Schema, fields, validate

class TenantBaseSchema(Schema):
    organization_code = fields.String(required=True, validate=validate.Length(min=1, max=50))
    tenant_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    sub_domain = fields.String(required=True, validate=validate.Length(min=1, max=100))
    default_currency = fields.String(required=True, validate=validate.Length(min=1, max=20))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    status = fields.String(required=True, validate=validate.OneOf(["Active", "Inactive", "Suspended"]))
    country_id = fields.Integer(required=True)

class TenantInputSchema(TenantBaseSchema):
    """Schema for validating input when creating/updating Tenant."""
    pass

class TenantOutputSchema(TenantBaseSchema):
    """Schema for serializing Tenant for output, with dump_only fields."""
    tenant_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # country = fields.Nested(CountryOutputSchema, dump_only=True, description="Detailed information about the associated country.") # Uncomment if you want nested Country details

class TenantMinimalOutputSchema(Schema):
    tenant_id = fields.Integer(required=True)
    tenant_name = fields.String(required=True)
