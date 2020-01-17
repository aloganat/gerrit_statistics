#!/usr/bin/env python

import argparse
import logging
import sys
import calendar
import csv
from requests.exceptions import RequestException
from pygerrit2 import GerritRestAPI
import pandas as pd
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
import urllib.parse
from datetime import timedelta

def fetch_gerrit_statistics(args):
    """
    """
    level = logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=level)

    auth = None

    rest = GerritRestAPI(url=args.gerrit_url, auth=auth)

    try:

        st_str = args.status
        st_list = st_str.split(',')
        from datetime import datetime as dt
        #args.start_date = str((dt.strptime(args.start_date, "%Y-%m-%d") - timedelta(days=1)).date())
        args.end_date = str((dt.strptime(args.end_date, "%Y-%m-%d") + timedelta(days=1)).date())
        tmp_list = []
        for index_o,st_item in enumerate(st_list):
            query = ["project:"+args.project_name]
            if st_item == "pendingreview" or st_item == "need_to_address_comments":
                query += ""
            else:    
                query += ["status:"+st_item]
            if index_o == 0:
                tmp_list.append(["Month", "Status:"+st_item])
            else:
                tmp_list[0].append("Status:"+st_item)
            s_month = int(args.start_date.split('-')[1])
            e_month = int(args.end_date.split('-')[1])
            start_month = (calendar.month_name[int(args.start_date.split('-')[1])])
            start_year = int(args.start_date.split('-')[0])
            end_month = (calendar.month_name[int(args.end_date.split('-')[1])])
            end_year = int(args.end_date.split('-')[0])
            month_list = []
            if start_month == end_month and start_year == end_year:
                query += ["after:"+args.start_date]
                query += ["until:"+args.end_date]
                month_list.append(start_month)
                if st_item == "pendingreview":
                    cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' is:open (label:Verified=ok AND NOT label:Code-Review-2 AND NOT label:Code-Review-1)')
                elif st_item == "need_to_address_comments":
                    cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' status:open  (label:Code-review-1 OR label:Code-review-2)')
                else:
                    cmd = "/changes/?q=%s" % "%20".join(query)
                changes = rest.get(cmd)
                count = len(changes)
                for i in month_list:
                    if index_o == 0:
                        tmp_list.append([i, count])
                    else:
                        for inde,chk in enumerate(tmp_list):
                            if i in chk:
                                tmp_list[inde].append(count)

            else:

                sd = dt.strptime(args.start_date, "%Y-%m-%d") 
                ed = dt.strptime(args.end_date, "%Y-%m-%d") 

                lst = [dt.strptime('%2.2d-%d' % (y, m), '%Y-%m').strftime('%B-%Y') \
                       for y in range(sd.year, ed.year+1) \
                       for m in range(sd.month if y==sd.year else 1, ed.month+1 if y == ed.year else 13)]
                for month in calendar.month_name[s_month:e_month+1]:
                    month_list.append(month)
                mon_num = len(lst)
                for index,mont in enumerate(lst):
                    mon = mont.split('-')[0]
                    yr = mont.split('-')[1]
                    if index == 0:
                        query += ["after:"+args.start_date]
                        day = calendar.monthrange(start_year, int(list(calendar.month_name).index(mon)))[1]
                        query += ["until:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)]
                    elif index == mon_num-1:
                        query = [i for i in query if (('until' not in i) and ('after' not in i)) ]
                        query += ["after:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-1"]
                        query += ["until:"+args.end_date]
                    else:
                        query = [i for i in query if (('until' not in i) and ('after' not in i)) ]
                        day = calendar.monthrange(start_year, int(list(calendar.month_name).index(mon)))[1]
                        query += ["after:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-1"]
                        query += ["until:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)]
                    if st_item == "pendingreview":
                        cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' is:open (label:Verified=ok AND NOT label:Code-Review-2 AND NOT label:Code-Review-1)')
                    elif st_item == "need_to_address_comments":
                        cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' status:open  (label:Code-review-1 OR label:Code-review-2)')
                    else:
                        cmd = "/changes/?q=%s" % "%20".join(query)

                    changes = rest.get(cmd)
                    count = len(changes)
                    mon=mon+"-"+str(yr)
                    if index_o == 0:
                        tmp_list.append([mon, count])
                    else:
                        for inde,chk in enumerate(tmp_list):
                            if mon in chk:
                                tmp_list[inde].append(count)

            with open(args.csv_output_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(tmp_list)


        df = pd.read_csv(args.csv_output_file,sep=",")

        ax=df.plot.bar(x = tmp_list[0][0], y = tmp_list[0][1:], figsize=(15,15))
        for p in ax.patches:
            ax.annotate(str(p.get_height()), (p.get_x() * 1.005, p.get_height() * 1.005))
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        ax.set_ylabel("Number of patches")
        plt.savefig(args.chart_output_file)

    except RequestException as err:
        logging.error("Error: %s", str(err))


def fetch_gerrit_statistics_A(args):
    """
    """
    args.status = "open"
    fetch_gerrit_statistics(args)

def fetch_gerrit_statistics_B(args):
    """
    """
    args.status = "merged"
    fetch_gerrit_statistics(args)

def fetch_gerrit_statistics_C(args):
    """
    """
    args.status = "pendingreview"
    fetch_gerrit_statistics(args)

def fetch_gerrit_statistics_D(args):
    """
    """
    args.status = "need_to_address_comments"
    fetch_gerrit_statistics(args)

def fetch_gerrit_statistics_E(args):
    """
    """
    print("TODO:Implementation is in progress")
    pass

def fetch_gerrit_statistics_A_D(args):
    """
    """
    option_dict = {'A': 'open', 'B': 'merged', 'C': 'pendingreview', 'D': 'need_to_address_comments'}
    args.status = ""
    for option in args.choose_options.split(','):
        args.status += (option_dict[option]) + ","

    args.status = args.status.strip(",")
    fetch_gerrit_statistics(args)

def _parser_add_argument(parser_obj):
    """
    """

    parser_obj.add_argument(
        '--gerrit-url',
        help="Gerrit server url to process the request. Example: https://review.gluster.org/",
        metavar=('gerrit_url'), dest='gerrit_url', required=True,
        type=str)
    parser_obj.add_argument(
        '--project-name',
        help="Project name for fetching the statistics. Example: glusto-tests",
        metavar=('project_name'), dest='project_name', required=True,
        type=str)
    parser_obj.add_argument(
        '--start-date',
        help="Start date for setting the time range in YYYY-MM-DD format. Example: 2019-09-01",
        metavar=('start_date'), dest='start_date', required=True,
        type=str)
    parser_obj.add_argument(
        '--end-date',
        help="End date for setting the time range in YYYY-MM-DD format. Example: 2019-10-31",
        metavar=('end_date'), dest='end_date', required=True,
        type=str)

    parser_obj.add_argument(
        '--csv-output-file',
        help="Output file name in csv format. Example: statistics.csv",
        metavar=('csv_output_file'), dest='csv_output_file', required=True,
        type=str)

    parser_obj.add_argument(
        '--chart-output-file',
        help="Output file name for saving chart in png format. Example: statistics_chart.png",
        metavar=('chart_output_file'), dest='chart_output_file', required=True,
        type=str)
    return parser_obj

def main():
    parser = argparse.ArgumentParser(prog="fetch gerrit statistics",
                                     description=("Tool for fetching gerrit statistics"))

    subparsers = parser.add_subparsers(title='Available sub commands',
                                       help='sub-command help')

    A_parser = subparsers.add_parser(
        'A',
        help=("collects number of patches that are in open state in given timerange."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    A_parser = _parser_add_argument(A_parser)
    A_parser.set_defaults(func=fetch_gerrit_statistics_A)

    B_parser = subparsers.add_parser(
        'B',
        help=("collects number of patches that gets merged in given time range."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    B_parser = _parser_add_argument(B_parser)
    B_parser.set_defaults(func=fetch_gerrit_statistics_B)

    C_parser = subparsers.add_parser(
        'C',
        help=("collects number of patches in given time range that needs to be reviewed."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    C_parser = _parser_add_argument(C_parser)
    C_parser.set_defaults(func=fetch_gerrit_statistics_C)

    D_parser = subparsers.add_parser(
        'D',
        help=("collects number of patches in given timerange that needs comments to be addressed."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    D_parser = _parser_add_argument(D_parser)
    D_parser.set_defaults(func=fetch_gerrit_statistics_D)

    E_parser = subparsers.add_parser(
        'E',
        help=("collects number of patches reviewed and total number of comments given by list of users in given timerange."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    E_parser = _parser_add_argument(E_parser)
    E_parser.set_defaults(func=fetch_gerrit_statistics_E)

    A_D_generate_chart_parser = subparsers.add_parser(
        'generate_combined_chart',
        help=("Generates combined bar chart for the options A,B,C,D."),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    A_D_generate_chart_parser = _parser_add_argument(A_D_generate_chart_parser)
    A_D_generate_chart_parser.add_argument(
        '--choose-options',
        help="Choose the options A-D with comma separated values. Example: A,B",
        metavar=('choose_options'), dest='choose_options', required=True,
        type=str)
    A_D_generate_chart_parser.set_defaults(func=fetch_gerrit_statistics_A_D)

    args = parser.parse_args()
    args.func(args)
    sys.exit(0)

if __name__ == "__main__":
    main()
