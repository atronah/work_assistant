from setuptools import setup, find_packages

requires = [
    'python-telegram-bot',
    'pyyaml',
    'google-api-python-client',
    'google-auth-httplib2',
    'google-auth-oauthlib',
    'python-redmine',
    'python-otrs @ git+https://github.com/ewsterrenburg/python-otrs.git@4d634a7c8ca08ab04583c29997c75bf2550bdc2a'
]

setup(
    name='work_assistant',
    version='0.1',
    description='telegram bot for simplifying some work processes',
    classifiers=[
        'Programming Language :: Python',
    ],
    author='atronah',
    author_email='atronah.ds@gmail.com',
    keywords='python telegram bot gmail otrs redmine',
    # using a package folder with the different name than the package
    # for academic purposes (as example)
    package_dir={'': 'src'},
    # manual specifying package which is in folder with different name
    packages=['telegram_bot'] + find_packages(),
    entry_points={'console_scripts': [
        'work_assistant_bot = telegram_bot.bot:main',
    ]},
    dependency_links=[
        'git+https://github.com/ewsterrenburg/python-otrs.git@master#egg=python-otrs-0'
    ],
    install_requires=requires,
)