from django.views.generic import View
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.http import HttpResponse

from .forms import SignUpForm, activate_user


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
    
    
class ActivateView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        result = activate_user(uidb64, token)
        if result:
            return HttpResponse('Success.')
        else:
            return HttpResponse('Activation link is invalid!')