from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import NotificationLog

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
        
    # Maintain notification logs
    log = NotificationLog.objects.create(
        client=client,
        candidate=candidate,
        email_sent_to=recruiter.email,
        subject=subject,
        message=message,
        status=status
    )
    return log
