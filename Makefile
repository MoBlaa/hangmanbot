.PHONY: init run package clean package-win

init:
	python3 -m pip install -r requirements.txt

run:
	python3 __main__.py

package-win:
	python3 -m pip install pyinstaller
	python3 -O -m PyInstaller --onefile __main__.py

package:
	zip -r ../hangmanbot.zip *
	echo '#!/usr/bin/env python' | cat - ../hangmanbot.zip > hangmanbot
	chmod +x ../hangmanbot.zip

fmt:
	python3 -m pip install yapf
	yapf --in-place *.py

clean:
	rm -r build dist
