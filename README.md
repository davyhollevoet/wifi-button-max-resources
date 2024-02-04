# myStrom WiFi Button Max resources

This repository contains some files and scripts that can be useful for user of [myStrom WiFi Button Max devices](https://mystrom.ch/wifi-button-max/) that run the [Button Max Custom Firmware](https://mystrom.ch/support/mystrom-button-max-tool/).

**Disclaimer**: I have no affiliation with myStrom AG. Use the resources in this repo on your own risk.

## Intended audience
myStrom provides the [myStrom Button Max Tool](https://mystrom.ch/support/mystrom-button-max-tool/) to configure the devices, but there is no Linux version. It also seems like the tool (still in beta, mind you) does not support all features of the device, like `ondone` actions and `on-enter` triggers.

## Content

### schema.json

A JSON Schema that can be used to check whether the config you want to upload to the device, is in fact valid. The schema has been constructed from a few files produced by the Button Max Tool and extended by looking at the firmware.

```shell
jsonschema schema.json -i my_screens.json
```

#### Extra features

The following features are not supported (yet?) by the [myStrom Button Max Tool](https://mystrom.ch/support/mystrom-button-max-tool/), but they are implemented in firmware 1.1.10 on the device.

* `http/ondone` Which screen to switch to after an HTTP action has completed (`then`) or failed (`else`).
  ```json
  "actions": [
    {
      "http": {
        "...": "..."
        "ondone": {
          "then": {
            "screen": "call_ok"
          },
          "else": {
            "screen": "call_failed"
          }
        }
      },
      "scheme": "long",
      "trigger": "btn1"
    }
  ]
  ```
* `on-enter` Perform an action when a screen is entered
  ```json
  "actions": [
    {
      "trigger": "on-enter",
      "http": {
        ...
      }
    }
  ]
  ```

#### More extra features?

* The firmware hints at a feature that blinks the led a number of times in a specified color and at a given speed (`color`, `times`, `speed`). I've not been able to get that to work.
* There is also mention of `while` and `@current`, which may point to extra features.

### icons

A list of icons embedded in the device (may be incomplete).

### convert.py

```shell
python convert.py my_screens.yml
# writes to output.json
```

A small script to convert a YAML config file into a proper JSON config file (I just really prefer working in YAML). It also adds some convenient things:

* reference a .bmp file instead of embedding it:
  ```yaml
  files:
    bmp:
      - name: my_icon
        ref: my_icon_large.bmp
  ```
* layout `3N-ico-text`
  
  This lets you define a screen with N>4 tiles, that is then converted in a set of screens with each 3 tiles and one ">>" tile bottom right. See `icons.yml` for an example generated from the list of icons.
  
  Remark: the actions have to be defined *in* the tiles. If would be too difficult to manage them otherwise.
  
  TODO: a `4N-ico-text` without the ">>" tile?
  
* `ha` actions
  
  This feature provides a shorthand notation for URL POST actions to a fixed endpoint such as Home Assistant. It also generates a (trigger) script that can be used in Home Assistant.

  ```yaml
  #...
  - actions:
    - trigger: btn1
      scheme: 1x
      ha:
        action: some_action
  #...
  ha:
    config:
      url: http://some_server/some_path
      payload: "some_param=some_value&action={action}"
  actions:
    some_action:
      - service: light.toggle
        target:
          entity_id: light.some_light
  ```
  
  is converted into
  
  ```json
  "actions": [
    {
      "trigger": "btn1",
      "scheme": "1x",
      "http": {
        "method": "POST",
        "payload": "some_param=some_value&action=some_action",
        "url": "http://some_server/some_path"
      }
    }
  ]
  ```
  
  and
  
  ```yaml
  - if:
    - condition: template
      value_template: '{{ trigger.payload_json.action == ''some_action'' }}'
    then:
    - service: light.toggle
      target:
        entity_id: light.some_light
  ```
