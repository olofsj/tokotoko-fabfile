from setuptools import setup, find_packages

setup(
    name='tokotoko_fabfile',
    version='0.1',
    description='Fabfile for setting up and managing Django projects on Amazon EC2',
    long_description=open('README.md', 'r').read(),
    keywords='django, fabfile, fabric',
    author='Olof Sjöbergh',
    author_email='olofsj at gmail com',
    url='https://github.com/olofsj/tokotoko-fabfile',
    license='BSD',
    package_dir={'tokotoko_fabfile': 'tokotoko_fabfile'},
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    entry_points = {
        'console_scripts': [
            'tokotoko-fabfile-path = tokotoko_fabfile:print_path',
            ],
        }
    scripts=['scripts/tokotoko-fabfile']

)

