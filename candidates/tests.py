from django.test import TestCase
from django.contrib.auth import get_user_model
from teams.models import Team, TechnologyStack
from candidates.models import Candidate
from candidates.forms import CandidateForm

User = get_user_model()

class CandidateRestrictionsTestCase(TestCase):
    def setUp(self):
        # Create Stacks
        self.python_stack = TechnologyStack.objects.create(name="Python")
        self.django_stack = TechnologyStack.objects.create(name="Django")
        self.java_stack = TechnologyStack.objects.create(name="Java")
        
        # Create Team
        self.python_team = Team.objects.create(name="Python Team")
        self.python_team.technology_stacks.add(self.python_stack, self.django_stack)
        
        # Create Recruiters
        self.python_recruiter = User.objects.create_user(
            email='py_recruiter@test.com',
            password='password123',
            full_name='Python Recruiter',
            role='recruiter',
            team=self.python_team
        )
        
        self.unassigned_recruiter = User.objects.create_user(
            email='unassigned@test.com',
            password='password123',
            full_name='Unassigned Recruiter',
            role='recruiter',
            team=None
        )

    def test_allowed_stack_validation_success(self):
        """Form is valid if the selected stack belongs to the recruiter's team."""
        form_data = {
            'full_name': 'John Doe',
            'years_of_experience': 4,
            'rate_card': 55.00,
            'location': 'Remote',
            'availability': 'Immediate',
            'summary': 'Some Python developer notes',
            'technical_stack': [self.python_stack.id]
        }
        form = CandidateForm(data=form_data, user=self.python_recruiter)
        self.assertTrue(form.is_valid(), form.errors)

    def test_blocked_stack_validation_failure(self):
        """Form is invalid if recruiter selects a stack (Java) outside their team (Python Team)."""
        form_data = {
            'full_name': 'Jane Java',
            'years_of_experience': 5,
            'rate_card': 65.00,
            'location': 'New York',
            'availability': 'Immediate',
            'summary': 'Java developer notes',
            'technical_stack': [self.java_stack.id]
        }
        form = CandidateForm(data=form_data, user=self.python_recruiter)
        self.assertFalse(form.is_valid())
        self.assertIn('technical_stack', form.errors)
        self.assertEqual(
            form.errors['technical_stack'][0],
            "You are not authorized to upload candidates outside your assigned technology stack."
        )

    def test_unassigned_recruiter_upload_fails(self):
        """A recruiter with no team assigned cannot upload candidates."""
        form_data = {
            'full_name': 'No Team Dev',
            'years_of_experience': 3,
            'rate_card': 45.00,
            'location': 'Remote',
            'availability': '2 Weeks Notice',
            'summary': 'Developer summary',
            'technical_stack': [self.python_stack.id]
        }
        form = CandidateForm(data=form_data, user=self.unassigned_recruiter)
        self.assertFalse(form.is_valid())
