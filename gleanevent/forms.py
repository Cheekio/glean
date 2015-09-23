from django import forms
from crispy_forms.bootstrap import (FieldWithButtons,
                                    InlineCheckboxes,
                                    StrictButton,
                                    AppendedText)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (Layout,
                                 Fieldset,
                                 ButtonHolder,
                                 Field,
                                 Row,
                                 Submit,
                                 Div,
                                 HTML)

from counties.models import County
from gleanevent.models import GleanEvent
from constants import STATES, TIME_OF_DAY
from generic.forms import Counties_For_Forms
from django.contrib.auth.models import User, Group


class GleanForm(Counties_For_Forms, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GleanForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "id-custom-registration-form"
        self.helper.form_method = "post"
        self.helper.form_show_errors = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Row("title", "date"),
                    Row("time", "time_of_day", "duration"),
                    Row("volunteers_needed"),
                    Row("farm", "farm_location"),
                    Row("address_one", "address_two"),
                    Row("city", "state", "zipcode"),
                    "created_by",
                    self.county_fieldset,
                    css_class="glean-form-left pull-left"
                ),
                Div(
                    "description",
                    "directions",
                    "instructions",
                    css_class="glean-form-right pull-left"
                ),
                css_class="glean-form-container"
            ),
            HTML("<input type='submit' "
                 "class='glean-button green-button pull-left' "
                 "style='clear:both;' name='submit' value=\"Ok, It's Ready\">")
        )
        if self.instance:
            glean = self.instance

    time_of_day = forms.ChoiceField(label="&nbsp;",
                                    choices=TIME_OF_DAY,
                                    required=False)

    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.HiddenInput()
        )

    class Meta:
        model = GleanEvent
        exclude = [
            'invited_volunteers',
            'attending_volunteers',
            'officiated_by',
            'created_by_id',
            'created_by'
        ]
