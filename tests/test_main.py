"""
Multi-tenant isolation and integration tests.

Tests verify:
1. Tenant isolation - Tenant B cannot access Tenant A's data
2. Happy path - Full workflow from login to property creation
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.tenant import Tenant, User
from tests.conftest import get_auth_token


class TestTenantIsolation:
    """
    Tests to verify tenant data isolation.
    
    Critical security tests ensuring one tenant cannot access another's data.
    """
    
    @pytest.mark.asyncio
    async def test_tenant_b_cannot_access_tenant_a_property(
        self,
        client: AsyncClient,
        user_a: User,
        user_b: User,
        tenant_a: Tenant,
        tenant_b: Tenant,
    ):
        """
        Test that Tenant B receives 404 when trying to access Tenant A's property.
        
        Steps:
        1. Login as User A (Tenant A)
        2. Create a property as Tenant A
        3. Login as User B (Tenant B)
        4. Attempt to access Tenant A's property
        5. Assert 404 Not Found (tenant isolation enforced)
        """
        # Step 1: Get token for User A
        token_a = create_access_token(user_id=user_a.id, tenant_id=user_a.tenant_id)
        
        # Step 2: Create property as Tenant A
        property_data = {
            "title": "Luxury Apartment",
            "address": "123 Main St, London",
            "price": 500000.00,
            "property_type": "APARTMENT",
            "status": "AVAILABLE",
        }
        
        response = await client.post(
            "/api/v1/properties/",
            json=property_data,
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 201
        property_a = response.json()
        property_a_id = property_a["id"]
        
        # Step 3: Get token for User B
        token_b = create_access_token(user_id=user_b.id, tenant_id=user_b.tenant_id)
        
        # Step 4: Tenant B attempts to access Tenant A's property
        response = await client.get(
            f"/api/v1/properties/{property_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        
        # Step 5: Assert 404 - Tenant B cannot see Tenant A's property
        assert response.status_code == 404
        assert response.json()["detail"] == "Property not found"
    
    @pytest.mark.asyncio
    async def test_tenant_b_cannot_see_tenant_a_contacts(
        self,
        client: AsyncClient,
        user_a: User,
        user_b: User,
    ):
        """
        Test that Tenant B's contact list doesn't include Tenant A's contacts.
        """
        # Create contact as Tenant A
        token_a = create_access_token(user_id=user_a.id, tenant_id=user_a.tenant_id)
        
        response = await client.post(
            "/api/v1/contacts/",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@tenanta.com",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 201
        
        # List contacts as Tenant B
        token_b = create_access_token(user_id=user_b.id, tenant_id=user_b.tenant_id)
        
        response = await client.get(
            "/api/v1/contacts/",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert response.status_code == 200
        contacts = response.json()
        
        # Tenant B should see empty list (no access to Tenant A's contacts)
        assert len(contacts) == 0
    
    @pytest.mark.asyncio
    async def test_tenant_b_cannot_update_tenant_a_property(
        self,
        client: AsyncClient,
        user_a: User,
        user_b: User,
    ):
        """
        Test that Tenant B cannot update Tenant A's property.
        """
        # Create property as Tenant A
        token_a = create_access_token(user_id=user_a.id, tenant_id=user_a.tenant_id)
        
        response = await client.post(
            "/api/v1/properties/",
            json={
                "title": "Beach House",
                "address": "456 Ocean Dr, Brighton",
                "price": 750000.00,
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert response.status_code == 201
        property_id = response.json()["id"]
        
        # Attempt to update as Tenant B
        token_b = create_access_token(user_id=user_b.id, tenant_id=user_b.tenant_id)
        
        response = await client.patch(
            f"/api/v1/properties/{property_id}",
            json={"title": "HACKED!"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        
        # Should get 404
        assert response.status_code == 404


class TestHappyPath:
    """
    Integration tests for complete user workflows.
    """
    
    @pytest.mark.asyncio
    async def test_full_real_estate_workflow(
        self,
        client: AsyncClient,
        user_a: User,
    ):
        """
        Happy path test: Login -> Create Contact -> Create Property -> List Properties.
        
        Verifies the complete workflow from authentication to data creation.
        """
        # Step 1: Get authentication token
        token = create_access_token(user_id=user_a.id, tenant_id=user_a.tenant_id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create a contact
        contact_response = await client.post(
            "/api/v1/contacts/",
            json={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "phone": "+44 20 1234 5678",
            },
            headers=headers,
        )
        assert contact_response.status_code == 201
        contact = contact_response.json()
        assert contact["first_name"] == "Alice"
        assert contact["tenant_id"] == str(user_a.tenant_id)
        
        # Step 3: Create a property
        property_response = await client.post(
            "/api/v1/properties/",
            json={
                "title": "Modern City Flat",
                "address": "10 Downing Street, London",
                "price": 2500000.00,
                "property_type": "APARTMENT",
                "status": "AVAILABLE",
                "bedrooms": "3",
                "bathrooms": "2",
            },
            headers=headers,
        )
        assert property_response.status_code == 201
        property_data = property_response.json()
        assert property_data["title"] == "Modern City Flat"
        assert property_data["status"] == "AVAILABLE"
        assert property_data["tenant_id"] == str(user_a.tenant_id)
        
        # Step 4: List properties
        list_response = await client.get(
            "/api/v1/properties/",
            headers=headers,
        )
        assert list_response.status_code == 200
        properties = list_response.json()
        assert len(properties) == 1
        assert properties[0]["title"] == "Modern City Flat"
        
        # Step 5: Get specific property
        get_response = await client.get(
            f"/api/v1/properties/{property_data['id']}",
            headers=headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == property_data["id"]
    
    @pytest.mark.asyncio
    async def test_create_deal_for_contact(
        self,
        client: AsyncClient,
        user_a: User,
    ):
        """
        Test creating a deal linked to a contact.
        """
        token = create_access_token(user_id=user_a.id, tenant_id=user_a.tenant_id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create contact
        contact_response = await client.post(
            "/api/v1/contacts/",
            json={
                "first_name": "Bob",
                "last_name": "Wilson",
                "email": "bob@example.com",
            },
            headers=headers,
        )
        assert contact_response.status_code == 201
        contact_id = contact_response.json()["id"]
        
        # Create deal linked to contact
        deal_response = await client.post(
            "/api/v1/deals/",
            json={
                "title": "Property Purchase - 123 Main St",
                "amount": 350000.00,
                "stage": "NEW",
                "contact_id": contact_id,
            },
            headers=headers,
        )
        assert deal_response.status_code == 201
        deal = deal_response.json()
        assert deal["title"] == "Property Purchase - 123 Main St"
        assert deal["contact_id"] == contact_id
        assert deal["stage"] == "NEW"


class TestAuthentication:
    """
    Authentication endpoint tests.
    """
    
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self,
        client: AsyncClient,
        user_a: User,
    ):
        """Test successful login returns JWT token."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "user_a@tenanta.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_password(
        self,
        client: AsyncClient,
        user_a: User,
    ):
        """Test login fails with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "user_a@tenanta.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(
        self,
        client: AsyncClient,
    ):
        """Test protected endpoints require authentication."""
        response = await client.get("/api/v1/properties/")
        assert response.status_code == 401


class TestHealthCheck:
    """
    Health check endpoint tests.
    """
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "status" in response.json()
