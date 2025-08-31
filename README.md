# Graph-visualizer

## Team members
* Nikola Ognjenović, SV51/2022
* Uroš Radukić, SV54/2022
* Danilo Drobnjak SV19/2022

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
```

5. Run webapp
```shell
    python manage.py makemigrations
    python manage.py migrate
    python manage.py runserver
```