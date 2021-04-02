.PHONY: init run package clean package-win

init:
	python3 -m pip install -r requirements.txt --target hangmanbot

run:
	python3 hangmanbot/__main__.py

package-win:
	python3 -m pip install pyinstaller
	python3 -O -m PyInstaller --onefile hangmanbot/__main__.py

package: init
	python3 -m pip install zipapp
	python -m zipapp -p "/usr/bin/env python3" hangmanbot

clean:
	rm -r build dist
