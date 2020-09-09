all: img dmg

img:
	tiffutil -cathidpicheck xfinder_800x400.tif xfinder_1600x800.tif -out backImage.tiff

dmg:
	rm -f xfinder_v1.1.dmg
	create-dmg \
		--volname "Xfinder Installer" \
		--volicon "../../icons/raspi.icns" \
		--background "backImage.tiff" \
		--window-pos 200 120 \
		--window-size 800 440 \
		--icon-size 100 \
		--icon "xfinder.app" 200 190 \
		--hide-extension "xfinder.app" \
		--app-drop-link 600 185 \
		"xfinder_v1.1.dmg" \
		"../../bin/xfinder.app/"

clean:
	rm -f .DS_store
	rm -f backImage.tiff
