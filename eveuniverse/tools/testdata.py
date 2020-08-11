from copy import deepcopy
from collections import OrderedDict, namedtuple
import logging
import json
from typing import Dict

from django.core.serializers.json import DjangoJSONEncoder

from eveuniverse.models import EveUniverseEntityModel, EveSolarSystem, EveStargate

from .. import __title__
from ..utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


ModelSpec = namedtuple("ModelSpec", ["ids", "include_children"])


def create_testdata(
    spec: Dict[EveUniverseEntityModel, ModelSpec], filepath: str
) -> None:
    """Loads eve data from ESI as defined by spec and dumps it to file as JSON
    
    Args:
        spec: Specification of which Eve objects to load
        filepath: absolute path of where to store the resulting JSON file
    """

    # clear database
    for MyModel in EveUniverseEntityModel.all_models():
        if MyModel.__name__ != "EveUnit":
            MyModel.objects.all().delete()

    # load data per definition
    for model_name, model_spec in spec.items():
        MyModel = EveUniverseEntityModel.get_model_class(model_name)
        for id in model_spec.ids:
            MyModel.objects.get_or_create_esi(
                id=id,
                include_children=model_spec.include_children,
                wait_for_children=True,
            )

    # dump all data into file
    data = OrderedDict()
    for MyModel in EveUniverseEntityModel.all_models():
        if MyModel.objects.count() > 0 and MyModel.__name__ != "EveUnit":
            logger.info(
                "Collecting %d rows for %s", MyModel.objects.count(), MyModel.__name__
            )
            my_data = list(MyModel.objects.all().values())
            for row in my_data:
                del row["last_updated"]

            data[MyModel.__name__] = my_data

    logger.info("Writing testdata to %s", filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=DjangoJSONEncoder, indent=4, sort_keys=True)


def load_testdata_from_dict(testdata: dict) -> None:
    """creates eve objects in the database from testdata dump given as dict
    
    Args:
        testdata: The dict containing the testdata as created by `create_testdata()`
    """
    for MyModel in EveUniverseEntityModel.all_models():
        model_name = MyModel.__name__
        if model_name in testdata:
            if MyModel.__name__ == "EveStargate":
                for _ in range(2):
                    for obj in deepcopy(testdata[model_name]):
                        try:
                            EveStargate.objects.get(
                                id=obj["destination_eve_stargate_id"]
                            )
                        except EveStargate.DoesNotExist:
                            del obj["destination_eve_stargate_id"]
                            obj["destination_eve_stargate"] = None

                        try:
                            EveSolarSystem.objects.get(
                                id=obj["destination_eve_solar_system_id"]
                            )
                        except EveSolarSystem.DoesNotExist:
                            del obj["destination_eve_solar_system_id"]
                            obj["destination_eve_solar_system"] = None

                        id = obj["id"]
                        del obj["id"]
                        MyModel.objects.update_or_create(id=id, defaults=obj)
            else:
                for obj in testdata[model_name]:
                    MyModel.objects.create(**obj)


def load_testdata_from_file(filepath: str) -> None:
    """creates eve objects in the database from testdata dump given as JSON file   
    
    Args:
        filepath: Absolute path to the JSON file containing the testdata created by `create_testdata()`
    """
    with open(filepath, "r", encoding="utf-8") as f:
        testdata = json.load(f)

    load_testdata_from_dict(testdata)
