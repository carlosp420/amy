import os
import re
import yaml
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from workshops.models import Event

URL_PATTERN = re.compile(r'^https?://(.+)\.github\.io/([^/]+)/?$')

class Command(BaseCommand):
    args = '/path/to/site'
    help = 'Report inconsistencies in workshop URLs.'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Usage: check_workshop_urls /path/to/site')

        path_to_site = args[0]
        workshops_file = os.path.join(path_to_site, 'config', 'workshops.yml')
        archive_file = os.path.join(path_to_site, 'config', 'archived.yml')
        with open(workshops_file, 'r') as reader:
            workshops = [self.normalize(x) for x in yaml.load(reader)]
        with open(archive_file, 'r') as reader:
            archives = [self.normalize(x['url']) for x in yaml.load(reader)]

        self.check_overlap(workshops, archives)
        self.check_urls(workshops + archives)

    def check_overlap(self, left, right):
        joint = set(left).intersection(set(right))
        if joint:
            joint = list(joint)
            joint = '\n'.join(joint.sort())
            raise CommandError('Workshop URLs present in both files: {0}'.format(joint))

    def check_urls(self, urls):
        for u in urls:
            try:
                Event.objects.get(url=u)
            except ObjectDoesNotExist:
                print('"{0}" in configuration but not in database'.format(u))

        urls = set(urls)
        for e in Event.objects.all():
            if e.url and (e.url not in urls):
                print('"{0}" in database but not in configuration'.format(e.url))

    def normalize(self, url):
        m = URL_PATTERN.match(url)
        if m:
            url = 'https://github.com/{0}/{1}'.format(m.group(1), m.group(2))
        return url
