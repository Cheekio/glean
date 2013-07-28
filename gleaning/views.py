import datetime

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.decorators import user_passes_test
from userprofile.models import Profile
from gleanevent.models import GleanEvent
from django.contrib.sites.models import Site
from posts.models import Post

def home(request):
	if not request.user.is_anonymous() and not Profile.objects.filter(user=request.user).exists():
		return HttpResponseRedirect(reverse('userprofile:userdetailentry'))
	else:
		gleans = GleanEvent.objects.filter(date__gte=datetime.datetime.now())
		posts = Post.objects.order_by('datetime')[:10]
		return render(request, 'home.html', {'gleans':gleans, 'posts':posts})

	# try:
	# 	prof = Profile.objects.get(user=request.user)
	# 	lastday = datetime.datetime.now()+datetime.timedelta(days=7)
	# 	day1 = datetime.datetime.now()
	# 	gleans = list(GleanEvent.objects.filter(date__gte=day1,date__lte=lastday))
	# 	return render(request, 'home.html',{'gleans' : gleans})
	# except:
	# 	if not request.user.is_anonymous():
	# 		return HttpResponseRedirect(reverse('userprofile:userdetailentry'))
	# 	else:
	# 		lastday = datetime.datetime.now()+datetime.timedelta(days=7)
	# 		day1 = datetime.datetime.now()
	#         gleans = list(GleanEvent.objects.filter(date__gte=day1,date__lte=lastday))
	#         return render(request, 'home.html',{'gleans' : gleans})

	
