from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT, JSON

import sqlalchemy as sa
import datetime
import json

from extensions import db 

class Country(db.Model):
    __tablename__ = 'countries'

    country_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_code = db.Column(db.String(6), nullable=False, unique=True)
    country_name = db.Column(db.String(255), nullable=False)
    status = db.Column(Enum('Active', 'Inactive'), nullable=False)

   
    tenants = relationship("Tenant", back_populates="country", cascade="all, delete", passive_deletes=True)
    branches = relationship("Branch", back_populates="country", cascade="all, delete", passive_deletes=True)


class Tenant(db.Model):
    __tablename__ = 'tenant'
    __table_args__ = (
        db.PrimaryKeyConstraint('tenant_id', 'organization_code', 'sub_domain'),
    )

    tenant_id = db.Column(db.BigInteger, autoincrement=True, nullable=False)
    organization_code = db.Column(db.String(50), nullable=False,unique=True)
    tenant_name = db.Column(db.String(100))
    sub_domain = db.Column(db.String(50), nullable=False,unique=True)
    default_currency = db.Column(db.String(3), nullable=False, default='USD')
    description = db.Column(db.String(500))
    status = db.Column(Enum('Active', 'Inactive'), default='Active')

    country_id = db.Column(
        db.Integer,
        db.ForeignKey('countries.country_id', ondelete='CASCADE'),
        nullable=True
    )

   
    country = relationship("Country", back_populates="tenants")
    
    branches = relationship(
        "Branch",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class Branch(db.Model):
    __tablename__ = 'branch'

    branch_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    tenant_id = db.Column(
        db.BigInteger,
        db.ForeignKey('tenant.tenant_id', ondelete='CASCADE'),
        nullable=True
    )

    name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    
    status = db.Column(Enum('Active', 'Inactive'), default='Active')
    code = db.Column(db.String(50), nullable=True)

    country_id = db.Column(
        db.Integer,
        db.ForeignKey('countries.country_id', ondelete='CASCADE'),
        nullable=True
    )
   
    tenant = relationship(
        "Tenant",
        back_populates="branches",
        passive_deletes=True
    )
    country = relationship(
        "Country",
        back_populates="branches",
        passive_deletes=True
    )
    
class Module(db.Model):
    __tablename__ = 'module'

    module_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    created_by = db.Column(db.String(50), nullable=True)
    code = db.Column(db.String(50), nullable=True)

    dependent_modules = db.Column(db.JSON, nullable=True)

    __table_args__ = (
        CheckConstraint("JSON_VALID(dependent_modules)", name="ck_json_valid_dependent_modules"),
    )
    
    product_modules = db.relationship('ProductModule', back_populates='module', cascade='all, delete-orphan')
    
class Feature(db.Model):
    __tablename__ = 'feature'

    feature_id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=True)
    description = db.Column(db.String(500), nullable=True)

    module_id = db.Column(
        db.BigInteger,
        db.ForeignKey('module.module_id', ondelete='CASCADE'),
        nullable=True
    )

    created_by = db.Column(db.String(50), nullable=True)

    module = db.relationship("Module", backref=db.backref("features", cascade="all, delete-orphan", passive_deletes=True))
    
    
class TenantFeature(db.Model):
    __tablename__ = 'tenant_feature'

    tenant_feature_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    tenant_id = db.Column(
        db.BigInteger,
        db.ForeignKey('tenant.tenant_id', ondelete='CASCADE'),
        nullable=True
    )
    
    feature_id = db.Column(
        db.SmallInteger,
        db.ForeignKey('feature.feature_id', ondelete='CASCADE'),
        nullable=True
    )

    is_enabled = db.Column(db.Boolean, nullable=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modified_on = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow, nullable=True)

    tenant = db.relationship("Tenant", backref=db.backref("tenant_features", cascade="all, delete-orphan", passive_deletes=True))
    feature = db.relationship("Feature", backref=db.backref("tenant_features", cascade="all, delete-orphan", passive_deletes=True))

