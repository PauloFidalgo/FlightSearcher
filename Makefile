fmt:
	uv run ruff format
	uv run ruff check --fix --unsafe-fixes
	uv run mypy .

web:
	uv run streamlit run flight_viewer.py