# views.py
import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Question


def send_signup_success_email(user_email, user_name, website_url):
    subject = 'Signup Successful - Account Pending Approval'
    html_message = render_to_string('email/signup_success_email.html',
                                    {'user_name': user_name, 'current_year': 2024, 'website_url': website_url})
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user_email
    send_mail(subject, plain_message, from_email, [to], html_message=html_message)



def send_review_status_email(user_email, user_name, status):
    # Construct the login URL dynamically
    login_url = "https://edugrowconsulting.co.uk/login"

    subject = 'Account Review Status'

    # Render the email template with dynamic context
    html_message = render_to_string('email/review_status_email.html', {
        'user_name': user_name,
        'status': status,
        'login_url': login_url,  # Pass the login URL to the template
        'current_year': 2024  # Or use a dynamic value for the current year
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user_email
    send_mail(subject, plain_message, from_email, [to], html_message=html_message)




def send_question_answered_email(question, request):
    """
    Sends an email to the user when their question is answered by a moderator.

    Parameters:
    - question: The question object.
    - request: The request object for building the absolute URL.
    """
    # Generate the question detail URL dynamically
    question_url = f"{request.scheme}://{request.get_host()}/questions/{question.id}/"

    # Prepare the email context
    context = {
        'question': question,
        'question_url': question_url,
        'current_year': datetime.datetime.now().year
    }

    # Render the HTML and plain text email content
    html_message = render_to_string('email/question_answered_email.html', context)
    plain_message = strip_tags(html_message)
    subject = f"Your Question '{question.title}' Has Been Answered"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [question.user.email]

    # Send the email
    send_mail(subject, plain_message, from_email, to_email, html_message=html_message)


def send_transaction_email(customer_name, customer_email, transaction_id, amount_total, currency, payment_status):
    """
    Sends a transaction confirmation email to the customer.
    """

    # Prepare the email context
    email_context = {
        'customer_name': customer_name,
        'transaction_id': transaction_id,
        'amount_total': amount_total,
        'currency': currency,
        'payment_status': payment_status,
    }


    # Render the email content
    html_message = render_to_string('email/transaction_success_email.html', email_context)
    plain_message = strip_tags(html_message)
    subject = 'Payment Confirmation'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [customer_email]

    # Send the email
    status = send_mail(subject, plain_message, from_email, to_email, html_message=html_message)
    import pdb; pdb.set_trace()
    if status == 1:
        print("Email sent successfully.")
    else:
        print("Email failed to send.")


def get_side_data():
    questions = Question.objects.all().order_by('-created_at')
    # Fetch the 5 most recent questions
    recent_questions = questions.order_by('-created_at')[:5]
    most_viewed_questions = Question.objects.all().order_by('-view_count')[:7]

    return {
        'recent_questions': recent_questions,
        'most_viewed_questions': most_viewed_questions,
    }
