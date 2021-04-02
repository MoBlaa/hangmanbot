.PHONY: init run package clean package-win

init:
	python3 -m pip install -r requirements.txt

run: init
	python3 hangmanbot/__main__.py

package-win:
	python3 -m pip install pyinstaller
	python3 -O -m PyInstaller --onefile hangmanbot/__main__.py

package:
	mkdir -p dist/exec
	cp -r hangmanbot/* dist/exec/
	python3 -m pip install -r requirements.txt --target dist/exec/
	cd dist/exec && zip -r ../hangmanbot.zip .
	echo "#!/usr/bin/env python3" | cat - dist/hangmanbot.zip > dist/hangmanbot
	chmod +x dist/hangmanbot

clean:
	rm -r build dist
