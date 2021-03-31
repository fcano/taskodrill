from django.views.generic import TemplateView


class HomePage(TemplateView):
    template_name = "home.html"


class FeaturesPage(TemplateView):
    template_name = "features.html"
