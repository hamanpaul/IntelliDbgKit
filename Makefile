PYTHON ?= python3

.PHONY: test contract-check ui-poc hlapi-import hlapi-discovery-sample

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

contract-check:
	@fd . /home/paul_chen/IntelliDbgKit/specs/001-debug-loop/contracts -e json -t f | sort | xargs -I{} jq empty "{}"

ui-poc:
	cd /home/paul_chen/IntelliDbgKit/gui/poc && $(PYTHON) -m http.server 8080

hlapi-import:
	$(PYTHON) -m src.cli.commands.hlapi_ingest \
		--source /home/paul_chen/IntelliDbgKit/docs/6.3.0GA_prplware_v403_LLAPI_Test_Report.xlsx \
		--vault /tmp/idk-vault \
		--project IntelliDbgKit

hlapi-discovery-sample:
	printf "Device.WiFi.Radio.1.Channel rw\nDevice.WiFi.SSID.1.Enable read\n" > /tmp/idk-discovery-input.txt
	$(PYTHON) -m src.cli.commands.hlapi_discovery \
		--run-id run-sample \
		--target-id board-01 \
		--input /tmp/idk-discovery-input.txt \
		--output /tmp/idk-discovery-output.json
