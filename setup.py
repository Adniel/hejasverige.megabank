from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='hejasverige.megabank',
      version=version,
      description="Heja Sverige MegaBank integration",
      long_description=open("README.md").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
                   "Framework :: Plone",
                   "Programming Language :: Python",
                   ],
      keywords='',
      author='',
      author_email='daniel.grindelid@gmail.com',
      url='http://swedwise.com/megabank/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['hejasverige'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Plone',
          'collective.beaker',
          'requests',
          'hejasverige.content',
          'plone.app.registry',
          'plone.app.z3cform',

          # -*- Extra requirements: -*-
      ],
      extras_require={
        'test': ['plone.app.testing',]
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
