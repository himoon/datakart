```shell
python3 -m pip install --upgrade pip build
python3 -m build

python3 -m pip install --upgrade twine
python3 -m twine upload dist/*
```