#============================================================
# Makefile to build xfiner.app
#
# @file xfinder
# @brief Makefile for building xfinder.py's executable
# @author Noriaki Ando <n-ando@aist.go.jp>
# @copyright Copyright (C) 2020 Noriaki Ando, All right reserved.
#
# This Makefile generate xfinder.py's executable on MacOS X
# How to use:
# make       .... build xfiner.app (exe will be in the "dist")
# make clean .... clean-up generated files
#
#============================================================
all:
	make `uname`

Linux:
	pyinstaller xfinder.py --onefile --noconsole --icon=icons/raspi.icns
	mkdir -p bin
	cp dist/xfinder bin/

Darwin:
	pyinstaller xfinder.py --onefile --noconsole --icon=icons/raspi.icns
	mkdir -p bin
	cp dist/xfinder.app bin/

clean:
	rm -f *~
	rm -f .DS_store
	rm -f xfinder.spec
	rm -rf build dist __pycache__
