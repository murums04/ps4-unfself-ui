from pathlib import Path


def pytest_configure(config):
    # pytest creates --basetemp without parents; a fresh checkout has no .work folder.
    Path(config.rootpath, ".work").mkdir(exist_ok=True)
