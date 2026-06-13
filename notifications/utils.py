from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

def send_cart_notification(client, candidate):
    """
    Sends email notification to the candidate's recruiter when a client adds the candidate to their cart.
    Logs the success/failure state in NotificationLog.
    """
    recruiter = candidate.recruiter
    subject = f"Talent Portal - Your Candidate Added to Cart: {candidate.full_name}"
    
    # Extract candidate tech stack
    tech_stacks = ", ".join([stack.name for stack in candidate.technical_stack.all()])
    
    # Formulate email content
    message = (
        f"Hello {recruiter.full_name},\n\n"
        f"A client has added one of your candidates to their cart on the Talent Recruitment Portal.\n\n"
        f"Client Details:\n"
        f"---------------\n"
        f"Name: {client.full_name}\n"
        f"Company: {client.company_name}\n"
        f"Email: {client.email}\n"
        f"Phone: {client.phone}\n\n"
        f"Candidate Details:\n"
        f"-----------------\n"
        f"Name: {candidate.full_name}\n"
        f"Experience: {candidate.years_of_experience} years\n"
        f"Technology Stack: {tech_stacks}\n"
        f"Rate Card: ${candidate.rate_card}/hr\n"
        f"Location: {candidate.location}\n"
        f"Availability: {candidate.availability}\n\n"
        f"Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Thank you,\n"
        f"Talent Management Portal Team"
    )
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentportal.com')
    recipient_list = [recruiter.email]
    
    try:
        from .models import Notification
        Notification.objects.create(
            user=recruiter,
            title=subject,
            message=message
        )
    except Exception as e:
        print(f"Error creating dashboard notification: {e}")
        
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False
        )
        status = 'success'
    except Exception as e:
        status = 'failed'
        print(f"Error sending email: {e}") # helpful debug print
        
    return status == 'success'

def send_recruiter_creation_email(recruiter, password):
    """
    Sends email to the recruiter about their account creation and login details.
    """
    subject = "Talent Portal - Your Recruiter Account Has Been Created"
    message = (
        f"Hello {recruiter.full_name},\n\n"
        f"An administrator has created a Recruiter account for you on the Talent Recruitment Portal.\n\n"
        f"Here are your login credentials:\n"
        f"-------------------------------\n"
        f"Email Address: {recruiter.email}\n"
        f"Password: {password}\n\n"
        f"You can log in to your dashboard here:\n"
        f"https://talentplatform.people-prime.com/accounts/login/\n\n"
        f"Thank you,\n"
        f"Talent Management Portal Team"
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentportal.com')
    recipient_list = [recruiter.email]
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending recruiter creation email: {e}")
        return False


def send_corporate_cart_notification(corporate_client, candidate, job, recruiter):
    """
    Sends an email to the recruiter when a Corporate Client adds a candidate
    to their cart inside My Space.
    """
    subject = f"My Space – {corporate_client.company_name} shortlisted {candidate.full_name}"
    message = (
        f"Hello {recruiter.full_name},\n\n"
        f"A Corporate Client has added one of your candidates to their shortlist in My Space.\n\n"
        f"Client Details:\n"
        f"---------------\n"
        f"Company: {corporate_client.company_name}\n\n"
        f"Job Requirement:\n"
        f"----------------\n"
        f"Job Title: {job.job_title}\n\n"
        f"Candidate Details:\n"
        f"-----------------\n"
        f"Name: {candidate.full_name}\n"
        f"Technology Stack: {candidate.technology_stack}\n"
        f"Experience: {candidate.total_experience}\n"
        f"Rate Card: ${candidate.rate_card}/hr\n\n"
        f"Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Please follow up with the client as soon as possible.\n\n"
        f"Thank you,\n"
        f"Talent Management Portal Team"
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentportal.com')
    recipient_list = [recruiter.email]

    try:
        from .models import Notification
        Notification.objects.create(
            user=recruiter,
            title=subject,
            message=message
        )
    except Exception as e:
        print(f"Error creating dashboard notification (corporate): {e}")

    try:
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error sending corporate cart email: {e}")
        return False
