from django.http import HttpResponseRedirect
from django.core.paginator import Paginator


class ExcludeMemOrgsMixin(object):
    def get_factory_kwargs(self):
        factory_kwargs = super(ExcludeMemOrgsMixin, self).get_factory_kwargs()
        if self.request.user.has_perms(self.uniauth_string):
            return factory_kwargs
        else:
            factory_kwargs["exclude"] = ("member_organization",)
            return factory_kwargs

    def formset_valid(self, formset):
        if self.request.user.has_perms(self.uniauth_string):
            return super(ExcludeMemOrgsMixin, self).formset_valid(formset)
        memorg = self.request.user.profile.member_organization
        self.object_list = formset.save(commit=False)
        for instance in self.object_list:
            instance.member_organization = memorg
            instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_queryset(self):
        if self.request.method == 'post':
            self.extra = 0
            return super(Hours_Entry, self).get_queryset()
        else:
            GET = self.request.GET
            if "date_from" in GET or "date_until" in GET:
                self.extra = 0
                return super(Hours_Entry, self).get_queryset()
            else:
                queryset = WorkEvent.objects.none()
                self.extra = 10
                return queryset
