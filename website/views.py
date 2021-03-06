from bs4 import BeautifulSoup
import requests
from urllib.parse import unquote

from django.conf import settings
from django.contrib.admindocs.views import ModelIndexView, ModelDetailView
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import TemplateView



# INFO WEBPAGES
################################################################################



def index(request):
    """
    Redirect to ROC landing: ``/pages/``.
    """
    return redirect('homepage')


def homepage(request):
    """
    ROC landing page.
    """
    index_context = {}
    return render(request, 'website/index.html', index_context)


def page(request, val):
    """
    ROC info pages ``/pages/<val>`` are served using google docs HTML embeds.
    See `GOOGLE_DOCS_PAGES` above for the info about each page.
    To change the website will change, edit the google doc with at ``gdoc_url``.
    """
    val = val.rstrip('/')
    if val == "about":
        # for backward compatibility since previously we had `/page/about`
        return redirect('page', val="background")

    elif val in settings.WEBSITE_PAGES_GOOGLE_DOCS:
        context = settings.WEBSITE_PAGES_GOOGLE_DOCS[val]
        template_name = 'website/google_doc_embed_page.html'

        # GET the `embed_url` HTML source and extract the parts we need from it
        # 1. get doc styles from head
        response = requests.get(context["embed_url"])
        soup = BeautifulSoup(response.content, 'html5lib')
        styles = soup.head.find_all('style')
        styles_str = "\n".join(str(style) for style in styles)
        context["google_doc_styles"] = styles_str
        # 2. clean links from google prefix
        links = soup.body.find_all('a')
        for link in links:
            if link.has_attr('href') and 'https://www.google.com/url?q=' in link['href']:
                old_href = link['href']
                href = old_href[len('https://www.google.com/url?q='):]
                print(href)
                new_href = href.split("&")[0] if "&" in href else href
                link['href'] = unquote(new_href)
        # 3. put body inside the main container div
        body_contents_str = "\n".join(str(el) for el in soup.body.contents)
        context["body_contents"] = body_contents_str

    else:
        # old pages (deprecated)
        context = {}
        template_name = 'website/' + val + '.html'

    return render(request, template_name, context)


# PUBLIC ADMIN DOC FOR MODELS
################################################################################

class PublicModelIndexView(ModelIndexView):
    """
    Autogenerated docs for model list.
    TODO: replace with custom docs page
    """
    template_name = 'admin_doc/model_index_public.html'

    def dispatch(self, request, *args, **kwargs):
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['is_nav_sidebar_enabled'] = False
        context_data['site_header'] = 'ROC documentation'
        context_data['site_title'] = 'ROC documentation'
        # import pprint
        # pprint.pprint(context_data)
        return context_data


class PublicModelDetailView(ModelDetailView):
    """
    Autogenerated docs for each model.
    TODO: set order of fields
    """
    template_name = 'admin_doc/model_detail_public.html'

    def dispatch(self, request, *args, **kwargs):
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['is_nav_sidebar_enabled'] = False
        # context_data['site_header'] = 'ROC documentation'
        # context_data['site_title'] = 'ROC documentation'
        #import pprint
        # pprint.pprint(context_data)
        return context_data