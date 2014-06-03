# Create your views here.
import csv
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
# add view for certain type
from django.views.generic import View, UpdateView
from django.views.generic.detail import SingleObjectMixin
# experimenting with edit mixins
from django.utils.decorators import method_decorator, classonlymethod
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required

from farms.models import (Farm, FarmForm, FarmLocation,
                          LocationForm, Contact, ContactForm)
from django.http import HttpResponseForbidden
from generic.mixins import SimpleLoginCheckForGenerics
from farms.forms import *


@permission_required('farms.auth')
def index(request):
    if request.user.has_perm('farms.uniauth'):
        farms_list = Farm.objects.all().order_by('name')
    else:
        farms_list = Farm.objects.filter(
            member_organization=request.user.profile.member_organization
            ).order_by('name')
    return render(request, 'farms/index.html', {'farms': farms_list})


@permission_required('farms.auth')
def newFarm(request):
    if request.method == "POST":

        form = FarmForm(request.POST)
        if form.is_valid():
            new_save = form.save()
            new_save.member_organization.add(
                request.user.profile.member_organization)
            new_save.save()
            if request.POST['action'] == "Save And View":
                return HttpResponseRedirect(
                    reverse('farms:detailfarm', args=(new_save.id,)))
            else:
                return HttpResponseRedirect(reverse(
                    'farms:newlocation', args=(new_save.id,)))
        else:
                return render(
                    request,  'farms/new.html',
                    {'form': form, 'error': 'Your Farm Form Was Not Valid'})
    else:
        form = FarmForm()
        return render(request, 'farms/new.html', {'form': form})


