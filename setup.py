from setuptools import setup

setup(
    name='gitfucktime',
    version='0.1.0',
    py_modules=['gitfucktime'],
    install_requires=[
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'gitfucktime=gitfucktime:main',
        ],
    },
)
