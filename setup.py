import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


packages = []
package_dir = "dbbackup"
for dirpath, dirnames, filenames in os.walk(package_dir):
    # ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith("."):
            del dirnames[i]
    if "__init__.py" in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)


setup(name='django-dbbackup',
    version='0.3',
    description='Django Dropbox Backup',
    long_description=read('README.txt'),
    author='Michael Shepanski',
    license='BSD',
    url='http://bitbucket.org/mjs7231/django-dbbackup',
    keywords = ['django','dropbox','database','backup'],
    packages=packages)