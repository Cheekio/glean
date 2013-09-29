import time

from django.db import models

from django.contrib import admin

from memberorgs.models import MemOrg
from farms.models import Farm
from recipientsite.models import RecipientSite
from django.forms.widgets import TextInput
# Create your models here.

class Distro(models.Model):
	delivery = 'd'
	pickup = 'd'
	d_or_p = (
		(delivery, 'delivery'),
		(pickup, 'pickup')
	)
	field_glean = 'g'
	farm_pickup = 'p'
	farmers_market = 'f'
	g_or_p = (
		(field_glean, 'Field Glean'),
		(farm_pickup, 'Farm Pickup'),
		(farmers_market, "Farmer's Market")
	)
	member_organization = models.ForeignKey(MemOrg, verbose_name = "Member Organization", editable = False)
	date_d = models.DateField("Date of Distribution")
	recipient = models.ForeignKey(RecipientSite, verbose_name = "Recipient Site")
	field_or_farm = models.CharField(max_length=1, choices=g_or_p, default='g', verbose_name="Field Glean, Pickup, or Farmers Market")
	del_or_pick = models.CharField(max_length=2, choices=d_or_p, default='d', verbose_name="Delivery or Pickup?")
	date = models.DateField("Date of Harvest")
	crops = models.CharField(max_length=50, blank=True, null=True)
	farm = models.ForeignKey(Farm, null=True, blank=True)
	pounds = models.CharField(max_length=5, blank=True, null=True)
	other = models.CharField(max_length=50, blank=True, null=True)
	containers = models.CharField(max_length=20, blank=True, null=True)

	#created_by = models.ForeignKey(User, shiiite)

	class Meta:
		permissions = (
			("auth", "Member Organization Level Permissions"),
			("uniauth", "Universal Permission Level"),
		)
	

	def __unicode__(self):
		return self.member_organization.name + ' ' + self.date.strftime('%Y %m %d - %I:%M:%S %p') #+ ' ' + self.created_by.profile_set.first_name + ' ' + self.created_by.profile_set.last_name

admin.site.register(Distro)