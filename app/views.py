import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.http import JsonResponse
from django.template.loader import render_to_string
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
import requests
from app.forms import CustomLoginForm, ContactForm
from app.models import Question, ConsultationRequest, Transaction, Vote, Contact
from .forms import CustomUserCreationForm


class CustomLoginView(LoginView):
    authentication_form = CustomLoginForm
    template_name = 'registration/login.html'

    def form_valid(self, form):
        user = form.get_user()

        # Check if the user's verification status is 'Verified'
        if user.verification_status != 'Verified':
            # Log them out immediately
            logout(self.request)

            # Generate appropriate message
            if user.verification_status == 'Refused':
                messages.error(
                    self.request,
                    'Your account verification was refused. Please contact support for assistance.'
                )
            else:
                messages.error(
                    self.request,
                    'Your account has not been verified yet. Please wait for verification or contact support.'
                )

            # Redirect back to the login page
            return redirect(reverse('login'))

        # If the user is verified, proceed with the normal login process
        return super().form_valid(form)


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get client's IP address
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        is_uk_user = True

        # Use ip-api.com to get country information
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            data = response.json()
            country_code = data.get('countryCode')
            if country_code != 'GB':  # 'GB' is the country code for the UK
                is_uk_user = False
            elif country_code == 'PK':  # 'PK' is the country code for Pakistan
                is_pk_user = True
        except requests.RequestException as e:
            print(f"Error fetching IP information: {e}")
            messages.error(self.request, 'Unable to verify your location at this time.')
            is_uk_user = False  # If we can't verify, restrict access for safety

        context['is_uk_user'] = True
        return context


def index(request):
    # Annotate questions with upvote and downvote counts
    questions = Question.objects.annotate(
        upvote_count=Count('vote', filter=Q(vote__vote_type='up')),
        downvote_count=Count('vote', filter=Q(vote__vote_type='down'))
    ).order_by('-created_at')

    # Pagination settings
    page_number = request.GET.get('page', 1)
    paginator = Paginator(questions, 10)  # Show 10 questions per page
    page_obj = paginator.get_page(page_number)

    user_votes = {}
    # Get the logged-in user's votes
    if request.user.is_authenticated:
        user_votes = {vote.question_id: vote.vote_type for vote in Vote.objects.filter(user=request.user)}

    # Handling AJAX request for loading more questions
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        questions_html = render_to_string('components/questions_list.html', {'questions': page_obj}, request)
        return JsonResponse({
            'questions_html': questions_html,
            'has_next': page_obj.has_next(),  # Indicates if there are more pages to load
        })

    # Render initial page load
    context = {
        'questions': page_obj,
        'user_votes': user_votes,
        'show_more': paginator.count > 10  # Show "Show More" if there are more than 10 questions
    }
    return render(request, 'index.html', context)


def signin(request):
    return render(request, 'registration/login.html')


def detail(request, id):
    # Get the question and annotate with vote counts
    question = get_object_or_404(
        Question.objects.annotate(
            upvote_count=Count('vote', filter=Q(vote__vote_type='up')),
            downvote_count=Count('vote', filter=Q(vote__vote_type='down'))
        ), id=id
    )

    # Increment the view count
    question.view_count += 1
    question.save()

    # Get the user's vote type (if logged in)
    user_vote = None
    if request.user.is_authenticated:
        vote = Vote.objects.filter(user=request.user, question=question).first()
        if vote:
            user_vote = vote.vote_type

    # Handle voting logic if a POST request is made
    if request.method == 'POST' and request.user.is_authenticated:
        vote_type = request.POST.get('vote_type')
        if vote_type in ['up', 'down']:
            existing_vote = Vote.objects.filter(user=request.user, question=question).first()

            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    # Remove the vote if the same vote type is clicked again
                    existing_vote.delete()
                    messages.info(request, "Your vote has been removed.")
                else:
                    # Update the vote type
                    existing_vote.vote_type = vote_type
                    existing_vote.save()
                    messages.success(request, "Your vote has been updated.")
            else:
                # Create a new vote
                Vote.objects.create(user=request.user, question=question, vote_type=vote_type)
                messages.success(request, "Your vote has been recorded.")

        # Redirect to avoid resubmission on refresh
        return redirect('detail', id=id)

    return render(request, 'question_detail.html', {
        'question': question,
        'user_vote': user_vote,
    })




