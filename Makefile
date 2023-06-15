build:
	( \
	python3 -m venv venv; \
	source venv/bin/activate; \
	pip3 install -r requirements.txt; \
	)

run:
	python3 main.py -d ./ctg_files -p 8

visualize:
	python3 main.py -d ./ctg_files -p 8 -visualize
