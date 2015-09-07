import datetime

from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db import models
from django.forms import TextInput, Select
from django.forms import ModelForm

from crispy_forms.helper import FormHelper

from constants import STATES, TIME_OF_DAY
from django.contrib.auth.models import User
from farms.models import Farm, FarmLocation
from memberorgs.models import MemOrg
from counties.models import County

# Create your models here.


class GleanEvent(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField('Date', blank=True, null=True)
    time = models.CharField('Time', max_length=40, blank=True, null=True)
    time_of_day = models.CharField(
        '',
        choices=TIME_OF_DAY,
        max_length=2,
        default="NA",
        blank=True,
        null=True)
    farm = models.ForeignKey(Farm, blank=True, null=True)
    farm_location = models.ForeignKey(FarmLocation, blank=True, null=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, null=True)
    volunteers_needed = models.IntegerField(blank=True, default=1)
    duration = models.CharField(max_length=30, blank=True, null=True)

    address_one = models.CharField(
        'Address (line one)', max_length=200, blank=True)
    address_two = models.CharField(
        'Address (line two)', max_length=200, blank=True)
    city = models.CharField('Address (City)', max_length=200, blank=True)
    state = models.CharField(
        "State", choices=STATES, default="VT", max_length=2, blank=True)
    zipcode = models.CharField('Zip Code', max_length=11, blank=True)

    directions = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        User, editable=False, related_name="created_by")
    invited_volunteers = models.ManyToManyField(
        User, null=True, blank=True, related_name="invited_volunteers")

    rsvped = models.ManyToManyField(
        User, null=True, blank=True, related_name="rsvped", editable=False)
    not_rsvped = models.ManyToManyField(
        User, null=True, blank=True, related_name="not_rsvped", editable=False)
    waitlist = models.ManyToManyField(
        User, null=True, blank=True, related_name="waitlisted", editable=False)

    attending_volunteers = models.ManyToManyField(
        User, null=True, blank=True, related_name="attending_voluntters")
    officiated_by = models.ManyToManyField(
        User, blank=True, related_name="officiated_by")
    # counties = models.ForeignKey(County, blank=True, null=True)
    counties = models.ManyToManyField(
        County,
        blank=True,
        null=True,
        related_name="gleans"
    )

    member_organization = models.ForeignKey(MemOrg, editable=False, blank=True)

    def __unicode__(self):
        return unicode(self.date) + self.title

    def happened(self):
        now = datetime.date.today()
        return now > self.date

    def upcomming(self):
        now = datetime.date.today()
        return now <= self.date

    def data_entered(self):
        if self.postglean_set.count() != 0:
            return True
        return False

    @property
    def url(self):
        site = Site.objects.get(pk=1)
        return "http://{0}{1}".format(
            site.domain,
            reverse(
                "gleanevent:detailglean",
                args=(self.id,)
            )
        )

    @property
    def primary_location(self):
        if self.address_one:
            return self
        if (self.farm_location and hasattr(
                self.farm_location, 'instructions') and
                self.farm_location.instructions):
            return self.farm_location
        if (self.farm and hasattr(self.farm, 'instructions') and
                self.farm.instructions):
            return unicode(self.farm.instructions)

    def render_instructions(self):
        if self.instructions:
            return unicode(self.instructions)
        if (self.farm_location and
                hasattr(self.farm_location, 'instructions') and
                self.farm_location.instructions):
            return unicode(self.farm_location.instructions)
        if (self.farm and hasattr(self.farm, 'instructions')
                and self.farm.instructions):
            return unicode(self.farm.instructions)
        else:
            return u"Show up early and have fun!"

    def render_directions(self):
        if self.directions:
            return unicode(self.directions)
        if (self.farm_location and
                hasattr(self.farm_location, 'directions') and
                self.farm_location.directions):
            return unicode(self.farm_location.directions)
        if (self.farm and hasattr(self.farm, 'directions')
                and self.farm.directions):
            return unicode(self.farm.directions)
        else:
            return u"Show up early and have fun!"

    class Meta:
        permissions = (
            ("auth", "Member Organization Level Permissions"),
            ("uniauth", "Universal Permission Level"),
        )
