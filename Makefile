.PHONY: check start test

start:
	./scripts/dev.sh

test:
	python3 -m pytest
	npm --prefix apps/web test

check:
	python3 -m compileall apps/api/app tests apps/api/smoke_routes.py
	python3 -m pytest -q
	npm --prefix apps/web test
	npm run build
