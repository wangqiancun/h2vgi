try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Vehicle to grid simulator',
    'author': 'Samveg Saxena, Jonathan Coignard',
    'author_email': 'jcoignard@lbl.gov',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['h2vgi', 'h2vgi.driving', 'h2vgi.charging',
                 'h2vgi.post_simulation', 'h2vgi.driving.drivecycle'],
    'name': 'h2vgi',
    'package_data': {'': ['*.mat']},  # Add the drivecycle matlab data
    'include_package_data': True,
}

setup(**config)