class NewFarm(SimpleLoginCheckForGenerics, CreateView):
    model = Farm
    template_name = 'farms/new.html'
    form_class = NewFarmForm
    success_url = reverse_lazy('farms:index')

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        new_save = form.save()
        new_save.member_organization.add(
            self.request.user.profile.member_organization)
        new_save.save()
        self.object = None
        return super(NewFarm, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if self.request.user.has_perm('farms.auth'):
            return super(NewFarm, self).dispatch(*args, **kwargs)
        else:
            raise Http404


class EditFarm(SimpleLoginCheckForGenerics, UpdateView):
    model = Farm
    template_name = 'farms/edit.html'
    form_class = EditFarmForm

    def get_success_url(self):
        return reverse_lazy(
            "farms:editfarm", kwargs={"pk": int(self.kwargs["pk"])})

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        farm = Farm.objects.get(pk=int(self.kwargs["pk"]))
        if self.request.user.has_perm('farms.uniauth'):
            return super(EditFarm, self).dispatch(*args, **kwargs)
        elif self.request.user.has_perm('farms.auth') and self.request.user.profile.member_organization in farm.member_organization.all():
            return super(EditFarm, self).dispatch(*args, **kwargs)
        else:
            raise Http404


@permission_required('farms.auth')
def editFarm(request, farm_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    if request.method == "POST":
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            new_save = form.save()
            return HttpResponseRedirect(
                reverse('farms:detailfarm', args=(farm_id,)))
        else:
            return render(
                request, 'farms/edit.html',
                {'form': form, 'farm': farm,  'error': 'form needs some work'})
    form = FarmForm(instance=farm)
    return render(request, 'farms/edit.html', {'form': form, 'farm': farm})


@permission_required('farms.auth')
def detailFarm(request, farm_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    return render(request, 'farms/detail.html', {'farm': farm})

# == Delete Farm View ==#


class DeleteFarm(SimpleLoginCheckForGenerics, SingleObjectMixin, View):
    model = Farm
    success_url = reverse_lazy("Farm-List")

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        self.object = self.get_object()
        farm = get_object_or_404(Farm, pk=self.object.pk)
        if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
            return HttpResponseRedirect(reverse('farms:index'))
        return render(request, 'farms/delete_farm.html', {'farm': farm})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        self.object = self.get_object()
        farm = get_object_or_404(Farm, pk=self.object.pk)
        if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
            return HttpResponseRedirect(reverse('farms:index'))
        contacts = Contact.objects.filter(farm=farm)
        if contacts.exists():
            for contact in contacts:
                contact.delete()
        locations = FarmLocation.objects.filter(farm=farm)
        if locations.exists():
            for location in locations:
                location.delete()
        farm.delete()
        return HttpResponseRedirect(reverse('farms:index'))


@permission_required('farms.auth')
def newLocation(request, farm_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            if not FarmLocation.objects.filter(name=form.cleaned_data['name'], farm=farm).exists():
                new_save = form.save(commit=False)
                new_save .farm = farm
                new_save.save()
                return HttpResponseRedirect(
                    reverse('farms:detailfarm', args=(farm_id,)))
            else:
                return render(
                    request, 'farms/new_location.html',
                    {'form': form, 'farm': farm, 'error': 'That Location Name is Taken'})

        else:
            return render(
                request, 'farms/new_location.html',
                {'form': form, 'farm': farm, 'error': 'Form was incorrectly filled out'})
    else:
        form = LocationForm()
        return render(
            request, 'farms/new_location.html',
            {'form': form, 'farm': farm})


@permission_required('farms.auth')
def editLocation(request, farm_id, location_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    location = get_object_or_404(FarmLocation, pk=location_id)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            new_save = form.save()
            return HttpResponseRedirect(
                reverse('farms:detailfarm', args=(farm_id,)))
        else:
            return render(
                request, 'farms/edit_location.html',
                {'form': form, 'farm': farm, 'error': 'Form Had an Error'})
    else:
        form = LocationForm(instance=location)
        return render(
            request, 'farms/edit_location.html',
            {'form': form, 'farm': farm, 'editmode': True})


@permission_required('farms.auth')
def newContact(request, farm_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            new_contact = form.save()
            new_contact.farm = farm
            new_contact.save()
            if request.POST['action'] == 'Save':
                return HttpResponseRedirect(
                    reverse('farms:detailfarm', args=(farm_id,)))
            else:
                form = ContactForm()
                notice = 'Contact %s %s has been saved' % (new_contact.first_name, new_contact.last_name)
                return render(
                    request, 'farms/new_contact.html',
                    {'form': form, 'farm': farm, 'notice': notice})

        else:
            return render(
                request, 'farms/new_contact.html',
                {'form': form, 'farm': farm, 'error': 'Form was incorrectly filled out'})
    else:
        form = ContactForm()
        return render(
            request, 'farms/new_contact.html',
            {'form': form, 'farm': farm, 'notice': ''})


@permission_required('farms.auth')
def editContact(request, farm_id, contact_id):
    farm = get_object_or_404(Farm, pk=farm_id)
    if request.user.profile.member_organization not in farm.member_organization.all() and not request.user.has_perm('farms.uniauth'):
        return HttpResponseRedirect(reverse('farms:index'))
    contact = get_object_or_404(Contact, pk=contact_id)
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            new_save = form.save(commit=False)
            new_save.id = contact_id
            new_save.farm = farm
            new_save.save()
            return HttpResponseRedirect(
                reverse('farms:detailfarm', args=(farm_id,)))
        else:
            return render(
                request, 'farms/edit_contact.html',
                {'form': form, 'farm': farm, 'error': 'Form Had an Error'})
    else:
        form = ContactForm(instance=contact)
        return render(
            request, 'farms/edit_contact.html',
            {'form': form, 'farm': farm, })


@permission_required('farms.auth')
def download(request):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=farms.csv'

    # Create the CSV writer using the HttpResponse as the "file."
    writer = csv.writer(response)
    writer.writerow([
                    'name',
                    'description',

                    'physical address',
                    'physical address',
                    'physical city',
                    'physical state',
                    'physical is mailing',

                    'mailing address',
                    'mailing address',
                    'mailing city',
                    'mailing state',

                    'phone 1',
                    'phone 1 type',
                    'phone 2',
                    'phone 2 type',

                    'email',
                    'direction',
                    'instructions',
                    'counties',

                    'member organization',
                    ])

    if request.user.has_perm('farms.uniauth'):
        farms = Farm.objects.all()
    else:
        farms = Farm.objects.filter(
            member_organization=request.user.profile.member_organization)
    for farm in farms:
        writer.writerow([
            farm.name,
            farm.description,

            farm.address_one,
            farm.address_two,
            farm.city,
            farm.state,
            farm.physical_is_mailing,

            farm.mailing_address_one,
            farm.mailing_address_two,
            farm.mailing_city,
            farm.mailing_state,

            farm.phone_1,
            farm.get_phone_1_type_display(),
            farm.phone_2,
            farm.get_phone_2_type_display(),

            farm.email,
            farm.directions,
            farm.instructions,
            farm.counties.all(),

            farm.member_organization.get(),
            ])

    return response
