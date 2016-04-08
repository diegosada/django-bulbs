from django.db import models

from djbetty import ImageField

from djes.models import Indexable

from bulbs.content.models import ElasticsearchImageField

from bulbs.campaigns.tasks import save_campaign_special_coverage_percolator


class Campaign(Indexable):

    sponsor_name = models.CharField(max_length=255)
    sponsor_logo = ImageField(null=True, blank=True)
    sponsor_url = models.URLField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    campaign_label = models.CharField(max_length=255)
    impression_goal = models.IntegerField(null=True, blank=True)

    # Tunic Campaign ID
    tunic_campaign_id = models.IntegerField(blank=True, null=True, default=None)

    class Mapping:
        sponsor_logo = ElasticsearchImageField()

    def save(self, *args, **kwargs):
        """Kicks off celery task to re-save associated special coverages to percolator

        :param args: inline arguments (optional)
        :param kwargs: keyword arguments
        :return: `bulbs.campaigns.Campaign`
        """
        campaign = super(Campaign, self).save(*args, **kwargs)
        save_campaign_special_coverage_percolator.delay(self.id)
        return campaign

    @property
    def pixel_dict(self):
        data = {}
        for pixel in self.pixels.all():
            data[pixel.get_pixel_type_display()] = pixel.url
        return data


# class CampaignPixel(models.Model):
#     """Right now, there are two types of pixels, "Listing" and "Detail". The
#     intention here is that the "Listing" pixel is fired anywhere a sponsor's
#     logo shows up on a listing page, or a sidebar. The "Detail" pixel is to
#     be fired only when viewing a piece of content connected to that campaign"""

#     LISTING = 0
#     DETAIL = 1
#     PIXEL_TYPES = (
#         (LISTING, 'Listing'),
#         (DETAIL, 'Detail'),
#     )

#     url = models.URLField()
#     pixel_type = models.IntegerField(choices=PIXEL_TYPES, default=LISTING)
