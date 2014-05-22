from collections import OrderedDict

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.core import serializers

import projects.models as cm
from cvs.models import CV


class CCCSDetailView(DetailView):

    def get_context_data(self, **kwargs):
        context = super(CCCSDetailView, self).get_context_data(**kwargs)
        context['serialized'] = serializers.serialize('python', [self.get_object()])[0]
        return context


class ProjectDetailView(CCCSDetailView):
    model = cm.Project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['cvproject_list'] = self.get_object().cvproject_set.all()
        return context


class ProjectCCCSThemeListView(ListView):
    model = cm.Project
    categorization_fieldname = 'cccs_subthemes'
    categorization_parent_fieldname = 'theme'
    categorization_label = 'CCCS Theme'
    template_name = "projects/project_list2.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectCCCSThemeListView, self).get_context_data(**kwargs)
        context['categorization_name'] = self.categorization_label
        context['use_right_col'] = "No"  # a bit hacky but it will do for now
        context['categorization'] = categorize_projects2(context['object_list'],
                                                        self.categorization_fieldname,
                                                        self.categorization_parent_fieldname)
        return context


class ProjectIFCThemeListView(ProjectCCCSThemeListView):
    categorization_fieldname = 'ifc_subthemes'
    categorization_label = 'IFC Theme'


class ProjectCCCSSectorListView(ProjectCCCSThemeListView):
    categorization_fieldname = 'cccs_subsectors'
    categorization_parent_fieldname = 'sector'
    categorization_label = 'CCCS Sector'


class ProjectCountryListView(ListView):
    model = cm.Project
    categorization_fieldname = 'countries'
    categorization_label = 'Country'
    template_name = "projects/project_list1.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectCountryListView, self).get_context_data(**kwargs)
        context['categorization_name'] = self.categorization_label
        context['use_right_col'] = "No"  # a bit hacky but it will do for now
        context['categorization'] = categorize_projects(context['object_list'],
                                                        self.categorization_fieldname)
        return context


class ProjectIFCSectorListView(ProjectCountryListView):
    categorization_fieldname = 'ifc_sectors'
    categorization_label = 'IFC Sector'


def categorize_projects(projects, categorization_fieldname):
    """
    Organise the projects using a single categorization layer
    """
    categorization = dict()
    for project in projects:
        categories = getattr(project, categorization_fieldname).all()
        for category in categories:
            category_name = category.name
            if category_name not in categorization:
                categorization[category_name] = dict(projects=list(), count=0)
            categorization[category_name]['count'] += 1
            categorization[category_name]['id'] = category.id
            categorization[category_name]['projects'].append(project)
    return OrderedDict(((k, categorization[k]) for k in sorted(categorization.keys())))


def categorize_projects2(projects, categorization_fieldname, categorization_parent_fieldname):
    """
    Organise the projects so that they are nested in the sub categorizations
    """
    categorization = dict()
    for project in projects:
        sub_categorizations = getattr(project, categorization_fieldname).all()

        for sub in sub_categorizations:
            sub_name = sub.name
            super_name = getattr(sub, categorization_parent_fieldname).name

            if super_name not in categorization:
                categorization[super_name] = dict(subs=dict(), count=0)

            if sub_name not in categorization[super_name]['subs']:
                categorization[super_name]['subs'][sub_name] = dict(projects=list(), count=0)

            categorization[super_name]['count'] += 1
            categorization[super_name]['id'] = getattr(sub, categorization_parent_fieldname).id
            categorization[super_name]['subs'][sub_name]['projects'].append(project)
            categorization[super_name]['subs'][sub_name]['count'] += 1
            categorization[super_name]['subs'][sub_name]['id'] = sub.id

    for info in categorization.values():
        info['subs'] = OrderedDict(((k, info['subs'][k]) for k in sorted(info['subs'].keys())))
    return OrderedDict(((k, categorization[k]) for k in sorted(categorization.keys())))