# $Id: Makefile 3479 2012-04-25 20:22:10Z jeffk $
#
# Authors:     Jeff Klingner
# Maintainers: Jeff Klingner
# Copyright:   2011, Benetech, GPL v2 or later
# ============================================

source_files := $(wildcard ../src/*.py)

.PHONY: all clean

all: dist/Martus\ Data\ Summarizer.zip

clean:
	rm -rf build/ dist/

user_guide = Summarizer-user-guide-v1.0.pdf

dist/Martus\ Data\ Summarizer.zip: \
		dist/Martus\ Data\ Summarizer.app \
		../doc/$(user_guide)
	cp ../doc/$(user_guide) dist/
	cd dist; zip -r "$(notdir $@)" "$(notdir $<)" $(user_guide); cd ..
	rm -r dist/$(user_guide)
	rm -r "$<"

dist/Martus\ Data\ Summarizer.app: setup.py martus.icns $(source_files)
	python setup.py py2app
