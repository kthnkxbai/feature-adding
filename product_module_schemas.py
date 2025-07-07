
from marshmallow import Schema, fields, validate
from .product_schemas import ProductOutputSchema, ProductMinimalOutputSchema
from .module_schemas import ModuleOutputSchema

class ProductModuleBaseSchema(Schema):
    """Base schema for ProductModule, defines common fields."""
    product_id = fields.Integer(required=True)
    module_id = fields.Integer(required=True)
    is_active = fields.Boolean(load_default=True)
    notes = fields.String(allow_none=True)

class ProductModuleInputSchema(ProductModuleBaseSchema):
    """Schema for validating input when creating/updating ProductModule."""
    class Meta:
        pass

class ProductModuleOutputSchema(ProductModuleBaseSchema):
    """Schema for serializing ProductModule for output, with nested details."""
    product_module_id = fields.Integer(dump_only=True)
    product = fields.Nested(ProductOutputSchema, dump_only=True)
    module = fields.Nested(ModuleOutputSchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class AvailableProductModuleOutputSchema(Schema):
    """
    Specific schema for the API endpoint that shows available modules for a product,
    including whether they are configured for a given branch.
    """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    is_configured = fields.Boolean(required=True)

class ConfiguredBranchProductModuleOutputSchema(Schema):
    """
    Specific schema for the API endpoint that shows modules configured for a branch and product.
    This mimics the exact output structure requested in the previous app.py.
    """
    branch_id = fields.Integer(required=True)
    product_id = fields.Integer(required=True)
    module_id = fields.Integer(required=True)
    module_name = fields.String(required=True)

