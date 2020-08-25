rd /Q /S dist
rd /Q /S build

mkdir dist

copy icons\raspi.ico dist
C:\python27\python.exe setup.py py2exe
"C:\Program Files (x86)\NSIS\makensis.exe" setup.nsi

copy icons\raspi.ico dist
C:\python27\python.exe setup.py py2exe
"C:\Program Files (x86)\NSIS\makensis.exe" setup.nsi
