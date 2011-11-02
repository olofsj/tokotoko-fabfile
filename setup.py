from setuptools import setup, find_packages

setup(
    name='tokotoko-fabfile',
    version='0.1',
    description='Fabfile for setting up and managing Django projects on Amazon EC2',
    long_description=open('README.md', 'm').read(),
    keywords='django, fabfile, fabric',
    author='Olof Sjöbergh',
    author_email='olofsj at gmail com',
    url='https://github.com/olofsj/tokotoko-fabfile',
    license='BSD',
    package_dir={'fabfile': 'fabfile'},
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
)
