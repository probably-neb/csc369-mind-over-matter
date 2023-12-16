# MIND OVER MATTER

### PACKAGE USAGE

1. clone the repo

2. In the root directory either install the necessary requirements like so

```
pip install -r requirements.txt
```

After setting up a virtual environment of your choosing of course.

Afterwords the options for the program may be observed like so

```
python main.py --help
```

All files passed to the package using the `--files` flag must be in json format.

Alternatively, a neo4j instance and the package can be run with the following command

```
docker compose build && docker compose up
```
