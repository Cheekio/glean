# Create your views here.
import time
import datetime
import random

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django import forms
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required

from django.contrib.auth.models import User

from announce.models import Template, Announcement
from announce.forms import TemplateForm, AnnouncementForm, PartialTemplateForm
from gleanevent.models import GleanEvent
from userprofile.models import Profile

from mail_system import *


#==================== Template System ====================#

#== Template Index  View==#
@permission_required('announce.auth')
def Templates(request):
    if request.user.has_perm('announce.uniauth'):
        templates = Template.objects.all()
    else:
        morg = request.user.profile.member_organization
        templates = Template.objects.filter(member_organization=morg)
    return render(request, 'announce/templates.html', {'templates': templates})


#== Template Edit View ==#


class editTemplateClass(generic.UpdateView):
    model = Template
    form_class = PartialTemplateForm
    template_name = 'announce/edit_template.html'

    def get_success_url(self):
        return reverse(
            'announce:detailtemplate',
            kwargs={'template_id': self.object.pk})


@permission_required('announce.auth')
def editTemplate(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            template.member_organization):
        return HttpResponseRedirect(reverse('announce:templates'))
    if request.method == 'POST':
        form = PartialTemplateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['body'].find('{{custom}}') != -1:
                template.body = form.cleaned_data['body']
                template.default = form.cleaned_data['default']
                template.save()
                return HttpResponseRedirect(
                    reverse('announce:detailtemplate', args=(template.id,)))
            else:
                form = PartialTemplateForm(instance=newTemplate)
                return render(
                    request,
                    'announce/edit_template.html',
                    {
                        'form': form,
                        'template': template,
                        'error': 'Need a {{custom}} tag!',
                        'editmode': True
                    }
                )
        else:
            return render(request, 'announce/edit_template.html',
                          {'form': form,
                           'template':
                           template,
                           'error': 'Form was not valid',
                           'editmode': True})
    else:
        form = PartialTemplateForm(instance=template)
        return render(
            request,
            'announce/edit_template.html',
            {'form': form, 'template': template}
        )


