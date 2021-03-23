.PHONY: init run package clean

init:
	python3 -m pip install -r requirements.txt

run:
	python3 hangmanbot.py

package:
	python3 -m pip install pyinstaller
	python3 -O -m PyInstaller --onefile hangmanbot.py

fmt:
	python3 -m pip install yapf
	yapf --in-place *.py

clean:
	rm -r build dist