from setuptools import setup, find_packages
import os


version = '1.0~dev'
ldesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()


setup(name='restdns-bind',
      version=version,
      description='A Bind9 zonefile generator for Restdns',
      long_description=ldesc,
      classifiers=['License :: OSI Approved :: MIT License'],
      keywords='bind restdns rest',
      author='Antoine Millet',
      author_email='antoine@inaps.org',
      url='https://github.com/NaPs/restdns-bind',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages=['restdns', 'restdns.clients'],
      scripts=['restdns-bind'],
      include_package_data=True,
      zip_safe=True,
      install_requires=['dnspython', 'requests'])