class ReportMaster(db.Model):
    __tablename__ = 'report_master'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(999), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    category = db.Column(
        Enum('kpi', 'transaction', 'summary', name='report_category'),
        nullable=True
    )
class TenantReport(db.Model):
    __tablename__ = 'tenant_reports'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    report_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey('report_master.id', ondelete='CASCADE'),
        nullable=False
    )

    tenant_id = db.Column(
        db.BigInteger,
        db.ForeignKey('tenant.tenant_id', ondelete='CASCADE'),
        nullable=False
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    select_clause = db.Column(
        sa.Text(collation='utf8mb4_bin'),
        nullable=True
    )

    where_clause = db.Column(
        sa.Text(collation='utf8mb4_bin'),
        nullable=True
    )

    field_metadata = db.Column(
        sa.Text(collation='utf8mb4_bin'),
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint('report_type_id', 'tenant_id', name='uq_report_tenant'),
        CheckConstraint("JSON_VALID(select_clause)", name="ck_json_valid_select_clause"),
        CheckConstraint("JSON_VALID(where_clause)", name="ck_json_valid_where_clause"),
        CheckConstraint("JSON_VALID(field_metadata)", name="ck_json_valid_field_metadata"),
    )

    report = db.relationship("ReportMaster", backref=db.backref("tenant_reports", cascade="all, delete-orphan", passive_deletes=True))
    tenant = db.relationship("Tenant", backref=db.backref("tenant_reports", cascade="all, delete-orphan", passive_deletes=True))

class ProductTag(db.Model):
    __tablename__ = 'product_tag'

    product_tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    sequence = db.Column(db.Integer)

    def __repr__(self):
        return f"<ProductTag(code='{self.code}', name='{self.name}')>"

class Product(db.Model):
    __tablename__ = 'product'

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    code = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(500))
    tag = db.Column(db.String(50))
    
    sequence = db.Column(db.Integer)
    parent_product_id = db.Column(db.Integer, db.ForeignKey('product.product_id', ondelete='SET NULL'), nullable=True)
    is_inbound = db.Column(db.Boolean)
    product_tag_id = db.Column(db.Integer, db.ForeignKey('product_tag.product_tag_id', ondelete='SET NULL'), nullable=True)
    supported_file_formats = db.Column(db.String(250))

    
    parent_product = db.relationship('Product', remote_side=[product_id], backref='child_products', lazy='joined')
    product_tag = db.relationship('ProductTag', backref='products', lazy='joined')
    
    product_modules = db.relationship('ProductModule', back_populates='product', cascade='all, delete-orphan')
    def __repr__(self):
        return f"<Product(code='{self.code}', name='{self.name}')>"
        
class ProductModule(db.Model):
    __tablename__ = 'product_module'

    product_module_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    module_id = db.Column(db.BigInteger, db.ForeignKey('module.module_id', ondelete='CASCADE'), nullable=True)
    code = db.Column(db.String(50), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id', ondelete='CASCADE'), nullable=True)
    sequence = db.Column(db.Integer, nullable=True)

    module = db.relationship('Module', back_populates='product_modules', passive_deletes=True)
    product = db.relationship('Product', back_populates='product_modules', passive_deletes=True)
    
class BranchProductModule(db.Model):
    __tablename__ = 'branch_product_module'

    tenant_product_module = db.Column(db.Integer, primary_key=True, autoincrement=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.branch_id', ondelete='CASCADE'), nullable=True)
    product_module_id = db.Column(db.Integer, db.ForeignKey('product_module.product_module_id', ondelete='CASCADE'), nullable=True)
    created_by = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    eligibility_config = db.Column(LONGTEXT(collation='utf8mb4_bin'), nullable=True)

    __table_args__ = (
        CheckConstraint('JSON_VALID(eligibility_config)', name='check_valid_json_eligibility_config'),
    )

    
    branch = relationship('Branch', backref='branch_product_modules', passive_deletes=True)
    product_module = relationship('ProductModule', backref='branch_product_modules', passive_deletes=True)

    def __repr__(self):
        return f'<BranchProductModule ID={self.tenant_product_module}, Branch={self.branch_id}, ProductModule={self.product_module_id}>'   


