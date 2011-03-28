# -*- coding:utf8 -*-

from setuptools import setup, find_packages

setup(
    name='django-skypehub-earthquake',
    version='1.0.0',
    description='An earthquake notifier built on django-skypehub',
    author='Moriyoshi Koizumi',
    url='http://bitbucket.org/IanLewis/django-skypehub-earthquake/',
    packages = find_packages(),
    license='BSD',
    keywords='django skype webapp',
    install_requires = [
        'Django>=1.2',
        'django-skypehub>=0.2.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
