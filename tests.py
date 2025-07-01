import unittest
from unittest.mock import patch, MagicMock
from app import app, db, Country, Tenant, Branch, Product, TenantReport, ProductModule, Module, BranchProductModule 
import json
import uuid

class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.headers = {'Content-Type': 'application/json'}

        with self.app.app_context():
            db.session.remove()
            db.session.rollback()

            self.test_country_id = int(uuid.uuid4().int % 100000000)
            self.test_tenant_id = int(uuid.uuid4().int % 100000000)
            self.test_branch_id = int(uuid.uuid4().int % 100000000)
            self.test_product_id = int(uuid.uuid4().int % 100000000)
            self.test_module_id_1 = int(uuid.uuid4().int % 100000000)
            self.test_module_id_2 = int(uuid.uuid4().int % 100000000)
            self.test_product_module_id_1 = int(uuid.uuid4().int % 100000000)
            self.test_product_module_id_2 = int(uuid.uuid4().int % 100000000)


            self.test_org_code = f"TESTORG_{uuid.uuid4().hex[:10]}"
            self.test_sub_domain = f"testsub_{uuid.uuid4().hex[:10]}"

            self.test_country = Country(
                country_id=self.test_country_id,
                country_code=f"CC_{self.test_country_id % 1000:03d}",
                country_name=f"TestCountry_{self.test_country_id}",
                status="active"
            )
            db.session.add(self.test_country)
            db.session.commit()

            self.test_tenant = Tenant(
                tenant_id=self.test_tenant_id,
                organization_code=self.test_org_code,
                sub_domain=self.test_sub_domain,
                tenant_name="Common Test Tenant",
                default_currency="USD",
                description="Common test tenant for all tests",
                status="active",
                country_id=self.test_country_id
            )
            db.session.add(self.test_tenant)
            db.session.commit()

            self.test_branch = Branch(
                branch_id=self.test_branch_id,
                name="Test Branch",
                description="Test description",
                status="active",
                code="TB001",
                country_id=self.test_country_id,
                tenant_id=self.test_tenant_id
            )
            db.session.add(self.test_branch)
            db.session.commit()

            self.test_product = Product(
                product_id=self.test_product_id,
                name="Test Product",
                code="TP001",
                description="A product for testing APIs",
                tag="test",
                sequence=1,
                is_inbound=True,
                supported_file_formats="json,xml"
            )
            db.session.add(self.test_product)
            db.session.commit()

            self.test_module_1 = Module(module_id=self.test_module_id_1, name="Module A", code="MODA")
            self.test_module_2 = Module(module_id=self.test_module_id_2, name="Module B", code="MOD B")
            db.session.add(self.test_module_1)
            db.session.add(self.test_module_2)
            db.session.commit()

            self.test_product_module_1 = ProductModule(
                product_module_id=self.test_product_module_id_1,
                product_id=self.test_product_id,
                module_id=self.test_module_id_1,
                sequence=10
            )
            self.test_product_module_2 = ProductModule(
                product_module_id=self.test_product_module_id_2,
                product_id=self.test_product_id,
                module_id=self.test_module_id_2,
                sequence=20
            )
            db.session.add(self.test_product_module_1)
            db.session.add(self.test_product_module_2)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.rollback() 
            db.session.query(BranchProductModule).filter(
                BranchProductModule.branch_id == self.test_branch_id
            ).delete()
            db.session.commit()
            db.session.query(ProductModule).filter(
                ProductModule.product_id == self.test_product_id
            ).delete()
            db.session.commit()
            db.session.query(Module).filter(
                Module.module_id.in_([self.test_module_id_1, self.test_module_id_2])
            ).delete()
            db.session.commit()
            db.session.query(Product).filter(
                Product.product_id == self.test_product_id
            ).delete()
            db.session.commit()

            if hasattr(self, 'test_tenant_id'):
                try:
                    if db.session.query(TenantReport).filter_by(tenant_id=self.test_tenant_id).first():
                        db.session.query(TenantReport).filter_by(tenant_id=self.test_tenant_id).delete()
                        db.session.commit()
                except Exception as e:
                    print(f"Warning: Could not delete TenantReport (might not exist or be mapped): {e}")

            tenant_to_delete = db.session.get(Tenant, (self.test_tenant_id, self.test_org_code, self.test_sub_domain))
            if tenant_to_delete:
                db.session.delete(tenant_to_delete)
                db.session.commit()

            branch_to_delete = db.session.get(Branch, self.test_branch_id)
            if branch_to_delete:
                db.session.delete(branch_to_delete)
                db.session.commit()

            country_to_delete = db.session.get(Country, self.test_country_id)
            if country_to_delete:
                if not db.session.query(Tenant).filter_by(country_id=self.test_country_id).count() > 0 and \
                   not db.session.query(Branch).filter_by(country_id=self.test_country_id).count() > 0:
                    db.session.delete(country_to_delete)
                    db.session.commit()

            db.session.rollback()
            db.session.remove()
        self.app_context.pop()

    
    def test_create_tenant_invalid_country_id(self):
        """Tests tenant creation with an invalid country_id (zero or non-existent)."""
        payload = {
            "organization_code": f"ORG_INVALID_{uuid.uuid4().hex[:10]}",
            "tenant_name": "Invalid Country Tenant",
            "sub_domain": f"invalidsub_{uuid.uuid4().hex[:10]}",
            "default_currency": "USD",
            "description": "Tenant with bad country",
            "status": "active",
            "country_id": 0
        }
        response = self.client.post('/api/tenants', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        response_json = response.get_json()
        self.assertIsNotNone(response_json)
        self.assertIn("error", response_json)

        self.assertEqual(response_json["error"], "Invalid country_id provided or country does not exist.")


    def test_update_tenant_missing_fields(self):
        """Tests updating a tenant with missing required fields."""
        payload = {
            "tenant_name": "Missing Fields",
            "country_id": self.test_country_id
        }
        response = self.client.put(
            f'/api/tenants/{self.test_tenant_id}/{self.test_org_code}/{self.test_sub_domain}',
            data=json.dumps(payload),
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        response_json = response.get_json()
        self.assertIsNotNone(response_json)
        self.assertIn("error", response_json)
        self.assertIn("Missing fields", response_json["error"])
        self.assertTrue(any(field in response_json["error"] for field in ["default_currency", "description", "status"]))

    def test_get_branches_negative_tenant_id(self):
        """Tests retrieving branches for a non-existent tenant ID (negative)."""
        response = self.client.get('/api/tenants/-1/NONEXISTENTORG/test-sub/branches')
        self.assertEqual(response.status_code, 404)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None for 404 errors")

        self.assertIn("error", response_json)
        self.assertEqual(response_json["error"], "Resource not found")
        self.assertIn("details", response_json)
        self.assertIn("The requested URL was not found on the server.", response_json["details"])

    @patch('app.db.session.add')
    @patch('app.db.session.commit')
    @patch('app.db.session.get')
    @patch('app.db.session.get')
    def test_create_branch_invalid_code_and_country(self, mock_get_tenant, mock_get_country, mock_commit, mock_add):
        """Tests branch creation with an existing tenant but invalid branch details."""

        mock_get_tenant.return_value = self.test_tenant
        mock_get_country.return_value = self.test_country

        payload = {
            "name": "Main Branch",
            "description": "Head office",
            "status": "active",
            "code": "!!@#$%",
            "country_id": self.test_country_id
        }

        response = self.client.post(
            f'/api/branches/create/{self.test_tenant_id}/{self.test_org_code}/{self.test_sub_domain}',
            data=json.dumps(payload),
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None")
        self.assertIn("error", response_json)

        self.assertIn("Invalid branch code format", response_json["error"])

        mock_add.assert_not_called()
        mock_commit.assert_not_called()

    def test_put_branch_with_no_payload(self):
        """Tests updating a branch with an empty payload."""
        response = self.client.put(f'/api/branches/{self.test_branch_id}', data=json.dumps({}), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None")
        self.assertIn("error", response_json)
        self.assertIn("No input data provided", response_json["error"])

    @patch('app.db.session.get')
    @patch('app.db.session.commit')
    @patch('app.db.session.get')
    def test_put_branch_with_special_characters_and_invalid_country_mocked(self, mock_get_country, mock_commit, mock_get_branch):
        """Tests updating a branch with invalid data, but ensuring country_id is valid."""
        mock_get_branch.return_value = self.test_branch

        mock_get_country.return_value = self.test_country

        payload = {
            "name": "!@#$%^",
            "description": "<script>alert(1)</script>",
            "status": "active",
            "code": "!@!",
            "country_id": self.test_country_id
        }

        response = self.client.put(f'/api/branches/{self.test_branch_id}', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        response_json = response.get_json()
        self.assertIsNotNone(response_json)
        self.assertIn("error", response_json)

        self.assertTrue(
            "Invalid branch name format" in response_json["error"] or
            "Invalid branch code format" in response_json["error"]
        )

        mock_commit.assert_not_called()

    @patch('app.db.session.get', return_value=None)
    @patch('app.db.session.delete')
    @patch('app.db.session.commit')
    def test_delete_branch_negative_id(self, mock_commit, mock_delete, mock_get_branch):
        """Tests deleting a non-existent branch with a negative ID.
        This tests Flask's routing and global 404 handler, not the endpoint's internal 404.
        """
        response = self.client.delete('/api/branches/-1')
        self.assertEqual(response.status_code, 404)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None for 404 errors")

        self.assertIn("error", response_json)
        self.assertEqual(response_json["error"], "Resource not found")
        self.assertIn("details", response_json)
        self.assertIn("The requested URL was not found on the server.", response_json["details"])

        mock_delete.assert_not_called()
        mock_commit.assert_not_called()

    
    def test_get_product_negative_id(self):
        """Tests retrieving a product with a negative ID.
        This now expects Flask's global 404 handler for invalid URL parameters.
        """
        response = self.client.get('/api/products/-1')
        self.assertEqual(response.status_code, 404)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None for 404 errors")

        self.assertIn("error", response_json)
       
        self.assertEqual(response_json["error"], "Resource not found")
        self.assertIn("details", response_json)
        self.assertIn("The requested URL was not found on the server.", response_json["details"])
        
    def test_get_product_non_existent_id(self):
        """Tests retrieving a product with a non-existent ID."""
        non_existent_id = self.test_product_id + 99999
        response = self.client.get(f'/api/products/{non_existent_id}')
        self.assertEqual(response.status_code, 404)
        self.assertIn(f"product with id {non_existent_id} not found", response.get_json()["error"])

    def test_create_product_invalid_parent_id(self):
        """Tests creating a product with an invalid (non-existent) parent_product_id."""
        invalid_parent_id = self.test_product_id + 9999
        payload = {
            "name": "Child Product",
            "code": "CHILD001",
            "description": "A child product",
            "tag": "child",
            "sequence": 2,
            "parent_product_id": invalid_parent_id,
            "is_inbound": False
        }
        response = self.client.post('/api/products', data=json.dumps(payload), headers=self.headers)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())


    def test_create_product_invalid_product_tag_id(self):
        """Tests creating a product with an invalid (non-existent) product_tag_id."""
        invalid_product_tag_id = 99999
        payload = {
            "name": "Tagged Product",
            "code": "TAGGED001",
            "description": "A tagged product",
            "tag": "tagged",
            "sequence": 1,
            "is_inbound": True,
            "product_tag_id": invalid_product_tag_id
        }
        response = self.client.post('/api/products', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 500) 
        self.assertIn("error", response.get_json())


    def test_update_product_non_existent_id(self):
        """Tests updating a product with a non-existent product ID."""
        non_existent_id = self.test_product_id + 99999
        payload = {
            "name": "Updated Non-Existent Product"
        }
        response = self.client.put(f'/api/products/{non_existent_id}', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn(f"Product with id {non_existent_id} not found", response.get_json()["error"])

    def test_update_product_self_parent_reference(self):
        """Tests updating a product to have itself as parent_product_id."""
        payload = {
            "parent_product_id": self.test_product_id
        }
        response = self.client.put(f'/api/products/{self.test_product_id}', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 200) 
        updated_product = db.session.get(Product, self.test_product_id)
        self.assertIsNone(updated_product.parent_product_id) 

    def test_update_product_invalid_product_tag_id(self):
        """Tests updating a product with an invalid (non-existent) product_tag_id."""
        invalid_product_tag_id = 99999
        payload = {
            "product_tag_id": invalid_product_tag_id
        }
        response = self.client.put(f'/api/products/{self.test_product_id}', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 500) 
        self.assertIn("error", response.get_json())

    def test_delete_product_negative_id(self):
        """Tests deleting a non-existent product with a negative ID.
        This now expects Flask's global 404 handler for invalid URL parameters.
        """
        response = self.client.delete('/api/products/-1')
        self.assertEqual(response.status_code, 404)
        response_json = response.get_json()
        self.assertIsNotNone(response_json, "Response JSON should not be None for 404 errors")

        self.assertIn("error", response_json)
       
        self.assertEqual(response_json["error"], "Resource not found")
        self.assertIn("details", response_json)
        self.assertIn("The requested URL was not found on the server.", response_json["details"]) 



    def test_get_configured_modules_invalid_product_id(self):
        """Tests retrieving configured modules with an invalid product_id (non-existent)."""
        invalid_product_id = self.test_product_id + 9999
        response = self.client.get(f'/api/configure_modules?branch_id={self.test_branch_id}&product_id={invalid_product_id}&module_ids={self.test_module_id_1}')
        self.assertEqual(response.status_code, 404)
        self.assertIn("One or more requested product modules are not defined.", response.get_json()["error"])


    def test_get_configured_modules_non_integer_module_ids(self):
        """Tests retrieving configured modules with non-integer module_ids."""
        response = self.client.get(f'/api/configure_modules?branch_id={self.test_branch_id}&product_id={self.test_product_id}&module_ids=abc,123')
        self.assertEqual(response.status_code, 400)
        self.assertIn("module_ids must be a comma-separated list of integers", response.get_json()["error"])

    def test_get_configured_modules_product_module_not_defined(self):
        """Tests retrieving configured modules when a product module is not defined for the given product."""
        non_existent_module_id = self.test_module_id_1 + 9999
        response = self.client.get(f'/api/configure_modules?branch_id={self.test_branch_id}&product_id={self.test_product_id}&module_ids={non_existent_module_id}')
        self.assertEqual(response.status_code, 404)
        self.assertIn("One or more requested product modules are not defined.", response.get_json()["error"])
        self.assertIn(f"No ProductModule found for product_id {self.test_product_id} with missing module(s): module_id {non_existent_module_id}", response.get_json()["details"])


    def test_create_configured_modules_missing_fields(self):
        """Tests creating configured modules with missing required JSON fields."""
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1]
            
        }
        response = self.client.post('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch_id, product_id, module_ids (list), and created_by are required", response.get_json()["error"])

    def test_create_configured_modules_invalid_branch_id(self):
        """Tests creating configured modules with an invalid branch_id (non-existent)."""
        invalid_branch_id = self.test_branch_id + 9999
        payload = {
            "branch_id": invalid_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1],
            "created_by": "test_user"
        }
        response = self.client.post('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn(f"Branch with ID {invalid_branch_id} not found.", response.get_json()["error"])

   

    def test_create_configured_modules_non_list_module_ids(self):
        """Tests creating configured modules with non-list module_ids."""
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": "not_a_list",
            "created_by": "test_user"
        }
        response = self.client.post('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("module_ids must be a list of integers", response.get_json()["error"])

    def test_create_configured_modules_non_integer_module_ids_in_list(self):
        """Tests creating configured modules with non-integer module_ids in the list."""
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1, "abc"],
            "created_by": "test_user"
        }
        response = self.client.post('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("module_ids must be a list of integers", response.get_json()["error"])

    def test_create_configured_modules_product_module_not_defined(self):
        """Tests creating configured modules when a product module is not defined for the given product."""
        non_existent_module_id = self.test_module_id_1 + 9999
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [non_existent_module_id],
            "created_by": "test_user"
        }
        response = self.client.post('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("One or more requested product modules are not defined.", response.get_json()["error"])
        self.assertIn(f"No ProductModule found for product_id {self.test_product_id} and module_id(s): {non_existent_module_id}", response.get_json()["details"])



    def test_delete_configured_modules_missing_fields(self):
        """Tests deleting configured modules with missing required JSON fields."""
        payload = {
            "branch_id": self.test_branch_id,
            
        }
        response = self.client.delete('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch_id, product_id, and module_ids (list) are required", response.get_json()["error"])

    def test_delete_configured_modules_invalid_branch_id(self):
        """Tests deleting configured modules with an invalid branch_id (non-existent)."""
        invalid_branch_id = self.test_branch_id + 9999
        payload = {
            "branch_id": invalid_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1]
        }
        response = self.client.delete('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn(f"Branch with ID {invalid_branch_id} not found.", response.get_json()["error"])

    def test_delete_configured_modules_invalid_product_id(self):
        """Tests deleting configured modules with an invalid product_id (non-existent)."""
        invalid_product_id = self.test_product_id + 9999
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": invalid_product_id,
            "module_ids": [self.test_module_id_1]
        }
        response = self.client.delete('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn(f"Product with ID {invalid_product_id} not found.", response.get_json()["error"])

  

    def test_delete_configured_modules_non_integer_module_ids_in_list(self):
        """Tests deleting configured modules with non-integer module_ids in the list."""
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1, "def"]
        }
        response = self.client.delete('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("module_ids must be a list of integers", response.get_json()["error"])

    def test_delete_configured_modules_no_matching_configs(self):
        """Tests deleting configured modules when no matching configurations are found."""
        
        payload = {
            "branch_id": self.test_branch_id,
            "product_id": self.test_product_id,
            "module_ids": [self.test_module_id_1] 
        }
        response = self.client.delete('/api/configure_modules', data=json.dumps(payload), headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No matching module configurations found for deletion.", response.get_json()["message"])


if __name__ == '__main__':
    unittest.main()
