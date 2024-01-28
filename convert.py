import base64
import json
import sys
from typing import Dict, Any, List, Set

import yaml
from jsonschema import validate

screen_names: Set[Any]


def check_action(action: Dict[str, Any]) -> None:
    if "screen" in action:
        if action["screen"] not in screen_names:
            print(f"Unknown screen {action['screen']}")


def build_actions(screen: Dict[str, Any]) -> None:
    for j, tile in enumerate(screen["tiles"], start=1):
        actions = tile.pop("actions", [])
        for action in actions:
            action["trigger"] = f"btn{j}"
            screen["actions"].append(action)


def split_screen_3N(screen: Dict[str, Any]) -> List[Dict[str, Any]]:
    screen["layout"] = "4-ico-text"

    all_tiles = screen["tiles"]
    parts = (len(all_tiles) + 2) // 3
    # append empty tiles at the end to get full screen
    all_tiles += [{"txt": ""}] * (parts * 3 - len(all_tiles))

    # we'll repeat these actions for every screen generated
    base_actions = screen.pop("actions", [])

    screen["tiles"] = all_tiles[0:3]
    del all_tiles[0:3]
    screen["tiles"].append({"ico": "skip"})

    screen["actions"] = [
        {"trigger": "btn4", "scheme": "1x", "screen": f"{screen['name']}-1"}
    ]
    screen["actions"] += base_actions
    build_actions(screen)

    screens = [screen]

    for i in range(1, parts):
        tiles = all_tiles[0:3]
        del all_tiles[0:3]

        tiles.append({"ico": "skip"})

        extra_screen = {
            "dispName": f"{screen['dispName']} ({i})",
            "name": f"{screen['name']}-{i}",
            "layout": "4-ico-text",
            "tiles": tiles,
            "actions": [
                {
                    "trigger": "btn4",
                    "scheme": "1x",
                    "screen": (
                        f"{screen['name']}-{i + 1}"
                        if len(all_tiles)
                        else screen["name"]
                    ),
                }
            ],
        }

        extra_screen["actions"] += base_actions
        build_actions(extra_screen)

        screens.append(extra_screen)

    return screens


if __name__ == "__main__":
    with open("schema.json", "r") as f:
        schema = json.load(f)

    fn = sys.argv[1]
    with open(fn, "r") as f:
        data = yaml.safe_load(f)

    ha_data = data.pop("ha", {})
    ha_config = ha_data.get("config", {})

    # convert custom screens into something the device understands
    for i in reversed(range(len(data["screens"]))):
        if data["screens"][i]["layout"] == "3N-ico-text":
            split = split_screen_3N(data["screens"][i])
            data["screens"] = data["screens"][:i] + split + data["screens"][i + 1:]

    # list of defined screen names, to check references
    screen_names = {s["name"] for s in data["screens"]}

    for screen in data["screens"]:
        for action in screen.get("actions", []):
            if "ha" in action:
                val = action.pop("ha")
                act = val.pop("action")
                val.update(
                    {
                        "method": "POST",
                        "payload": ha_config['payload'].format(action=act),
                        "url": ha_config["url"],
                    }
                )
                action["http"] = val

                if act not in ha_data["actions"]:
                    print(f"Undefined action {act}")

            check_action(action)
            if "http" in action and "ondone" in action["http"]:
                if "then" in action["http"]["ondone"]:
                    check_action(action["http"]["ondone"]["then"])
                if "else" in action["http"]["ondone"]:
                    check_action(action["http"]["ondone"]["else"])

    if "files" in data and "bmp" in data["files"]:
        for bmp in data["files"]["bmp"]:
            if "ref" in bmp:
                fn = bmp.pop("ref")
                with open(fn, "rb") as fb:
                    bmp["data"] = base64.b64encode(fb.read()).decode("ascii")

    validate(instance=data, schema=schema)

    with open("output.json", "w") as json_file:
        json.dump(data, json_file)

    if ha_data.get("actions", {}):
        ha_actions = []
        for name, content in ha_data.get("actions", {}).items():
            act = {
                "if": [
                    {
                        "condition": "template",
                        "value_template": f"{{{{ trigger.payload_json.action == '{name}' }}}}",
                    }
                ],
                "then": content,
            }
            ha_actions.append(act)

        with open("output.yml", "w") as yml_file:
            yaml.dump(ha_actions, yml_file)
