from pathlib import Path
import json


def _load_sde_data() -> dict:
    esi_data_path = Path(__file__).parent / "sde_data.json"
    with esi_data_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


sde_data = _load_sde_data()


def type_materials_cache_content():
    type_material_data_all = dict()
    for row in sde_data["type_materials"]:
        type_id = row["typeID"]
        if type_id not in type_material_data_all:
            type_material_data_all[type_id] = list()
        type_material_data_all[type_id].append(row)
    return type_material_data_all
