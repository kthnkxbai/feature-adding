from marshmallow import Schema, fields, validate

class BranchBaseSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True, validate=validate.Length(max=500))
    status = fields.String(required=True, validate=validate.Length(min=1, max=50))
    code = fields.String(required=True, validate=validate.Length(min=1, max=50))
    country_id = fields.Integer(required=True)
    tenant_id = fields.Integer(required=True)

class BranchInputSchema(BranchBaseSchema):
    pass

class BranchOutputSchema(BranchBaseSchema):
    branch_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
