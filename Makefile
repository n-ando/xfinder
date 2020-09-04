all:
	make `uname`
	
Darwin:
	pyinstaller xfinder.py --onefile --noconsole --icon=icons/raspi.icns

clean:
	rm -rf xfinder.spec .DS_store build dist __pycache__ *~ 
