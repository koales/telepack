# build script

python -n venv venv
source venv/Scripts/activate

python -m pip install --upgrade pip
pip install --upgrade build wheel setuptools twine

python -m build

# Upload to test PyPI
python -m twine upload --verbose --repository testpypi dist/*

# Upload to production PyPI
# python -m twine upload --non-interactive dist/*
