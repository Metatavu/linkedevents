import re
import dateutil.parser
import requests
import requests_cache
import pytz
import time
import itertools
import logging
import hashlib
import uuid 
from collections import OrderedDict
from django.db.models import Count

from lxml import etree

from events.models import DataSource, Place, Event, Offer, Keyword
from events.keywords import KeywordMatcher
from django_orghierarchy.models import Organization

from .sync import ModelSyncher
from .base import Importer, register_importer, recur_dict
from .util import clean_text, unicodetext, replace_location

logger = logging.getLogger(__name__) 

from django.core.management.base import BaseCommand, CommandError

OSTERBOTTEN_BASE_URL = 'https://events.osterbotten.fi/EventService/search'
OSTERBOTTEN_PARAMS = {
    'languages': OrderedDict([
        ('fi', 'fi_FI'),
        ('sv', 'sv_SE'),
        ('en', 'en_US'),
    ])
}

@register_importer
class OsterbottenImporter(Importer):
    name = "osterbotten"
    supported_languages = ['fi', 'sv', 'en']

    def __init__(self, *args, **kwargs):
        super(OsterbottenImporter, self).__init__(*args, **kwargs)
        self.timezone = pytz.timezone('Europe/Helsinki')

    def items_from_url(self, url):
        resp = requests.get(url)
        if resp.status_code == 200:
            root = etree.fromstring(resp.content)
            return root.xpath('Events/Event')
        
        return None

    def municipalities_from_url(self, url):
        resp = requests.get(url)
        assert resp.status_code == 200
        root = etree.fromstring(resp.content)
        return root.xpath('Municipalities/Municipality')

    def _import_organizers_from_events(self, events):
        organizers = recur_dict()
        for k, event in events.items():
            if not 'organizer' in event:
                continue
            organizer = event['organizer']
            if not 'name' in organizer or not 'fi' in organizer['name']:
                continue
            oid = organizer['name']['fi']
            organizers[oid]['name'].update(organizer['name'])
            organizers[oid]['phone'].update(organizer['phone'])
        return organizers

    def setup(self):
        defaults = dict(name='Osterbotten')
        self.data_source, _ = DataSource.objects.get_or_create(id=self.name, defaults=defaults)
        self.osterbotten_data_source = DataSource.objects.get(id='osterbotten')
        org_args = dict(id='osterbotten')
        defaults = dict(name='Osterbotten', data_source=self.data_source)
        self.organization, _ = Organization.objects.get_or_create(defaults=defaults, **org_args)
    
        if self.options['cached']:
            requests_cache.install_cache('osterbotten')

    def getUrl(self, locale, start):
        url = OSTERBOTTEN_BASE_URL + '?Locale=' + locale + '&Start=' + str(start)
        return url

    def import_events(self):
        logger.info("Importing Osterbotten events")
        events = recur_dict()
        keyword_matcher = KeywordMatcher()
        for lang, locale in OSTERBOTTEN_PARAMS['languages'].items():
            for i in itertools.count(0, 10):
                items = self.items_from_url( self.getUrl(locale, i) )

                if items is None:
                    continue
                elif len(items) > 0: 
                    for item in items:
                        self._import_event(lang, item, events, keyword_matcher)
                    organizers = self._import_organizers_from_events(events)
                else:
                    break
            
        for event in events.values():
            if (event is not None):
                self.save_event(event)
        logger.info("%d events processed" % len(events.values()))

    def cleanCategory(self, category):
        symbols = ["&", ",", ".", "!"]
        conjunctions = [" och ", " ja ", " and "]
        conjuctionsWithSymbols = ["- och", "- ja"]

        for symbol in symbols:
            category = category.replace(symbol, "")
        for conjuctionsWithSymbol in conjuctionsWithSymbols:
            category = category.replace(conjuctionsWithSymbol, "")
        for conjunction in conjunctions:
            category = category.replace(conjunction, " ")
        
        return " ".join(category.split())

    def _import_event(self, lang, item, events, keyword_matcher):    
        eid = int(item.xpath('ID')[0].text)
        logger.info("Processing event with origin_id: %s" % eid)
        event = events[eid]
        event['data_source'] = self.data_source
        event['publisher'] = self.organization
        event['origin_id'] = eid

        event['headline'][lang] = item.xpath('Title')[0].text
        event['name'][lang] = item.xpath('Title')[0].text
        event['short_description'][lang] = item.xpath('EventTextShort')[0].text
        event['description'][lang] = item.xpath('EventText')[0].text
        event['info_url'][lang] = item.xpath('Link')[0].text

        if (item.xpath('Start')[0].text):
            startTime = dateutil.parser.parse(item.xpath('End')[0].text)
            event['start_time'] = startTime
            event['has_start_time'] = True

        if (item.xpath('End')[0].text):
            endTime = dateutil.parser.parse(item.xpath('End')[0].text)
            if (startTime <= endTime):
                event['start_time'] = endTime
                event['has_start_time'] = True

        if 'offers' not in event:
            event['offers'] = [recur_dict()]
        
        offer = event['offers'][0]
        if item.xpath('PriceType')[0].text == 'Free':
            offer['is_free'] = True
        offer['price'][lang] = item.xpath('PriceHidden')[0].text
        offer['description'][lang] = item.xpath('PriceText')[0].text

        keywords = []

        categories = item.xpath('Categories')[0]
        for category in categories:
            categoryText = category.xpath('Name')[0].text
            cleanedCategory = self.cleanCategory(categoryText)
            categorywords = cleanedCategory.split(' ')
            for categoryWord in categorywords:
                category_origin_id = 'category_{}_{}'.format(category.xpath('ID')[0].text, categoryWord)
                keywords.append(self.upsert_keyword(category_origin_id, categoryWord))
        
        targetGroups = item.xpath('TargetGroups')[0]
        for targetGroup in targetGroups:
            targetGroupText = targetGroup.xpath('Name')[0].text
            target_group_origin_id = 'target_{}'.format(targetGroup.xpath('ID')[0].text)
            keywords.append(self.upsert_keyword(target_group_origin_id, targetGroupText))

        place = item.xpath('Place')[0].text
        if not place:
            logger.info("Missing place name from event, using random uuid instead")
            place = str(uuid.uuid4())

        location_origin_id = hashlib.md5(place.encode('utf-8')).hexdigest()
        address = item.xpath('PostalAddress')[0].text
        city = item.xpath('PostalOffice')[0].text
        place = item.xpath('Place')[0].text
        zipCode = item.xpath('PostalCode')[0].text
        event['location'] = self.upsert_place(location_origin_id, address, city, place, zipCode)

        if len(keywords) > 0:
            event['keywords'] = keywords

        return event


    def upsert_place(self, origin_id, address, city, place, zipCode):
        result = recur_dict()
        _id = 'osterbotten:{}'.format(origin_id)

        result['id'] = _id
        result['origin_id'] = origin_id
        result['name']['fi'] = place
        result['street_address']['fi'] = address
        result['postal_code'] = zipCode
        result['address_locality']['fi'] = city
        result['publisher'] = self.organization
        result['data_source'] = self.data_source

        self.save_place(result)

        return result

    def getKeyword(self, _id):
        keywords = Keyword.objects.filter(id__exact='%s' % _id).order_by('id')
        keyword = keywords.first()

        return keyword

    def keywordExists(self, _id):
        keywords = Keyword.objects.filter(id__exact='%s' % _id).order_by('id')
        keyword = keywords.first()

        if not keyword:
            return False  
        return True

    def upsert_keyword(self, origin_id, name):
        if not origin_id:
            origin_id = str(uuid.uuid4())
            logger.info("Missing origin id from keyword, using random uuid instead")

        _id = 'osterbotten:{}'.format(origin_id)
        if not self.keywordExists(_id):
            kwargs = {
                'id': _id,
                'data_source_id': self.data_source,
                'name_fi': name,
                'origin_id': origin_id,
                'publisher': self.organization
            }
            Keyword.objects.get_or_create(**kwargs)

        return self.getKeyword(_id)