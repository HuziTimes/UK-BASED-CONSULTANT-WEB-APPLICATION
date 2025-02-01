from django.contrib.auth.models import AbstractUser
from django.db import models
from .custom_manager import CustomUserManager
from django.urls import reverse
import os
from django.conf import settings
from django.core.files.base import ContentFile
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    country_of_origin = models.CharField(max_length=50, null=True, blank=True)
    university = models.CharField(max_length=100, null=True, blank=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    government_id = models.FileField(upload_to='government_ids/', null=True, blank=True)
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        default='default_profile.png'
    )

    VERIFICATION_STATUS_CHOICES = [
        ('Not Verified', 'Not Verified'),
        ('Verified', 'Verified'),
        ('Refused', 'Refused'),
    ]

    verification_status = models.CharField(
        max_length=15,
        choices=VERIFICATION_STATUS_CHOICES,
        default='Not Verified'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.profile_image:
            static_default_image_path = os.path.join(settings.STATIC_ROOT, 'default_profile.png')
            with open(static_default_image_path, 'rb') as f:
                self.profile_image.save('default_profile.png', ContentFile(f.read()), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Person(models.Model):
    name = models.CharField(max_length=128)
    tagline = models.TextField()


class Question(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')  # User who asked the question
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )  # Moderator who answered
    answer = models.TextField(blank=True, null=True)  # Moderator's answer
    view_count = models.PositiveIntegerField(default=0)  # Number of views
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Adding related_name='votes' to the 'Vote' model's 'question' ForeignKey allows us to access votes via question.votes

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('detail', args=[str(self.id)])

    def vote_total(self):
        return self.votes.filter(vote_type='like').count() - self.votes.filter(vote_type='dislike').count()

class Vote(models.Model):
    UPVOTE = 'up'
    DOWNVOTE = 'down'
    VOTE_CHOICES = [
        (UPVOTE, 'Upvote'),
        (DOWNVOTE, 'Downvote'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('user', 'question')
class ConsultationRequest(models.Model):
    title = models.CharField(max_length=200)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='respond_consult')
    status = models.CharField(max_length=50,
                              choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')],
                              default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation for {self.user.email} on {self.date} at {self.time}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=255, unique=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.CharField(max_length=255, blank=True, null=True)
    amount_total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    payment_status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount_total} {self.currency}"

class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=2, choices=[('US', 'United States'), ('CA', 'Canada'), ('EU', 'Europe')])
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"