#== Create New Template View ==#
@permission_required('announce.auth')
def newTemplate(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            newTemplate = form.save(commit=False)
            if form.cleaned_data['body'].find('{{custom}}') != -1:
                morg = request.user.profile.member_organization
                newTemplate.member_organization = morg
                newTemplate.save()
                return HttpResponseRedirect(reverse('announce:templates'))
            else:
                form = TemplateForm(instance=newTemplate)
                return render(
                    request,
                    'announce/new_template.html',
                    {'form': form, 'error': 'Need a {{custom}} tag!'})
        else:
            return HttpResponse('form is not valid')
    else:
        form = TemplateForm
        return render(request, 'announce/new_template.html', {'form': form})


#== View for Individual Template ==#
@permission_required('announce.auth')
def detailTemplate(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    return render(
        request, 'announce/template_detail.html', {'template': template})


#== Delete Template View ==#
@permission_required('announce.auth')
def deleteTemplate(request, template_id):
    template = get_object_or_404(Template, pk=template_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            template.member_organization):
        return HttpResponseRedirect(reverse('announce:templates'))
    if request.method == 'POST':
        template.delete()
        return HttpResponseRedirect(reverse('announce:templates'))
    return render(
        request, 'announce/delete_template.html', {'template': template})
#==================== Announce System ====================#


#== View for individual Announcement ==#
@permission_required('announce.auth')
def detailAnnounce(request, announce_id):
    announcement = get_object_or_404(Announcement, pk=announce_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            announcement.member_organization):
        return HttpResponseRedirect(reverse('announce:announcements'))
    body = render_mail(template, announcement, request.user.profile)
    glean = announcement.glean
    source = primary_source(announcement.glean)
    if request.method == 'POST' and announcement.sent is False:
        mail_from_source(body, announcement)
        announcement.sent = True
        announcement.sent_by = request.user
        announcement.save()
        return HttpResponseRedirect(
            reverse('announce:detailannounce', args=(announce_id,)))
    else:
        return render(
            request,
            'announce/announce_detail.html',
            {'announcement': announcement,
             'test': body,
             'glean': glean,
             'source': source})


#== Delete Announcement View ==#
@permission_required('announce.auth')
def deleteAnnounce(request, announce_id):
    announce = get_object_or_404(Announcement, pk=announce_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            announce.member_organization):
        return HttpResponseRedirect(reverse('announce:annoucements'))
    if announce.glean.happened():
        return HttpResponseRedirect(reverse('announce:annoucements'))
    if request.method == 'POST':
        announce.delete()
        return HttpResponseRedirect(reverse('announce:announcements'))
    return render(
        request, 'announce/delete_announce.html', {'announce': announce})


#== View for Printable Phone List ==#
@permission_required('announce.auth')
def phoneAnnounce(request, announce_id):
    announcement = get_object_or_404(Announcement, pk=announce_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            announcement.member_organization):
        return HttpResponseRedirect(reverse('announce:announcements'))
    glean = announcement.glean
    source = primary_source(announcement.glean)
    return render(request,
                  'announce/phone.html',
                  {'announcement': announcement,
                   'glean': glean,
                   'source': source})


#== Index of All Announcements ==#
@permission_required('announce.auth')
def Announcements(request):
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
        announcements = Announcement.objects.all()
    else:
        announcements = Announcement.objects.filter(
            member_organization=profile.member_organization)
    try:
        announcements = Announcement.objects.filter(
            datetime__gte=date_from, datetime__lte=date_until).order_by(
            '-datetime')
    except:
        notice = 'Use the Date Picker you Muppets!'
        return render(
            request,
            'announce/announcements.html',
            {'announcements': announcements, 'notice': notice})
    return render(
        request,
        'announce/announcements.html',
        {'announcements': announcements, 'notice': ''})


#== New Announcement View ==#
@permission_required('announce.auth')
def announceGlean(request, glean_id):
    glean = get_object_or_404(GleanEvent, pk=glean_id)
    profile = request.user.profile
    if (not request.user.has_perm('announce.uniauth') and
            profile.member_organization != glean.member_organization):
        return HttpResponseRedirect(
            reverse('gleanevent:detailglean', args=(glean_id,)))
    if not glean.happened():
        empty_announcements = Announcement.objects.filter(
            title='', message='', sent=False)
        for ann in empty_announcements:
            if not ann.active():
                ann.delete()
        query = Template.objects.filter(
            member_organization=profile.member_organization, default=True)
        if query.exists():
            def_template = query.get()
            new_save = Announcement(
                title=glean.title,
                message='',
                glean=glean,
                member_organization=profile.member_organization,
                template=def_template)
            new_save.save()
            new_save.populate_recipients()
            return HttpResponseRedirect(
                reverse('announce:combinedannounce', args=(new_save.id,)))
        else:
            return HttpResponse(
                'no default template selected! You need a template'
                ' to announce a glean!')
    else:
        return HttpResponseRedirect(
            reverse('gleanevent:detailglean', args=(glean_id,))
        )


#== Edit Announcement View ==#
@permission_required('announce.auth')
def editAnnounce(request, announce_id):
    announce = get_object_or_404(Announcement, pk=announce_id)
    profile = request.user.profile
    if (not request.user.has_perm('announce.uniauth') and
            profile.member_organization != announce.member_organization):
        return HttpResponseRedirect(
            reverse('announce:detailannounce', args=(announce_id,)))
    templates = Template.objects.all(
        member_organization=profile.member_organization)
    source = primary_source(announce.glean)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            new_save = form.save(commit=False)
            new_save.member_organization = announce.member_organization
            new_save.glean = announce.glean
            new_save.datetime = announce.datetime
            new_save.id = announce.id
            new_save.save()
            return HttpResponseRedirect(
                reverse('announce:detailannounce', args=(new_save.id,)))
        else:
            return render(
                request,
                'announce/edit_announce.html',
                {'glean': announce.glean,
                 'templates': templates,
                 'form': form,
                 'recipients': recipients,
                 'source': source})
    else:
        templates = Template.objects.all()
        form = AnnouncementForm(instance=announce)
        return render(
            request,
            'announce/edit_announce.html',
            {'glean': announce.glean,
             'templates': templates,
             'form': form,
             'source': source})


#==================== Single Use Links ====================#
#== Unsubscribe 'view' ==#
def unsubscribeLink(request, key):
    prof = get_object_or_404(Profile, unsubscribe_key=key)
    prof.accepts_email = False
    prof.unsubscribe_key = None
    prof.save()
    return render(request, 'announce/unsubscribe.html')


@permission_required('announce.auth')
def combinedAnnounce(request, announce_id):
    announce = get_object_or_404(Announcement, pk=announce_id)
    profile = request.user.profile
    if (not request.user.has_perm('announce.uniauth') and
            profile.member_organization != announce.member_organization):
        return HttpResponseRedirect(
            reverse('announce:detailannounce', args=(announce_id,)))
    glean = announce.glean
    if announce.title:
        subject = announce.title
    else:
        subject = glean.title
    body = weave_template_and_body_and_glean(
        announce.template, announce, glean)
    templates = Template.objects.filter(
        member_organization=profile.member_organization)
    source = primary_source(announce.glean)
    recipients = []
    phone = []

    for recipient in source.counties.people.all():
        if (recipient not in recipients and recipient.accepts_email and
                recipient.preferred_method == '1'):
            recipients.append(recipient)
        elif (recipient.preferred_method == '2' and
                recipient.accepts_email and recipient not in phone):
            phone.append(recipient)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            new_save = form.save(commit=False)
            new_save.member_organization = announce.member_organization
            new_save.glean = announce.glean
            new_save.datetime = announce.datetime
            new_save.id = announce.id
            new_save.save()
            return HttpResponseRedirect(
                reverse('announce:combinedannounce', args=(new_save.id,)))
        else:
            return render(
                request,
                'announce/combined_announce.html',
                {'glean': announce.glean,
                 'templates': templates,
                 'form': form,
                 'recipients': recipients,
                 'phone': phone,
                 'source': source,
                 'subject': subject})
    else:
        templates = Template.objects.all()
        form = AnnouncementForm(instance=announce)
        if not request.user.has_perm('announce.uniauth'):
            form.fields['template'].queryset = Template.objects.filter(
                member_organization=profile.member_organization)
        return render(
            request,
            'announce/combined_announce.html',
            {'glean': announce.glean,
             'announcement': announce,
             'templates': templates,
             'form': form,
             'phone': phone,
             'recipients': recipients,
             'source': source,
             'test': body,
             'subject': subject})


@permission_required('announce.auth')
def sendAnnounce(request, announce_id):
    announcement = get_object_or_404(Announcement, pk=announce_id)
    if (not request.user.has_perm('announce.uniauth') and
            request.user.profile.member_organization !=
            announcement.member_organization):
        return HttpResponseRedirect(reverse('announce:announcements'))
    if request.method == 'POST' and announcement.sent is False:
        glean = announcement.glean
        body = weave_template_and_body_and_glean(
            announcement.template, announcement, glean)
        mail_from_source(body, announcement)
        announcement.sent = True
        announcement.sent_by = request.user
        announcement.save()
        return HttpResponseRedirect(
            reverse('announce:detailannounce', args=(announce_id,)))
    else:
        return HttpResonseRedirect(
            reverse('announce:combinedannounce', args=(annouce_id,)))


def HTMLemail(request, announce_id):
    announce = get_object_or_404(Announcement, pk=announce_id)
    glean = announce.glean
    body = weave_template_and_body_and_glean(
        announce.template, announce, glean)
    if announce.title:
        subject = announce.title
    else:
        subject = glean.title
    return render(
        request, 'announce/HTMLemail.html', {'body': body, 'subject': subject})


@permission_required('announce.auth')
def uninviteUser(request, announce_id, user_id):
    announcement = get_object_or_404(Announcement, pk=announce_id)
    user = get_object_or_404(User, pk=user_id)
    announcement.uninvite_user(user)
    return HttpResponseRedirect(
        reverse('announce:combinedannounce', args=(announce_id,)))


@permission_required('announce.auth')
def recipientList(request, announce_id):
    announcement = get_object_or_404(Announcement, pk=announce_id)
    return render(
        request, 'announce/recipientlist.html', {'announcement': announcement})
