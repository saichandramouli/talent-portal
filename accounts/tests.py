from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class AccountsTestCase(TestCase):
    def test_create_user_with_email(self):
        """Test that user can be created with email as unique identifier."""
        user = User.objects.create_user(
            email='recruiter@test.com',
            password='password123',
            full_name='Test Recruiter',
            role='recruiter'
        )
        self.assertEqual(user.email, 'recruiter@test.com')
        self.assertEqual(user.role, 'recruiter')
        self.assertTrue(user.check_password('password123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test that superuser creation automatically applies staff/superuser roles."""
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            full_name='Test Admin'
        )
        self.assertEqual(admin.email, 'admin@test.com')
        self.assertEqual(admin.role, 'admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_user_no_email_raises_error(self):
        """Test that creating a user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='password123',
                full_name='Test Recruiter'
            )
