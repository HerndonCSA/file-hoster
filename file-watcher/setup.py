from setuptools import setup

APP = ['file-watcher/app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt5'],
    "iconfile": "file-watcher/icon.icns",
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='Quick Embed',
)
