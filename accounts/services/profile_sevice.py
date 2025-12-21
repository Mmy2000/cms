from accounts.models import Profile


class ProfileService:
    @staticmethod
    def get_profile(user):
        profile = Profile.objects.get(user=user)
        return profile
    