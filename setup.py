from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in migration/__init__.py
from migration import __version__ as version

setup(
	name='migration',
	version=version,
	description='Migration',
	author='Firsterp',
	author_email='support@firsterp.in',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
