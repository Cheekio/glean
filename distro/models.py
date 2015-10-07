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
    pickup = 'p'
    d_or_p = (
        (delivery, 'delivery'),
        (pickup, 'pickup')
    )
    crop_list = (
        ('Apples', 'Apples'),
        ('Arugula', 'Arugula'),
        ('Beans', 'Beans'),
        ('Beet Greens/Chard', 'Beet Greens/Chard'),
        ('Beets', 'Beets'),
        ('Blueberries', 'Blueberries'),
        ('Bread', 'Bread'),
        ('Broccoli', 'Broccoli'),
        ('Brussel Sprouts', 'Brussel Sprouts'),
        ('Cabbage', 'Cabbage'),
        ('Carrots', 'Carrots'),
        ('Cauliflower', 'Cauliflower'),
        ('Celeriac', 'Celeriac'),
        ('Celery', 'Celery'),
        ('Chard', 'Chard'),
        ('Chinese Cabbage', 'Chinese Cabbage'),
        ('Collards', 'Collards'),
        ('Cooking Greens', 'Cooking Greens'),
        ('Corn', 'Corn'),
        ('CSA Share', 'CSA Share'),
        ('Cucumbers', 'Cucumbers'),
        ('Eggs', 'Eggs'),
        ('Eggplant', 'Eggplant'),
        ('Fennel', 'Fennel'),
        ('Flowers', 'Flowers'),
        ('Garlic/Garlic Scapes', 'Garlic/Garlic Scapes'),
        ('Head Lettuce', 'Head Lettuce'),
        ('Herbs', 'Herbs'),
        ('Kale', 'Kale'),
        ('Kohlrabi', 'Kohlrabi'),
        ('Leeks', 'Leeks'),
        ('Lettuce Mix', 'Lettuce Mix'),
        ('Melons', 'Melons'),
        ('Mesclun', 'Mesclun'),
        ('Microgreen', 'Microgreen'),
        ('Mixed Roots', 'Mixed Roots'),
        ('Mixed Veggies', 'Mixed Veggies'),
        ('Mushrooms', 'Mushrooms'),
        ('Onions', 'Onions'),
        ('Pac Choy', 'Pac Choy'),
        ('Parsnips', 'Parsnips'),
        ('Peas', 'Peas'),
        ('Peppers', 'Peppers'),
        ('Plants/Starts', 'Plants/Starts'),
        ('Potatoes', 'Potatoes'),
        ('Popcorn', 'Popcorn'),
        ('Pumpkins', 'Pumpkins'),
        ('Radishes', 'Radishes'),
        ('Ramps', 'Ramps'),
        ('Raspberries', 'Raspberries'),
        ('Rhubarb', 'Rhubarb'),
        ('Rutabaga', 'Rutabaga'),
        ('Scallions', 'Scallions'),
        ('Seeds', 'Seeds'),
        ('Spinach', 'Spinach'),
        ('Sprouts', 'Sprouts'),
        ('Strawberries', 'Strawberries'),
        ('Sweet Potatoes', 'Sweet Potatoes'),
        ('Summer Sq./Zucchini', 'Summer Sq./Zucchini'),
        ('Tomatillos', 'Tomatillos'),
        ('Tomatoes', 'Tomatoes'),
        ('Turnips', 'Turnips'),
        ('Watermelon', 'Watermelon'),
        ('Winter Squash', 'Winter Squash'),
    )
    field_glean = 'g'
    farm_pickup = 'p'
    farmers_market = 'f'
    drop_off = 'd'
    g_or_p = (
        (field_glean, 'Glean'),
        (farmers_market, "Farmer's Market"),
        (farm_pickup, 'Pickup'),
        (drop_off, "Drop off")
    )
    member_organization = models.ForeignKey(
        MemOrg, verbose_name="Member Organization", null=True, blank=True)
    date_d = models.DateField("Date of Distribution")
    del_or_pick = models.CharField(
        max_length=2,
        choices=d_or_p,
        default='d',
        verbose_name="Distribution Method"
    )
    recipient = models.ForeignKey(
        RecipientSite, verbose_name="Recipient Site", null=True, blank=True)
    field_or_farm = models.CharField(
        max_length=1,
        choices=g_or_p,
        default='g',
        verbose_name="Collection Method"
    )
    date = models.DateField("Harvest Date")
    farm = models.ForeignKey(Farm, null=True, blank=True)
    crops = models.CharField(max_length=50, blank=True, null=True,
                             verbose_name="Crop/Item",
                             choices=crop_list)
    pounds = models.CharField(max_length=5, blank=True, null=True)
    other = models.CharField(max_length=50, blank=True, null=True,
                             verbose_name="Count")
    containers = models.CharField(max_length=20, blank=True, null=True)

    #created_by = models.ForeignKey(User, shiiite)

    class Meta:
        permissions = (
            ("auth", "Member Organization Level Permissions"),
            ("uniauth", "Universal Permission Level"),
        )
        ordering = ["date_d"]

    def __unicode__(self):
        return self.member_organization.name + ' ' + self.date.strftime(
            '%Y %m %d - %I:%M:%S %p')

admin.site.register(Distro)


class WorkEvent(models.Model):
    member_organization = models.ForeignKey(
        MemOrg,
        related_name="hours"
    )
    first_name = models.CharField(max_length=25, blank=True, null=True)
    last_name = models.CharField(max_length=25, blank=True, null=True)
    date = models.DateField(null=True)
    time = models.CharField(max_length=10, blank=True, null=True)
    group = models.CharField(max_length=25, blank=True, null=True)
    members = models.CharField(max_length=10, blank=True, null=True)

    TASK_CHOICES = (
        ("Field Gleaning", "Field Gleaning"),
        ("Farmers Market/Farm Pick-ups", "Farmers Market/Farm Pick-ups"),
        ("Delivery/Distribution", "Delivery/Distribution"),
        ("Administrative Support", "Administrative Support"),
        ("Processing", "Processing")
    )
    task = models.CharField(
        max_length=50,
        choices=TASK_CHOICES,
        blank=True,
        null=True)
    miles = models.CharField(max_length=10, blank=True, null=True)
    notes = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        permissions = (
            ("auth", "Member Organization Level Permissions"),
            ("uniauth", "Universal Permission Level"),
        )
        ordering = ["date"]
