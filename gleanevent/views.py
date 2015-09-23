import csv
import datetime
import time

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.views import generic
from django import forms
from django.forms.models import modelformset_factory

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.template import RequestContext, loader
from django.utils.decorators import method_decorator

from weasyprint import HTML

from gleanevent.models import GleanEvent
from gleanevent.forms import GleanForm
from farms.models import Farm, FarmLocation
from announce.models import Announcement
from userprofile.models import Profile

from functions import primary_address

from django_comments.forms import CommentForm


class CustomCommentForm(CommentForm):

    def __init__(self, *args, **kwargs):
        super(CustomCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget = forms.TextInput()


@login_required
def index(request):
    profile = get_object_or_404(Profile, user=request.user)
    date_from = request.GET.get('date_from', '')
    date_until = request.GET.get('date_until', '')
    if date_from:
        date_from = date_from[6:] + '-' + date_from[:2] + '-' + date_from[3:5]
    else:
        date_from = '2013-01-01'
    if date_until:
        date_until = (date_until[6:] + '-' + date_until[:2] +
                      '-' + date_until[3:5])
    else:
        date_until = '3013-01-01'
    if request.user.has_perm('gleanevent.uniauth'):
        gleaning_events_list = GleanEvent.objects.all()
    else:
        gleaning_events_list = GleanEvent.objects.filter(
            member_organization=profile.member_organization)
    try:
        gleaning_events_list = gleaning_events_list.filter(
            date__gte=date_from).filter(date__lte=date_until).order_by('-date')
    except:
        notice = 'Use the Date Picker you Muppets!'
        return render(
            request,
            'gleanevent/index.html',
            {'gleans': gleaning_events_list, 'notice': notice}
        )
    return render(
        request,
        'gleanevent/index.html',
        {'gleans': gleaning_events_list, 'notice': ''}
    )


class NewGlean(generic.CreateView):
    model = GleanEvent
    form_class = GleanForm
    template_name = "gleanevent/new.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        self.object.member_organization = user.profile.member_organization
        self.object.created_by = user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = {}
        context.update(kwargs)
        context['form'].fields['created_by'].initial = self.request.user
        return super(NewGlean, self).get_context_data(**context)


class DetailGlean(generic.DetailView):
    model = GleanEvent
    template_name = "gleanevent/detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DetailGlean, self).dispatch(*args, **kwargs)


class UpdateGlean(generic.UpdateView):
    model = GleanEvent
    form_class = GleanForm
    template_name = "gleanevent/edit.html"
    success_url = reverse_lazy("home")


@permission_required('gleanevent.auth')
def deleteGlean(request, glean_id):
    glean = get_object_or_404(GleanEvent, pk=glean_id)
    profile = request.user.profile
    if (glean.member_organization != profile.member_organization and
            not request.user.has_perm('gleanevent.uniauth')):
        return HttpResponseRedirect(reverse('gleanevent:index'))
    if request.method == 'POST':
        announces = Announcement.objects.filter(glean=glean)
        if announces.exists():
            for announce in announces:
                announce.delete()
        glean.delete()
        return HttpResponseRedirect(reverse('gleanevent:index'))
    else:
        return render(request, 'gleanevent/delete.html', {'glean': glean})


@login_required
def confirmLink(request, glean_id):
    glean = get_object_or_404(GleanEvent, pk=glean_id)
    if not glean.happened():
        if request.user not in glean.rsvped.all():
            glean.rsvped.add(request.user)
            profile = request.user.profile
            profile.rsvped += 1
            profile.save()
            if request.user in glean.not_rsvped.all():
                glean.not_rsvped.remove(request.user)
            glean.save()
        return render(request, 'gleanevent/confirm.html', {'glean': glean})
    else:
        return HttpResponseRedirect(
            reverse('gleanevent:detailglean', args=(glean_id,)))


@login_required
def denyLink(request, glean_id):
    glean = get_object_or_404(GleanEvent, pk=glean_id)
    if not glean.happened():
        if request.user not in glean.not_rsvped.all():
            glean.not_rsvped.add(request.user)
            if request.user in glean.rsvped.all():
                glean.rsvped.remove(request.user)
                profile = request.user.profile
                profile.rsvped -= 1
                profile.save()
            glean.save()
            return render(request, 'gleanevent/deny.html', {'glean': glean})
        else:
            if request.user in glean.rsvped.all():
                glean.rsvped.remove(request.user)
            return render(request, 'gleanevent/deny.html', {'glean': glean})
    else:
        return HttpResponseRedirect(
            reverse('gleanevent:detailglean', args=(glean_id,)))


@permission_required('gleanevent.auth')
def printGlean(request, glean_id):
    glean = get_object_or_404(GleanEvent, pk=glean_id)

    template = loader.get_template('gleanevent/print.html')
    count = glean.rsvped.all().count()
    if count < 18:
        extra_lines = 18 - count
    else:
        extra_lines = 24 - ((count - 18) % 24)

    html = template.render(RequestContext(
        request,
        {
            'glean': glean,
            'extra_lines': [x for x in range(extra_lines)]
        })
    )

    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'
    ] = 'attachment; filename="{0} List.pdf"'.format(glean.title)

    HTML(string=html, url_fetcher=None).write_pdf(response)
    return response


