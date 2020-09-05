all:
	make `uname`

Darwin:
	pyinstaller xfinder.py --version 1.1 -onefile --noconsole --icon=icons/raspi.icns

clean:
	pyinstaller --clean
	rm -rf xfinder.spec .DS_store build dist __pycache__ *~ 
