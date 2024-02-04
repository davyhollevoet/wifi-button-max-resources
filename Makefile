HOST=...

# run as `make upload F=project`
upload: $(F).json
	curl -v -n -d @$(F).json http://$(HOST)/api/v1/config

info:
	curl -v -n http://$(HOST)/api/v1/info

config:
	curl -v -n http://$(HOST)/api/v1/config | jq . -

# run as `make check F=project`
check: $(F).json
	jsonschema -i $(F).json schema.json

# run as `make icon-small.bmp F=input.bmp`
%-small.bmp: $(F)
	convert $(F) -monochrome -resize 44x44 -colors 2 BMP3:$@

%-medium.bmp: $(F)
	convert $(F) -monochrome -resize 132x132 -colors 2 BMP3:$@

%-large.bmp: $(F)
	convert $(F) -monochrome -resize 200x200 -colors 2 BMP3:$@

check_code:
	@echo \> Checking code...
	@mypy --exclude venv .

format_code:
	@echo \> Formatting code...
	@black . --exclude "venv"
