REM ============================================================
REM Building xfinder.exe
REM
REM @file build.cmd
REM @brief xfinder executable build batchfile
REM @author Noriaki Ando <Noriaki.Ando@gmail.com>
REM @copyright Copyright (C) 2020 Noriaki Ando, All right reserved.
REM
REM This batch file generate xfinder.py's executable xfinder.exe
REM How to use:
REM build.cmd       .... build xfiner.exe (exe will be in the "dist")
REM build.cmd       .... clean-up generated files
REM ============================================================

REM Always clean generated files
del /S /Q __pycache__
rd /S /Q __pycache__
del /S /Q build
rd /S /Q build
del /S /Q dist
rd /S /Q dist
del /S /Q xfinder.spec

REM build target goes to END
if x%1 == xclean goto END

REM Building exe
pyinstaller xfinder.py --onefile --noconsole --icon=".\\icons\\raspi.ico" --add-data=".\\icons\\raspi.ico;.\\icons"

:END
