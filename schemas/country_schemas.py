
from marshmallow import Schema, fields, validate

class CountryBaseSchema(Schema):
    country_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    country_code = fields.String(required=True, validate=validate.Length(min=2, max=3))
    is_active = fields.Boolean(load_default=True)

class CountryInputSchema(CountryBaseSchema):
    pass

class CountryOutputSchema(CountryBaseSchema):
    country_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

