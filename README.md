# Graph-visualizer

## Team members
* Nikola Ognjenović, SV51/2022
* Uroš Radukić, SV54/2022
* Danilo Drobnjak SV19/2022
* Filip Vidaković SV42/2022

## Dev project setup
To get started on project development, do the following after cloning the repository:

1. Create a virtual environment for the whole project in a folder called venv:
```shell
  python3 -m venv venv
```

2. Activate the virtual environment:
* On Linux / macOS:
```shell
  source venv/bin/activate
```

* On Windows:
```shell
  .\venv\Scripts\Activate.ps1
```

3. Upgrade pip
```shell
  python -m pip install --upgrade pip
```

4. Install requirements
```shell
  pip install -r requirements.txt
  pip install ./API ./visualizer_platform ./plugins/datasources/json ./plugins/datasources/xml ./plugins/visualizers/simple ./plugins/visualizers/block
```

5. Run webapp
```shell
  cd ./webapp
  python manage.py makemigrations
  python manage.py migrate
  python manage.py runserver
```

## Testing data sources without a UI
After installing packages (step 4), you can test the JSON graph loader without the UI:

```shell
  # uses data/json/test_simple_graph.json by default
  python visualizer_platform/graph/use_cases/print_json_graph.py
  # or specify a custom file
  python visualizer_platform/graph/use_cases/print_json_graph.py data/json/test_simple_graph.json
```

This will output a list of nodes and edges parsed from the JSON file.

Sample JSON files you can try:
- data/json/test_simple_graph.json (very small, simple tree)
- data/json/test_acyclic_tree.json (larger, acyclic hierarchical structure)
- data/json/test_cyclic_graph.json (contains cross-references forming cycles)
- data/json/test_complex_graph.json (mixed structure with arrays, nested objects, and multiple refs)
