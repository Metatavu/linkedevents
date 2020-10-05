import pytest
import pytz
import re
import dateutil.parser

from pprint import pprint

from datetime import datetime, timedelta
from html.parser import HTMLParser
from events.importer.osterbotten import OsterbottenImporter
from unittest.mock import MagicMock
from lxml import etree
from urllib.parse import urlparse, parse_qs

from .utils import get
from .utils import versioned_reverse as reverse


# === util methods ===


def get_event(api_client, id):
    detail_url = reverse('event-detail', version='v1', kwargs={'pk': id, }) + "?include=location,keywords"
    response = get(api_client, detail_url, data=None)
    return response.data


def assert_imported_osterbotten_event(locale, api_event, osterbotten_event):
    timezone = pytz.timezone('Europe/Helsinki')

    assert get_osterbotten_event_id(osterbotten_event) == api_event["id"]
    assert dateutil.parser.parse(osterbotten_event.xpath('Start')[0].text).astimezone(timezone) == dateutil.parser.parse(api_event["start_time"])
    assert dateutil.parser.parse(osterbotten_event.xpath('End')[0].text).astimezone(timezone) == dateutil.parser.parse(api_event["end_time"])

    assert osterbotten_event.xpath('Link')[0].text == api_event["info_url"][locale]
    assert osterbotten_event.xpath('Title')[0].text == api_event["name"][locale]
    assert osterbotten_event.xpath('EventText')[0].text == api_event["description"][locale]
    assert osterbotten_event.xpath('EventTextShort')[0].text == api_event["short_description"][locale]

    assert osterbotten_event.xpath('Municipality')[0].text == api_event["location"]["address_locality"][locale]
    assert osterbotten_event.xpath('PostalAddress')[0].text == api_event["location"]["street_address"][locale]
    assert osterbotten_event.xpath('PostalCode')[0].text == api_event["location"]["postal_code"]

    is_free = osterbotten_event.xpath('PriceType')[0].text  == "Free"
    assert is_free == api_event["offers"][0]["is_free"]
    assert osterbotten_event.xpath('PriceHidden')[0].text == api_event["offers"][0]["price"][locale]
    assert osterbotten_event.xpath('PriceText')[0].text == api_event["offers"][0]["description"][locale]

    categories = osterbotten_event.xpath('Categories')[0]
    for category in categories:
      categoryText = category.xpath('Name')[0].text
      categoryId = "osterbotten:{}".format(categoryText)
      api_keyword = next(keyword for keyword in api_event["keywords"] if keyword["id"] == categoryId)
      assert categoryText == api_keyword["name"][locale]


def get_osterbotten_event_id(osterbotten_event):
  return "osterbotten:{}".format(osterbotten_event.xpath('ID')[0].text)


def read_osterbotten_event(index):
  return open("events/tests/static/osterbotten/event_{}.xml".format(index + 1), "r").read()


@pytest.fixture
def osterbotten_event_1():
  return etree.fromstring(read_osterbotten_event(0))


@pytest.fixture
def osterbotten_event_2():
  return etree.fromstring(read_osterbotten_event(1))


def mock_items_1_from_url(url):
  query = parse_qs(urlparse(url).query)
  start = query.get("Start")[0]
  locale = query.get("Locale")[0]

  if locale == "fi_FI" and start == "0":
    events = [read_osterbotten_event(0)]
  else:
    events = []

  events_template = open("events/tests/static/osterbotten/events.xml", "r").read()
    
  return etree.fromstring(events_template.replace("___EVENTS___", ' '.join(map(str, events)))).xpath('Events/Event')


def mock_items_2_from_url(url):
  query = parse_qs(urlparse(url).query)
  start = query.get("Start")[0]
  locale = query.get("Locale")[0]

  if locale == "fi_FI" and start == "0":
    events = [read_osterbotten_event(0), read_osterbotten_event(1)]
  else:
    events = []

  events_template = open("events/tests/static/osterbotten/events.xml", "r").read()
    
  return etree.fromstring(events_template.replace("___EVENTS___", ' '.join(map(str, events)))).xpath('Events/Event')


def mock_municipalities_from_url(url):
  response_file = open("events/tests/static/osterbotten/municipalities.xml", "r")
  return etree.fromstring(response_file.read()).xpath('Municipalities/Municipality')


# === tests ===


@pytest.mark.django_db
def test_import_osterbotten_events(api_client, osterbotten_event_1, osterbotten_event_2):
    importer = OsterbottenImporter({'verbosity': True, 'cached': False})
    importer.setup()
    importer.items_from_url = MagicMock(side_effect=mock_items_2_from_url)
    importer.municipalities_from_url = MagicMock(side_effect=mock_municipalities_from_url)
    importer.import_events()

    assert_imported_osterbotten_event("fi", get_event(api_client, get_osterbotten_event_id(osterbotten_event_1)), osterbotten_event_1)
    assert_imported_osterbotten_event("fi", get_event(api_client, get_osterbotten_event_id(osterbotten_event_2)), osterbotten_event_2)