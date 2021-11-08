from setuptools import setup, find_packages

setup(
    name='enerthon_model',
    url='https://github.com/rebaseenergy/enerthon-project',
    packages=find_packages(exclude=["*tests*"]),
    install_requires=['numpy', 'pyomo==5.7.3'],
    include_package_data=True,
    version='0.0.1',
    license='',
    description='Enerthon model',
    long_description=open('README.md').read(),
)
