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


from unittest.mock import patch

class RecruiterCreationTestCase(TestCase):
    def setUp(self):
        # Create Admin
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            full_name='Admin User'
        )

    def test_recruiter_self_registration_redirects(self):
        """Test that self-registration for recruiter is disabled and redirects."""
        response = self.client.get('/accounts/register/recruiter/')
        self.assertRedirects(response, '/accounts/login/')
        
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn("Self-registration for recruiters is disabled. Please contact an Administrator to set up your account.", messages)

    @patch('notifications.tasks.send_recruiter_creation_email_task.delay')
    def test_admin_recruiter_creation_success(self, mock_task_delay):
        """Test that admin can successfully create recruiter, triggering credentials email."""
        self.client.force_login(self.admin)
        
        form_data = {
            'full_name': 'New Recruiter',
            'email': 'new_rec@test.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'company_name': 'Recruiting Co',
            'phone': '1234567890',
        }
        
        response = self.client.post('/accounts/recruiters/create/', form_data)
        self.assertEqual(response.status_code, 302) # Redirect to recruiter_list
        self.assertRedirects(response, '/accounts/recruiters/')
        
        # Verify recruiter was created in database
        recruiter = User.objects.get(email='new_rec@test.com')
        self.assertEqual(recruiter.full_name, 'New Recruiter')
        self.assertEqual(recruiter.role, 'recruiter')
        self.assertEqual(recruiter.company_name, 'Recruiting Co')
        self.assertEqual(recruiter.phone, '1234567890')
        self.assertTrue(recruiter.check_password('password123'))
        
        # Verify the celery email notification task was triggered
        mock_task_delay.assert_called_once_with(recruiter.id, 'password123')
