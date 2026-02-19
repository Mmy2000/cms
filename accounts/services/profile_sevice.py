from accounts.models import Profile


class ProfileService:
    @staticmethod
    def get_profile(user):
        profile, created = Profile.objects.get_or_create(user=user)
        return profile
