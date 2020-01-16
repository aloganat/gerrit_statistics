# Description

This script will be used to fetch gerrit statistics. 
It collects the data in csv file for later reference and
draws chart with the gathered data.

## Python packages to be installed:

Python Packages to be installed:
  - yum install python-setuptools
  - easy_install pip3
  - pip3 install pygerrit2
  - pip3 install pandas
  - pip3 install matplotlib

## Installing system_monitor directly Git via pip

             pip3 install --upgrade git+git://github.com/aloganat/gerrit_statistics.git

## Uninstalling system_monitor

             pip3 uninstall gerrit_statistics

## Usage:
  gerrit_statistics -h

    usage: fetch gerrit statistics [-h] {A,B,C,D,E,generate_combined_chart} ...

    Tool for fetching gerrit statistics

    optional arguments:
      -h, --help            show this help message and exit

    Available sub commands:
      {A,B,C,D,E,generate_combined_chart}
                            sub-command help
        A                   collects number of patches that are in open state in
                            given timerange.
        B                   collects number of patches that gets merged in given
                            time range.
        C                   collects number of patches in given time range that
                            needs to be reviewed.
        D                   collects number of patches in given timerange that
                            needs comments to be addressed.
        E                   collects number of patches reviewed and total number
                            of comments given by list of users in given timerange.
        generate_combined_chart
                            Generates combined bar chart for the options A,B,C,D.

## Example:
        gerrit_statistics.py D  --gerrit-url  https://review.gluster.org/ --project-name glusto-tests --start-date 2018-1-1 --end-date 2020-01-15 --csv-output-file stat.csv --chart-output-file chart.png
        gerrit_statistics.py generate_combined_chart  --gerrit-url  https://review.gluster.org/ --project-name glusto-tests --start-date 2019-07-01 --end-date 2020-01-15 --csv-output-file stat.csv --chart-output-file chart.png --choose-options A,B,C,D
