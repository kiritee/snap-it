from __future__ import annotations
import typing
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount, EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest
    from snap_it.users.models import User

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter to handle user signups."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle social login (Google OAuth) and preserve admin status."""

    def is_open_for_signup(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self, request: HttpRequest, sociallogin: SocialLogin, data: dict[str, typing.Any]
    ) -> User:
        """
        Populates user information from social provider info.
        Fix: Only stores email, ignores missing `name` field.
        """
        user = super().populate_user(request, sociallogin, data)

        # Only store email, ignore `name`, `first_name`, and `last_name`
        user.email = data.get("email", "")
        return user  # ✅ Now it will not fail due to missing `name`

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin):
        """
        Automatically link Google OAuth to existing users based on email.
        Preserve `is_superuser` and `is_staff` if the user is an admin.
        """
        email = sociallogin.user.email

        if email:
            try:
                # Check if a user with this email already exists
                existing_user = User.objects.get(email=email)

                # Preserve admin status
                if existing_user.is_superuser:
                    sociallogin.user.is_superuser = True
                if existing_user.is_staff:
                    sociallogin.user.is_staff = True

                # Check if this social account is already linked
                if not SocialAccount.objects.filter(user=existing_user, provider=sociallogin.account.provider).exists():
                    sociallogin.connect(request, existing_user)  # ✅ Link Google account to existing user
                    sociallogin.user = existing_user  # ✅ Set the existing user to avoid duplicate accounts

            except User.DoesNotExist:
                pass  # If no existing user, allow Django-Allauth to create a new one

        # ✅ Auto-verify email if using Google OAuth
        if sociallogin.account.provider == "google":
            email_address, created = EmailAddress.objects.get_or_create(user=sociallogin.user, email=email)
            email_address.verified = True
            email_address.save()
