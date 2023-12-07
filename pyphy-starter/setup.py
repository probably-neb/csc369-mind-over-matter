from setuptools import setup, find_packages


setup(
    name='pyphy',
    version='1.0.4',
    license='MIT',
    author="Sixing Huang",
    author_email='dgg321982@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/dgg32/pyphy',
    keywords='NCBI taxonomy for python',
    package_data={'': ['*.config']}
)