@permission_required('gleanevent.auth')
def download(request):
    profile = request.user.profile
    if request.method == 'POST':
        date_from = request.POST['date_from']
        date_until = request.POST['date_until']
        if date_from:
            date_from = (date_from[6:] + '-' +
                         date_from[:2] + '-' +
                         date_from[3:5]
                         )
        else:
            date_from = '2013-01-01'
        if date_until:
            date_until = (date_until[6:] + '-' +
                          date_until[:2] + '-' +
                          date_until[3:5]
                          )
        else:
            date_until = '3013-01-01'
        if request.user.has_perm('gleanevent.uniauth'):
            gleaning_events_list = GleanEvent.objects.all()
        else:
            gleaning_events_list = GleanEvent.objects.filter(
                member_organization=profile.member_organization)
        try:
            gleaning_events_list = gleaning_events_list.filter(
                date__gte=date_from, date__lte=date_until).order_by('-date')
        except:
            return render(
                request,
                'gleanevent/downloadglean.html',
                {'error': 'Use the Date Picker, you muppets!'})
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=gleanevent.csv'

        # Create the CSV writer using the HttpResponse as the "file."
        writer = csv.writer(response)
        writer.writerow([
            'title',
            'address_one',
            'address_two',
            'city',
            'state',

            'date',
            'time',
            'description',

            'directions',
            'instructions',

            'volunteers_needed',
            'duration',

            'farm',
            'farm_location',

            'created_by',
            'invited_volunteers',

            'rsvped',
            'not_rsvped',
            'waitlist',

            'attending_volunteers',
            'officiated_by',
            'counties',

            'member_organization',
        ])

        for glean in gleaning_events_list:
            writer.writerow([
                glean.title,
                glean.address_one,
                glean.address_two,
                glean.city,
                glean.state,

                glean.date,
                glean.time,
                glean.description,

                glean.directions,
                glean.instructions,

                glean.volunteers_needed,
                glean.duration,

                glean.farm,
                glean.farm_location,

                glean.created_by,
                glean.invited_volunteers.all(),

                glean.rsvped.all(),
                glean.not_rsvped.all(),
                glean.waitlist.all(),

                glean.attending_volunteers.all(),
                glean.officiated_by.all(),
                glean.counties,

                glean.member_organization,
                ])

        return response
    else:
        return render(request, 'gleanevent/downloadglean.html', {'error': ''})


@permission_required('gleanevent.auth')
def postGleanDownload(request):
    if request.method == 'POST':
        profile = request.user.profile
        date_from = request.POST['date_from']
        date_until = request.POST['date_until']
        if date_from:
            date_from = (date_from[6:] + '-' +
                         date_from[:2] + '-' +
                         date_from[3:5])
        else:
            date_from = '2013-01-01'
        if date_until:
            date_until = (date_until[6:] + '-' +
                          date_until[:2] + '-' +
                          date_until[3:5])
        else:
            date_until = '3013-01-01'
        if request.user.has_perm('gleanevent.uniauth'):
            post_glean_events_list = PostGlean.objects.all()
        else:
            post_glean_events_list = PostGlean.objects.filter(
                glean__member_organization=profile.member_organization)
        try:
            post_glean_events_list = post_glean_events_list.filter(
                glean__date__gte=date_from, glean__date__lte=date_until
            ).order_by('-glean__date')
        except:
            return render(
                request,
                'gleanevent/downloadpostglean.html',
                {'error': 'Use the Date Picker You Muppets!'})
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment;'
        ' filename=volunteer_hours.csv'

        # Create the CSV writer using the HttpResponse as the "file."
        writer = csv.writer(response)
        writer.writerow([
            'first_name',
            'last_name',
            'username',
            'glean',
            'attended',
            'hours',
            'group',
            'members',
            'notes',
        ])

        for postglean in post_glean_events_list:
            writer.writerow([
                postglean.first_name,
                postglean.last_name,
                postglean.user,
                postglean.glean,
                postglean.attended,
                postglean.hours,
                postglean.group,
                postglean.members,
                postglean.notes,
                ])

        return response
    else:
        return render(
            request,
            'gleanevent/downloadpostglean.html',
            {'error': ''})