@login_required(login_url='login')
def ask(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')

        # Create a new question entry
        question = Question.objects.create(
            title=title,
            message=message,
            user=request.user  # Associate the logged-in user with the question
        )

        # Success message
        messages.success(request, "Your question has been posted successfully!")
        return redirect('detail', question.id)
    return render(request, 'ask.html')


@login_required(login_url='login')
def book_consultation(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        preferred_date = request.POST.get('preferred_date')
        preferred_time = request.POST.get('preferred_time')

        # Create a new consultation entry (adjust model fields accordingly)
        consultation = ConsultationRequest.objects.create(
            title=title,
            message=description,
            date=preferred_date,
            time=preferred_time,
            user=request.user  # Assuming the student is logged in
        )

        # Success message
        messages.success(request, "Your consultation has been booked successfully!")
        return redirect('index')  # Redirect to a success or consultation list page

    return render(request, 'consult.html')


def privacy_terms(request):
    return render(request, 'privacy_terms.html')


def faqs(request):
    return render(request, 'faqs.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save data to the database using the Contact model
            Contact.objects.create(
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                company=form.cleaned_data['company'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                country=form.cleaned_data['country'],
                message=form.cleaned_data['message']
            )
            messages.success(request, 'Your message has been successfully sent.')
            return redirect('contact')  # Assuming you have a URL named 'contact'
        else:
            messages.error(request, 'There was an error with your submission. Please correct the highlighted fields.')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


@login_required(login_url='login')
def donate(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Validate the amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Please enter a valid donation amount.')
                return redirect('donate')
        except (ValueError, InvalidOperation):
            messages.error(request, 'Please enter a valid donation amount.')
            return redirect('donate')

        # Convert amount to cents
        amount_cents = (amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        amount_cents = int(amount_cents)

        # Initialize Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # Create a unique transaction ID
            transaction_id = str(uuid.uuid4())

            # Create a Stripe Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',  # Change to your currency if needed
                        'unit_amount': amount_cents,
                        'product_data': {
                            'name': 'Donation',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('payment_failure')),
                customer_email=email,
                payment_intent_data={
                    'metadata': {
                        'transaction_id': transaction_id,
                        'name': name,
                        'message': message,
                    },
                },
            )

            # Store transaction details in the Transaction model
            Transaction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                transaction_id=transaction_id,
                customer_name=name,
                customer_email=email,
                amount_total=amount,
                currency='usd',
                payment_status='Pending',
            )

            # Redirect to Stripe Checkout
            return redirect(session.url, code=303)
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('donate')

    else:
        return render(request, 'donation.html')


@login_required(login_url='login')
def payment_success(request):
    session_id = request.GET.get('session_id', None)

    if not session_id:
        messages.error(request, 'No session ID provided.')
        return redirect('donate')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        # Retrieve the session and expand the payment_intent
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['payment_intent']
        )

        # Verify payment status
        if session.payment_status == 'paid':
            # Access metadata from payment_intent
            payment_intent = session.payment_intent
            metadata = payment_intent.metadata
            transaction_id = metadata.get('transaction_id')

            # Retrieve the Transaction instance
            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)
                # Update the transaction details
                transaction.payment_status = 'Completed'
                transaction.save()
            except Transaction.DoesNotExist:
                messages.error(request, 'Transaction not found.')
                return redirect('donate')

            # Collect data to pass to the template
            amount_cents = session.amount_total  # Amount in cents
            amount_dollars = Decimal(amount_cents) / 100  # Convert to dollars

            # Get date and time of the payment
            from django.utils import timezone
            payment_datetime = timezone.now()

            # Prepare context data
            context = {
                'order_number': transaction_id,
                'date': payment_datetime.strftime('%B %d, %Y, %I:%M %p'),
                'donation_amount': amount_dollars,
                'email': transaction.customer_email,
                'phone': '',  # If you have phone number, include it here
            }

            messages.success(request, 'Thank you for your donation!')
            return render(request, 'payment_success.html', context)
        else:
            messages.error(request, 'Payment was not successful.')
            return redirect('donate')
    except Exception as e:
        messages.error(request, f'An error occurred while processing your payment: {str(e)}')
        return redirect('donate')


@login_required(login_url='login')
def payment_failure(request):
    session_id = request.GET.get('session_id', None)

    if session_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['payment_intent']
            )
            transaction_id = session.payment_intent.metadata.get('transaction_id')
            # Retrieve and update the Transaction instance
            try:
                transaction = Transaction.objects.get(transaction_id=transaction_id)
                transaction.payment_status = 'Canceled'
                transaction.save()
            except Transaction.DoesNotExist:
                pass  # Transaction not found; handle as needed
        except Exception as e:
            pass  # Handle exceptions as needed

    messages.error(request, 'Your payment was canceled or failed.')
    return render(request, 'payment_failure.html')


@login_required(login_url='login')
def dashboard(request):
    user = request.user  # Get the currently logged-in user

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile_update':
            # Handle profile updates
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            profile_image = request.FILES.get('profile_image')

            if not first_name or not last_name:
                messages.error(request, 'First name and last name are required.')
            else:
                # Update user fields
                user.first_name = first_name
                user.last_name = last_name
                user.phone_number = phone_number

                if profile_image:
                    user.profile_image = profile_image

                user.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('dashboard')

        elif form_type == 'change_password':
            # Handle change password form submission
            current_password = request.POST.get('current_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_new_password = request.POST.get('confirm_new_password', '').strip()

            if not user.check_password(current_password):
                messages.error(request, 'Your current password is incorrect.')
            elif new_password != confirm_new_password:
                messages.error(request, 'The new passwords do not match.')
            else:
                try:
                    validate_password(new_password, user=user)
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # Keep the user logged in
                    messages.success(request, 'Your password has been updated successfully.')
                    return redirect('dashboard')
                except ValidationError as e:
                    messages.error(request, e.messages[0])

    # Handle questions listing
    search_query = request.GET.get('search', '')
    questions = Question.objects.filter(user_id=user.id)

    if search_query:
        questions = questions.filter(
            title__icontains=search_query)  # You can also include 'message__icontains' if needed

    # Order questions by creation date (newest first)
    questions = questions.order_by('-created_at')

    # Pagination for questions
    paginator = Paginator(questions, 10)  # Show 10 questions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle consultations listing
    consult_search_query = request.GET.get('consult_search', '')
    consultations = ConsultationRequest.objects.filter(user=user)

    if consult_search_query:
        consultations = consultations.filter(
            title__icontains=consult_search_query
        )

    # Order consultations by date (upcoming first)
    consultations = consultations.order_by('date', 'time')

    # Pagination for consultations
    consult_paginator = Paginator(consultations, 10)
    consult_page_number = request.GET.get('consult_page')
    consult_page_obj = consult_paginator.get_page(consult_page_number)

    # Handle transactions listing
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')

    # Pagination for transactions
    transaction_paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    transaction_page_number = request.GET.get('transaction_page')
    transaction_page_obj = transaction_paginator.get_page(transaction_page_number)

    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'email': user.email,
        'age': user.age,
        'country_of_origin': user.country_of_origin,
        'university': user.university,
        'course': user.course,
        'government_id': user.government_id,
        'profile_image': user.profile_image,
        'verification_status': user.verification_status,
        'page_obj': page_obj,
        'search_query': search_query,
        'consult_page_obj': consult_page_obj,
        'consult_search_query': consult_search_query,
        'transaction_page_obj': transaction_page_obj,
    }
    return render(request, 'dashboard.html', context)


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)


def search(request):
    query = request.GET.get('q', '')  # Get the search term from the query parameter
    results = []

    if query:
        # Filter the questions based on the query (case-insensitive)
        results = Question.objects.filter(title__icontains=query) | Question.objects.filter(message__icontains=query)

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'search.html', context)


def vote(request, question_id):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to be logged in to vote.')
        return redirect('question_list')  # Replace 'question_list' with your view name for the question list page.

    question = get_object_or_404(Question, id=question_id)
    vote_type = request.POST.get('vote_type')

    if vote_type not in [Vote.UPVOTE, Vote.DOWNVOTE]:
        messages.error(request, 'Invalid vote type.')
        return redirect('index')  # Replace with your question detail view name.

    # Check if a vote already exists
    vote, created = Vote.objects.get_or_create(user=request.user, question=question)

    if not created and vote.vote_type == vote_type:
        # If the same vote is clicked again, remove the vote
        vote.delete()
        messages.info(request, 'Your vote has been removed.')
    else:
        # Otherwise, update or create the vote
        vote.vote_type = vote_type
        vote.save()
        if vote_type == Vote.UPVOTE:
            messages.success(request, 'You upvoted this question.')
        else:
            messages.success(request, 'You downvoted this question.')

    return redirect('index')
