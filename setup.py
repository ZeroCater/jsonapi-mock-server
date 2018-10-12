from setuptools import setup, find_packages

install_requires = [
    'django >=1.7, <2',
    'django-cors-headers',
    'djangorestframework',
    'faker',
    'inflection',
    'jsondiff',
    'requests',
    'simplejson',
    'urllib3[secure]',
]

setup(
    name='jsonapi-mock-server',
    description='JSON API mock server',
    version='0.15',
    author='ZeroCater',
    packages=find_packages(),
    install_requires=install_requires,
    licence='MIT',
    url='https://github.com/ZeroCater/jsonapi-mock-server',
    keywords='jsonapi mock server',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
