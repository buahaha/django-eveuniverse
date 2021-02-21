from pathlib import Path
import json


def _load_sde_data() -> dict:
    esi_data_path = Path(__file__).parent / "sde_data.json"
    with esi_data_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


sde_data = _load_sde_data()
