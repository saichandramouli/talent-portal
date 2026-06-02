from django.test import TestCase
from django.contrib.auth import get_user_model
from teams.models import Team, TechnologyStack
from candidates.models import Candidate, JobTitle, Skill
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


class CandidateHoldTestCase(TestCase):
    def setUp(self):
        # Create standard tech stack
        self.stack = TechnologyStack.objects.create(name="Python")
        
        # Create Recruiter
        self.recruiter = User.objects.create_user(
            email='rec1@test.com',
            password='password123',
            full_name='Recruiter One',
            role='recruiter'
        )
        # Create Another Recruiter
        self.recruiter_two = User.objects.create_user(
            email='rec2@test.com',
            password='password123',
            full_name='Recruiter Two',
            role='recruiter'
        )
        # Create Admin
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='password123',
            full_name='Admin User',
            role='admin'
        )
        # Create Client
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='password123',
            full_name='Client User',
            role='client'
        )
        
        # Create Candidate
        self.candidate = Candidate.objects.create(
            full_name='Candidate Py',
            years_of_experience=3,
            rate_card=50.00,
            location='Remote',
            availability='Immediate',
            recruiter=self.recruiter
        )
        self.candidate.technical_stack.add(self.stack)

    def test_recruiter_owner_can_toggle_hold(self):
        self.client.force_login(self.recruiter)
        response = self.client.post(f'/candidates/{self.candidate.id}/toggle-hold/')
        self.assertEqual(response.status_code, 302)
        self.candidate.refresh_from_db()
        self.assertTrue(self.candidate.is_on_hold)

        # Toggle back
        response = self.client.post(f'/candidates/{self.candidate.id}/toggle-hold/')
        self.assertEqual(response.status_code, 302)
        self.candidate.refresh_from_db()
        self.assertFalse(self.candidate.is_on_hold)

    def test_unauthorized_recruiter_cannot_toggle_hold(self):
        self.client.force_login(self.recruiter_two)
        response = self.client.post(f'/candidates/{self.candidate.id}/toggle-hold/')
        self.assertEqual(response.status_code, 302)
        self.candidate.refresh_from_db()
        self.assertFalse(self.candidate.is_on_hold)

    def test_admin_can_toggle_hold(self):
        self.client.force_login(self.admin)
        response = self.client.post(f'/candidates/{self.candidate.id}/toggle-hold/')
        self.assertEqual(response.status_code, 302)
        self.candidate.refresh_from_db()
        self.assertTrue(self.candidate.is_on_hold)

    def test_client_cannot_see_hold_candidate_on_dashboard(self):
        # When hold is False, it should be visible
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertContains(response, 'Candidate Py')

        # Put on hold
        self.candidate.is_on_hold = True
        self.candidate.save()

        # When hold is True, it should not be visible
        response = self.client.get('/clients/dashboard/')
        self.assertNotContains(response, 'Candidate Py')

    def test_client_cannot_view_details_of_hold_candidate(self):
        self.candidate.is_on_hold = True
        self.candidate.save()

        self.client.force_login(self.client_user)
        response = self.client.get(f'/candidates/{self.candidate.id}/')
        # Should redirect to client_dashboard with error message
        self.assertRedirects(response, '/clients/dashboard/')

    def test_client_cannot_add_hold_candidate_to_cart(self):
        self.candidate.is_on_hold = True
        self.candidate.save()

        self.client.force_login(self.client_user)
        response = self.client.get(f'/clients/cart/add/{self.candidate.id}/')
        # Should redirect back with error
        self.assertRedirects(response, '/clients/dashboard/')
        from clients.models import Cart
        self.assertEqual(Cart.objects.filter(client=self.client_user, candidate=self.candidate).count(), 0)

    def test_client_cart_excludes_hold_candidates(self):
        from clients.models import Cart
        # Add to cart first
        Cart.objects.create(client=self.client_user, candidate=self.candidate)

        self.client.force_login(self.client_user)
        response = self.client.get('/clients/cart/')
        self.assertContains(response, 'Candidate Py')

        # Now put candidate on hold
        self.candidate.is_on_hold = True
        self.candidate.save()

        response = self.client.get('/clients/cart/')
        self.assertNotContains(response, 'Candidate Py')

    def test_location_not_on_dashboards(self):
        # 1. Recruiter Dashboard
        self.client.force_login(self.recruiter)
        response = self.client.get('/candidates/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<th>Location</th>')
        self.assertNotContains(response, 'Remote')
        
        # 2. Client Dashboard
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Remote')
        self.assertNotContains(response, 'Search by candidate name, stack, or location...')

        # 3. Admin Candidate List
        self.client.force_login(self.admin)
        response = self.client.get('/candidates/admin-list/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<th>Location</th>')
        self.assertNotContains(response, 'Remote')

    def test_dashboard_notification_creation_and_actions(self):
        from notifications.utils import send_cart_notification
        from notifications.models import Notification

        # Initial state: recruiter should have no notifications
        self.assertEqual(Notification.objects.filter(user=self.recruiter).count(), 0)

        # Call send_cart_notification
        success = send_cart_notification(self.client_user, self.candidate)
        self.assertTrue(success)

        # Notification should be created in the database
        notifications = Notification.objects.filter(user=self.recruiter)
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.title, f"Talent Portal - Your Candidate Added to Cart: {self.candidate.full_name}")
        self.assertIn(self.client_user.full_name, notification.message)
        self.assertIn(self.candidate.full_name, notification.message)
        self.assertFalse(notification.is_read)

        # Recruiter Dashboard should render it
        self.client.force_login(self.recruiter)
        response = self.client.get('/candidates/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, notification.title)

        # Mark notification as read
        response = self.client.post(f'/notifications/{notification.id}/mark-read/')
        self.assertEqual(response.status_code, 302)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        # Create another notification and test mark all read
        send_cart_notification(self.client_user, self.candidate)
        unread = Notification.objects.filter(user=self.recruiter, is_read=False)
        self.assertEqual(unread.count(), 1)

        response = self.client.post('/notifications/mark-all-read/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(user=self.recruiter, is_read=False).count(), 0)


class JobTitleSkillTestCase(TestCase):
    def setUp(self):
        # Create Tech Stack
        self.stack = TechnologyStack.objects.create(name="Python")
        # Create Admin
        self.admin = User.objects.create_user(
            email='admin_jt@test.com',
            password='password123',
            full_name='Admin User',
            role='admin'
        )
        # Create Recruiter
        self.recruiter = User.objects.create_user(
            email='rec_jt@test.com',
            password='password123',
            full_name='Recruiter User',
            role='recruiter'
        )
        # Create Client
        self.client_user = User.objects.create_user(
            email='client_jt@test.com',
            password='password123',
            full_name='Client User',
            role='client'
        )

    def test_admin_job_title_crud(self):
        self.client.force_login(self.admin)
        
        # Create
        response = self.client.post('/candidates/job-titles/create/', {'name': 'DevOps Engineer'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(JobTitle.objects.filter(name='DevOps Engineer').exists())
        
        # Read/List
        response = self.client.get('/candidates/job-titles/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DevOps Engineer')
        
        # Update
        job_title = JobTitle.objects.get(name='DevOps Engineer')
        response = self.client.post(f'/candidates/job-titles/{job_title.id}/edit/', {'name': 'SRE'})
        self.assertEqual(response.status_code, 302)
        job_title.refresh_from_db()
        self.assertEqual(job_title.name, 'SRE')
        
        # Delete
        response = self.client.post(f'/candidates/job-titles/{job_title.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(JobTitle.objects.filter(name='SRE').exists())

    def test_admin_skill_crud(self):
        self.client.force_login(self.admin)
        
        # Create
        response = self.client.post('/candidates/skills/create/', {'name': 'Kubernetes'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Skill.objects.filter(name='Kubernetes').exists())
        
        # Read/List
        response = self.client.get('/candidates/skills/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kubernetes')
        
        # Update
        skill = Skill.objects.get(name='Kubernetes')
        response = self.client.post(f'/candidates/skills/{skill.id}/edit/', {'name': 'Docker'})
        self.assertEqual(response.status_code, 302)
        skill.refresh_from_db()
        self.assertEqual(skill.name, 'Docker')
        
        # Delete
        response = self.client.post(f'/candidates/skills/{skill.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Skill.objects.filter(name='Docker').exists())

    def test_client_dashboard_relation_filtering(self):
        # Create test titles, skills, and candidates
        jt_python = JobTitle.objects.create(name='Python Developer')
        jt_java = JobTitle.objects.create(name='Java Developer')
        
        s_django = Skill.objects.create(name='Django')
        s_spring = Skill.objects.create(name='Spring Boot')
        
        c1 = Candidate.objects.create(
            full_name='Alice Python',
            years_of_experience=3,
            rate_card=40.00,
            location='Remote',
            availability='Immediate',
            job_title=jt_python,
            recruiter=self.recruiter
        )
        c1.technical_stack.add(self.stack)
        c1.skills.add(s_django)
        
        c2 = Candidate.objects.create(
            full_name='Bob Java',
            years_of_experience=4,
            rate_card=45.00,
            location='Remote',
            availability='Immediate',
            job_title=jt_java,
            recruiter=self.recruiter
        )
        c2.technical_stack.add(self.stack)
        c2.skills.add(s_spring)
        
        self.client.force_login(self.client_user)
        
        # Filter by job title
        response = self.client.get(f'/clients/dashboard/?job_title={jt_python.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Python')
        self.assertNotContains(response, 'Bob Java')
        
        # Filter by skill
        response = self.client.get(f'/clients/dashboard/?skills={s_spring.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Alice Python')
        self.assertContains(response, 'Bob Java')

    def test_client_dashboard_ml_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "ML", "DL", "TensorFlow", "PyTorch", "SQL", "MLOps", "Docker", "AWS",
            "Model Deployment", "R", "Statistics", "Pandas", "NumPy", "Tableau", "Power BI",
            "A/B Testing", "NLP", "CV", "APIs", "Experimentation", "Algorithms",
            "Data Analysis", "Data Visualization", "Excel"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')

    def test_client_dashboard_nn_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "Text Analytics", "NLP", "Data Processing", "Regex", "NLTK", "SpaCy", "SQL",
            "Computer Vision", "OpenCV", "CNN", "Image Processing", "TensorFlow", "PyTorch",
            "Deep Learning", "DL", "Image Annotation", "Bounding Box", "Segmentation",
            "Speech Annotation", "Audio Labeling", "Transcription", "Speech Recognition",
            "Phonetics Basics", "Neural Networks", "RNN", "Transformers", "Model Training", "Optimization"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')

    def test_client_dashboard_nl_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "NLP", "Transformers", "BERT", "GPT", "NLTK", "SpaCy", "Hugging Face",
            "ML", "DL", "Text Mining", "Research", "Text Analytics", "SQL", "Pandas",
            "Data Visualization", "Pytorch", "PyTorch", "Retrieval Augmented Generation",
            "Retrieval Augmented Generation (RAG)", "Text Annotation", "Named Entity Recognition (NER)",
            "Sentiment Labeling", "Linguistics Basics"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')

    def test_client_dashboard_de_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "SQL", "ETL", "Data Pipelines", "Spark", "Hadoop", "Airflow", "AWS",
            "Data Warehousing", "Kafka", "Data Modeling", "dbt", "BI Tools", "Tableau", "Power BI",
            "Big Data", "Java", "Hive", "HDFS", "Distributed Systems", "Informatica", "SSIS",
            "Data Integration", "ML Basics", "ML", "Statistics", "Pandas", "NumPy", "Visualization",
            "Data Visualization", "Data Annotation", "Data Labeling", "Image/Text Tagging", "QA",
            "Tools (Labelbox/CVAT)", "Attention to Detail", "Data Validation", "Annotation Review",
            "Accuracy Check", "Guidelines", "Reporting"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')

    def test_client_dashboard_genai_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "Generative AI", "LLM", "Transformers", "OpenAI APIs", "Prompt Engineering",
            "LangChain", "Fine-tuning", "GPT", "Hugging Face", "RAG", "Retrieval Augmented Generation (RAG)",
            "AI Tools", "NLP Basics", "NLP", "Content Generation", "Testing & Iteration", "AI Integration",
            "APIs", "ML", "Backend Development", "Cloud", "Deployment", "AI Solutions", "System Design",
            "Client Requirements", "Chatbots", "Dialogflow", "Rasa", "Speech APIs", "Intent Recognition",
            "Text Annotation", "Prompt Evaluation", "NER", "Named Entity Recognition (NER)",
            "Sentiment Analysis", "Data Labeling", "LLM Evaluation", "Human Feedback", "RLHF",
            "Quality Analysis", "QA", "Data Validation"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')

    def test_client_dashboard_mlops_skills_javascript(self):
        self.client.force_login(self.client_user)
        response = self.client.get('/clients/dashboard/')
        self.assertEqual(response.status_code, 200)
        
        expected_skills = [
            "Python", "MLOps", "CI/CD", "Docker", "Kubernetes", "Mlflow", "Kubeflow", "AWS",
            "Model Deployment", "ML Platforms", "APIs", "Cloud (AWS/GCP/Azure)", "Cloud", "GCP", "Azure",
            "Data Pipelines", "Scalability", "Infrastructure", "Distributed Systems", "Spark",
            "System Design", "DevOps", "Monitoring", "Automation", "ML Deployment", "Flask", "FastAPI"
        ]
        
        for skill in expected_skills:
            self.assertContains(response, f'"{skill}"')


from django.core.files.uploadedfile import SimpleUploadedFile
from candidates.models import CredentialRequest

class CandidateCredentialsTestCase(TestCase):
    def setUp(self):
        # Create standard tech stack
        self.stack = TechnologyStack.objects.create(name="Python")
        
        # Create Recruiter
        self.recruiter = User.objects.create_user(
            email='rec_cred@test.com',
            password='password123',
            full_name='Recruiter Owner',
            role='recruiter'
        )
        # Create Client
        self.client_user = User.objects.create_user(
            email='client_cred@test.com',
            password='password123',
            full_name='Client User',
            role='client'
        )
        # Create Another Client (Unauthorized)
        self.unauth_client = User.objects.create_user(
            email='unauth_client@test.com',
            password='password123',
            full_name='Unauth Client',
            role='client'
        )
        
        # Create Candidate with PDF files
        self.resume_file = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        self.bgv_file = SimpleUploadedFile("bgv.pdf", b"bgv content", content_type="application/pdf")
        self.eval_file = SimpleUploadedFile("eval.pdf", b"eval content", content_type="application/pdf")
        
        self.candidate = Candidate.objects.create(
            full_name='Candidate Py',
            years_of_experience=3,
            rate_card=50.00,
            location='Remote',
            availability='Immediate',
            recruiter=self.recruiter,
            resume=self.resume_file,
            bgv_verification=self.bgv_file,
            evaluation_certificate=self.eval_file
        )
        self.candidate.technical_stack.add(self.stack)

    def test_client_can_request_credentials(self):
        self.client.force_login(self.client_user)
        response = self.client.get(f'/candidates/{self.candidate.id}/request-credentials/')
        self.assertEqual(response.status_code, 302) # Redirects to cart_view
        
        # Verify request created in pending state
        req = CredentialRequest.objects.get(client=self.client_user, candidate=self.candidate)
        self.assertEqual(req.status, 'pending')

    def test_recruiter_can_approve_request(self):
        req = CredentialRequest.objects.create(client=self.client_user, candidate=self.candidate, status='pending')
        self.client.force_login(self.recruiter)
        response = self.client.post(f'/candidates/requests/{req.id}/approve/')
        self.assertEqual(response.status_code, 302)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')

    def test_recruiter_can_reject_request(self):
        req = CredentialRequest.objects.create(client=self.client_user, candidate=self.candidate, status='pending')
        self.client.force_login(self.recruiter)
        response = self.client.post(f'/candidates/requests/{req.id}/reject/')
        self.assertEqual(response.status_code, 302)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'rejected')

    def test_secure_download_permissions(self):
        # 1. Unauthenticated / Unauthorized Client request should be blocked (403)
        self.client.force_login(self.unauth_client)
        response = self.client.get(f'/candidates/{self.candidate.id}/document/resume/')
        self.assertEqual(response.status_code, 403)
        
        # 2. Request Pending Client should be blocked (403)
        req = CredentialRequest.objects.create(client=self.client_user, candidate=self.candidate, status='pending')
        self.client.force_login(self.client_user)
        response = self.client.get(f'/candidates/{self.candidate.id}/document/resume/')
        self.assertEqual(response.status_code, 403)
        
        # 3. Approved Client should succeed (200)
        req.status = 'approved'
        req.save()
        response = self.client.get(f'/candidates/{self.candidate.id}/document/resume/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/pdf')

    def test_pdf_only_validation_in_form(self):
        # Uploading a non-pdf file should fail validation
        txt_file = SimpleUploadedFile("resume.txt", b"text content", content_type="text/plain")
        form_data = {
            'full_name': 'Candidate Py',
            'years_of_experience': 3,
            'rate_card': 50.00,
            'location': 'Remote',
            'availability': 'Immediate',
            'technical_stack': [self.stack.id],
        }
        file_data = {
            'resume': txt_file
        }
        form = CandidateForm(data=form_data, files=file_data, user=self.recruiter)
        self.assertFalse(form.is_valid())
        self.assertIn('resume', form.errors)
        self.assertIn('Only PDF files are allowed', form.errors['resume'][0])
