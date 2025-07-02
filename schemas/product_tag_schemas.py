from marshmallow import Schema, fields, validate

class ProductTagBaseSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    is_active = fields.Boolean(load_default=True)

class ProductTagInputSchema(ProductTagBaseSchema):
    pass

class ProductTagOutputSchema(ProductTagBaseSchema):
    product_tag_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
