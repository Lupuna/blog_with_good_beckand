from django.contrib.sitemaps import Sitemap
from . import models


class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return models.Post.published.all()

    def lastmod(self, obj):
        return obj.updated
