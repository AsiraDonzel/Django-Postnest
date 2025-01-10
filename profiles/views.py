from django.contrib.auth.models import User
from django.views.generic import DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from feed.models import Post  # Ensure this model exists
from followers.models import Follower  # Ensure this model exists
import logging

logger = logging.getLogger(__name__)  # For debugging purposes

class ProfileDetailView(DetailView):
    http_method_names = ["get"]
    template_name = "profiles/detail.html"
    model = User
    context_object_name = "user"
    slug_field = "username"
    slug_url_kwarg = "username"
    
    def get_context_data(self, **kwargs):
        user = self.get_object()
        context = super().get_context_data(**kwargs)
        context["total_posts"] = Post.objects.filter(author=user).count()
        if self.request.user.is_authenticated:
            context['you_follow'] = Follower.objects.filter(following=user, followed_by=self.request.user).exists()
        return context


class FollowView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        data = request.POST.dict()

        # Validate the POST data
        if "action" not in data or "username" not in data:
            logger.error("Missing data in POST request: %s", data)
            return HttpResponseBadRequest("Missing action or username in request")

        try:
            other_user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            logger.error("User does not exist: %s", data['username'])
            return HttpResponseBadRequest("User does not exist")

        if data['action'] == "follow":
            # Follow the user
            _, created = Follower.objects.get_or_create(
                followed_by=request.user,
                following=other_user,
            )
            wording = "Unfollow" if created else "Follow"
        elif data['action'] == "unfollow":
            # Unfollow the user
            try:
                follower = Follower.objects.get(
                    followed_by=request.user,
                    following=other_user,
                )
                follower.delete()
                wording = "Follow"
            except Follower.DoesNotExist:
                logger.error("Follow relationship does not exist: %s", data)
                return HttpResponseBadRequest("Follow relationship does not exist")
        else:
            logger.error("Invalid action in POST request: %s", data['action'])
            return HttpResponseBadRequest("Invalid action")

        # Return JSON response
        return JsonResponse({
            'success': True,
            'wording': wording,
        })
