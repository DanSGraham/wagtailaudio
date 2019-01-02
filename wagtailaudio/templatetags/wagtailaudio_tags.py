import re

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch
from django.utils.functional import cached_property
import math

register = template.Library()

@register.filter()
def formatSeconds(s):
    hours = math.floor(s / 3600)
    mins = math.floor((s - (hours * 60)) / 60)
    secs = math.floor(s - (mins * 60) - (hours * 3600))
    return "%d:%02d:%02d" % (hours, mins, secs)
