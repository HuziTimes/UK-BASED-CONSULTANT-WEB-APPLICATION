from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path

from app.views import *

handler404 = custom_404_view
urlpatterns = [
    path('', index, name='index'),
    path('signin/', signin, name='signin'),
    path('detail/<int:id>/', detail, name='detail'),
    path('ask/', ask, name='ask'),
    path('book-consultation/', book_consultation, name='book_consultation'),
    path('privacy-terms/', privacy_terms, name='privacy_terms'),
    path('faqs/', faqs, name='faqs'),
    path('contact/', contact, name='contact'),
    path('donate/', donate, name='donate'),
    path('payment_success/', payment_success, name='payment_success'),
    path('payment_failure/', payment_failure, name='payment_failure'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('search/', search, name='search'),
    path('vote/<int:question_id>/', vote, name='vote'),
    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_forms.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_doness.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirms.html'),
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_completes.html'), name='password_reset_complete'),

]
