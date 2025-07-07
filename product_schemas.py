from marshmallow import Schema, fields, validate

class ProductBaseSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    code = fields.String(required=True, validate=validate.Length(min=1, max=50))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    tag = fields.String(allow_none=True, validate=validate.Length(max=100))
    sequence = fields.Integer(allow_none=True)
    parent_product_id = fields.Integer(allow_none=True)
    is_inbound = fields.Boolean(load_default=False)
    product_tag_id = fields.Integer(allow_none=True)
    supported_file_formats = fields.String(allow_none=True, validate=validate.Length(max=255))

class ProductInputSchema(ProductBaseSchema):
    pass 

class ProductOutputSchema(ProductBaseSchema):
    product_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductMinimalOutputSchema(Schema):
    """Schema for returning minimal product information (ID and Name)."""
    product_id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    code = fields.String(dump_only=True) 
