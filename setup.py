from setuptools import setup

setup(name='gerrit_statistics',
      version='0.1',
      author='Arthy Loganathan',
      author_email='aloganat@redhat.com',
      description=('Tool for fetching gerrit statistics'),
      url='https://github.com/aloganat/gerrit_statistics',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7.5',
        'Topic :: Software Development :: Quality Assurance',
        ],
      packages=['gerrit_statistics'],
      entry_points={
        'console_scripts': [
            'gerrit_statistics = gerrit_statistics.gerrit_statistics:main',
            ]
                    },
      install_requires=['pygerrit2', 'pandas', 'matplotlib']
)
