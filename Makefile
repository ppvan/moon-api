dev:
	uvicorn --app-dir src  main:app --reload

run:
	uvicorn --app-dir src main:app --host 0.0.0.0 --port 8001