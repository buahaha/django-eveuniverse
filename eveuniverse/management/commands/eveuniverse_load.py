from django.core.management.base import BaseCommand
from allianceauth.services.hooks import get_extension_logger

from ... import __title__
from ...providers import esi
from ...tasks import load_eve_entity
from ...utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def get_input(text):
    """wrapped input to enable unit testing / patching"""
    return input(text)


class Command(BaseCommand):
    help = 'Updates Eve Online SDE data'
    
    def _load_models(self):
        # self._load_parent('EveCategory', 'get_universe_categories')
        self._load_parent('EveRegion', 'get_universe_regions')
    
    def _load_parent(self, model_name, eve_method):
        all_ids = getattr(esi.client.Universe, eve_method)().results()
        counter = 0
        for eve_id in all_ids:
            progress = int(counter / len(all_ids) * 100)
            self.stdout.write(
                f'Loading {model_name} with children '
                f'for ID {eve_id} ({progress}% complete)'
            )
            load_eve_entity.delay(model_name, eve_id)
                
    def handle(self, *args, **options):
        self.stdout.write(
            'This command will load the complete Eve Universe from ESI and '
            'store it locally. This process can take a long time to complete.'
        )
        user_input = get_input('Are you sure you want to proceed? (Y/n)?')
        if user_input == 'Y':
            self.stdout.write('Starting update. Please stand by.')
            self._load_models()
            self.stdout.write('Update completed!')
        else:
            self.stdout.write('Aborted')
