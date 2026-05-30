from celery import shared_task
from django.contrib.auth import get_user_model
from candidates.models import Candidate
from .utils import send_cart_notification, send_recruiter_creation_email

User = get_user_model()

@shared_task
def send_cart_notification_task(client_id, candidate_id):
    """
    Asynchronous Celery task wrapper to send candidate selection emails to recruiters.
    Accepts client_id and candidate_id to remain fully JSON-serializable.
    """
    try:
        client = User.objects.get(id=client_id)
        candidate = Candidate.objects.get(id=candidate_id)
        return send_cart_notification(client, candidate)
    except (User.DoesNotExist, Candidate.DoesNotExist) as e:
        print(f"Error executing send_cart_notification_task: {e}")
        return False

@shared_task
def send_recruiter_creation_email_task(recruiter_id, password):
    """
    Asynchronous Celery task wrapper to send recruiter registration details and password.
    """
    try:
        recruiter = User.objects.get(id=recruiter_id)
        return send_recruiter_creation_email(recruiter, password)
    except User.DoesNotExist as e:
        print(f"Error executing send_recruiter_creation_email_task: {e}")
        return False
