from setuptools import setup, find_packages

requires = [
    'python-telegram-bot',
    'PyCryptoDome',
    'python-otrs @ git+https://github.com/ewsterrenburg/python-otrs.git@4d634a7c8ca08ab04583c29997c75bf2550bdc2a'
]

setup(
    name='work assistant',
    version='0.1',
    description='telegram bot for simplifying some work processes',
    classifiers=[
        'Programming Language :: Python',
    ],
    author='atronah',
    author_email='atronah.ds@gmail.com',
    keywords='python telegram bot gmail otrs redmine',
    packages=find_packages(),
    install_requires=requires,
    dependency_links=[
        'git+https://github.com/ewsterrenburg/python-otrs.git@master#egg=python-otrs'
    ],
)