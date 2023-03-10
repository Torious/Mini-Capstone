from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views
from .forms import ResetPasswordForm

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('unauthorized/', views.unauthorized, name='unauthorized'),
    path('list/', views.list_users, name='list_users'),
    path('list_table/', views.list_users_table, name='list_users_table'),
    path('create/', views.create_user, name='create_user'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('preferences/<int:user_id>/', views.edit_preferences, name='edit_preferences'),
    path('access_control/groups/list/', views.list_groups, name='list_groups'),
    path('access_control/groups/list_table/', views.list_groups_table, name='list_groups_table'),
    path('access_control/groups/create/', views.create_group, name='create_group'),
    path('access_control/groups/edit/<int:group_id>/', views.edit_group, name='edit_group'),
    path('flag/<int:user_id>/', views.flag_user, name='flag_user'),
    path('unflag/<int:user_id>/', views.unflag_user, name='unflag_user'),
    path('two_factor_authentication/', views.two_factor_authentication, name='two_factor_authentication'),
    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile/<code>/', views.profile_from_code, name='profile_from_code'),
    path('edit_case/<int:user_id>/', views.edit_case, name='edit_case'),

    path(
        'login/',
        views.LoginViewTo2FA.as_view(template_name='accounts/authentication/login.html'),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),
    path(
        'change_password/',
        views.ChangePasswordView.as_view(),
        name='change_password'
    ),
    path(
        'change_password/done/',
        views.change_password_done,
        name='change_password_done'
    ),
    path(
        'forgot_password/',
        views.forgot_password,
        name='forgot_password'
    ),
    path(
        'forgot_password/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/authentication/forgot_password_done.html'),
        name='forgot_password_done'
    ),
    path(
        'reset_password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            form_class=ResetPasswordForm,
            template_name='accounts/authentication/reset_password.html',
            success_url=reverse_lazy('accounts:reset_password_done')
        ),
        name='reset_password'
    ),
    path(
        'reset_password/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/authentication/reset_password_done.html'),
        name='reset_password_done'
    ),
    path(
        'register/<uidb64>/<token>/',
        views.register_user,
        name='register_user'
    ),
    path(
        'register/password/<uidb64>/password_done/',
        views.register_user_password_done,
        name='register_user_password_done'
    ),
    path(
        'register/password/<uidb64>/<token>/',
        views.RegisterPasswordResetConfirmView.as_view(
            form_class=ResetPasswordForm,
            template_name='accounts/registration/register_user_password.html',
        ),
        name='register_user_password'
    ),
    path(
        'register/details/<uidb64>/<token>/',
        views.register_user_details,
        name='register_user_details'
    ),
    path(
        'register/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/registration/register_user_done.html'),
        name='register_user_done'
    ),

    path('get_distance/<postal_code>/<current_lat>/<current_long>/',
         views.verify_quarantine_compliance, name='get_distance')
]
