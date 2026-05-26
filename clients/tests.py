from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from teams.models import TechnologyStack
from candidates.models import Candidate
from clients.models import Cart

User = get_user_model()

class ClientCartTestCase(TestCase):
    def setUp(self):
        # Create standard tech stack
        self.stack = TechnologyStack.objects.create(name="Python")
        
        # Create recruiter
        self.recruiter = User.objects.create_user(
            email='recruiter@test.com',
            password='password123',
            full_name='Test Recruiter',
            role='recruiter'
        )
        
        # Create candidate
        self.candidate = Candidate.objects.create(
            full_name='John PyDev',
            years_of_experience=5,
            rate_card=60.00,
            location='San Francisco',
            availability='Immediate',
            summary='Python developer notes',
            recruiter=self.recruiter
        )
        self.candidate.technical_stack.add(self.stack)
        
        # Create client
        self.client = User.objects.create_user(
            email='client@test.com',
            password='password123',
            full_name='Test Client',
            role='client'
        )

    def test_add_to_cart_successful(self):
        """Test candidate can be added to client cart successfully."""
        cart_item = Cart.objects.create(client=self.client, candidate=self.candidate)
        self.assertEqual(cart_item.client, self.client)
        self.assertEqual(cart_item.candidate, self.candidate)
        self.assertEqual(self.client.cart_items.count(), 1)

    def test_prevent_duplicate_cart_entries(self):
        """Test that adding a duplicate candidate to a client's cart raises IntegrityError due to database constraints."""
        Cart.objects.create(client=self.client, candidate=self.candidate)
        
        with self.assertRaises(IntegrityError):
            Cart.objects.create(client=self.client, candidate=self.candidate)
            
    def test_remove_from_cart(self):
        """Test that removing candidate from cart works successfully."""
        cart_item = Cart.objects.create(client=self.client, candidate=self.candidate)
        self.assertEqual(self.client.cart_items.count(), 1)
        
        cart_item.delete()
        self.assertEqual(self.client.cart_items.count(), 0)
