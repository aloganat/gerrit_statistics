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
import os
from requests.auth import HTTPBasicAuth
import requests
import re
import copy

def fetch_gerrit_statistics(args):
    """
    """
    level = logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=level)

    if args.http_username and args.http_password:
        auth = HTTPBasicAuth(args.http_username, args.http_password)
    else:
        auth = None

    rest = GerritRestAPI(url=args.gerrit_url, auth=auth)

    try:

        st_str = args.status
        st_list = st_str.split(',')
        from datetime import datetime as dt
        #args.start_date = str((dt.strptime(args.start_date, "%Y-%m-%d") - timedelta(days=1)).date())
        args.end_date = str((dt.strptime(args.end_date, "%Y-%m-%d") + timedelta(days=1)).date())
        tmp_list = []
        detailed_info_list = []
        info_tmp_list = []
        for index_o,st_item in enumerate(st_list):
            query = ["project:"+args.project_name]
            if st_item == "pendingreview" or st_item == "need_to_address_comments" or st_item == "patch_review_info":
                query += ""
            else:    
                query += ["status:"+st_item]
            if index_o == 0:
                if st_item == "patch_review_info":
                    tmp_list.append(["Month", "Number of partches reviewed", "Total number of comments given", "Number of code-review +1 given", "Number of code-review +2 given"])
                else:
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
            flag = 0
            if start_month == end_month and start_year == end_year:
                detailed_count_list = []
                query += ["after:"+args.start_date]
                query += ["until:"+args.end_date]
                month_list.append(start_month)
                if st_item == "pendingreview":
                    cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' is:open (label:Verified=ok AND NOT label:Code-Review-2 AND NOT label:Code-Review-1)')
                elif st_item == "need_to_address_comments":
                    cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' status:open  (label:Code-review-1 OR label:Code-review-2)')
                elif st_item == "patch_review_info":
                    query += ["reviewedby:"+args.reviewer]
                    cmd = "/changes/?q=%s" % "%20".join(set(query))
                else:
                    cmd = "/changes/?q=%s" % "%20".join(query)
                changes = rest.get(cmd)
                if st_item == "patch_review_info":
                    review_count = 0
                    change_ids = [each_review['change_id'] for each_review in changes if True]
                    review_count = len(change_ids)
                    sum_comments_count = 0
                    code_review_1_sum_comments_count = 0
                    cnt = 0
                    for change_id in change_ids:
                        tmp_query = "/changes/" + change_id + "/comments"
                        out = rest.get(tmp_query)
                        comments_count = 0
                        for item in out.values():
                            for i in item:
                                if i["author"]["username"] == args.reviewer:
                                    comments_count = comments_count + 1
                        sum_comments_count = sum_comments_count + comments_count
                        tmp_query = "/changes/" + change_id + "/detail"
                        out = rest.get(tmp_query)
                        code_review_1_comments_count = 0
                        for item in out["labels"]["Code-Review"]["all"]:
                            for key in item:
                                if key == "username":
                                    if item[key] == args.reviewer:
                                        if item["value"] == 1:
                                            code_review_1_comments_count = code_review_1_comments_count + 1
                        code_review_1_sum_comments_count = code_review_1_sum_comments_count + code_review_1_comments_count

                        cnt = 0
                        if "approved" in out["labels"]["Code-Review"].keys():
                            if out["labels"]["Code-Review"]["approved"]["username"] == args.reviewer:
                                cnt = cnt + 1
                        else:
                            cnt = 0
                else:
                        summary_list = [item["subject"] for item in changes if True]
                        testfix_count = 0
                        libfix_count = 0
                        test_count = 0
                        lib_count = 0
                        uncategorised_count = 0
                        for str_item in summary_list:
                            if re.search(r'^\s*\[testfix\].*',str_item,re.IGNORECASE):
                                testfix_count += 1
                            elif re.search(r'^\s*\[libfix\].*',str_item,re.IGNORECASE):
                                libfix_count += 1
                            elif re.search(r'^\s*\[test\].*',str_item,re.IGNORECASE):
                                test_count += 1
                            elif re.search(r'^\s*\[lib\].*',str_item,re.IGNORECASE):
                                lib_count += 1
                            else:
                                uncategorised_count += 1

                        detailed_count = "TestFixF:" + str(testfix_count) + ",LibFix:" + str(libfix_count) + ",Test:" + str(test_count) + ",Lib:" + str(lib_count) + ",Uncategorised:" + str(uncategorised_count)
                        detailed_count_list.append(detailed_count)
                        flag = 1

                count = len(changes)
                for i in month_list:
                    if index_o == 0:
                        if st_item == "patch_review_info":
                            tmp_list.append([i, review_count, sum_comments_count, code_review_1_sum_comments_count, cnt])
                        else:
                            tmp_list.append([i, count])
                    else:
                        for inde,chk in enumerate(tmp_list):
                            if i in chk:
                                tmp_list[inde].append(count)
                tmp_detailed_list = copy.deepcopy(tmp_list)
                info_tmp_list.append(tmp_detailed_list)
                detailed_info_list.append(detailed_count_list)
            else:

                sd = dt.strptime(args.start_date, "%Y-%m-%d") 
                ed = dt.strptime(args.end_date, "%Y-%m-%d") 

                lst = [dt.strptime('%2.2d-%d' % (y, m), '%Y-%m').strftime('%B-%Y') \
                       for y in range(sd.year, ed.year+1) \
                       for m in range(sd.month if y==sd.year else 1, ed.month+1 if y == ed.year else 13)]
                for month in calendar.month_name[s_month:e_month+1]:
                    month_list.append(month)
                mon_num = len(lst)
                detailed_count_list = []
                for index,mont in enumerate(lst):
                    mon = mont.split('-')[0]
                    yr = mont.split('-')[1]
                    if index == 0:
                        query += ["after:"+args.start_date]
                        day = calendar.monthrange(start_year, int(list(calendar.month_name).index(mon)))[1]
                        #query += ["until:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)]
                        tmp_date = str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)
                        tmp_date = str((dt.strptime(tmp_date, "%Y-%m-%d") + timedelta(days=1)).date())
                        query += ["until:"+str(tmp_date)]
                    elif index == mon_num-1:
                        query = [i for i in query if (('until' not in i) and ('after' not in i)) ]
                        query += ["after:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-1"]
                        query += ["until:"+args.end_date]
                    else:
                        query = [i for i in query if (('until' not in i) and ('after' not in i)) ]
                        day = calendar.monthrange(start_year, int(list(calendar.month_name).index(mon)))[1]
                        query += ["after:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-1"]
                        #query += ["until:"+str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)]
                        tmp_date = str(yr)+"-"+str(list(calendar.month_name).index(mon))+"-"+str(day)
                        tmp_date = str((dt.strptime(tmp_date, "%Y-%m-%d") + timedelta(days=1)).date())
                        query += ["until:"+tmp_date]
                    if st_item == "pendingreview":
                        cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' is:open (label:Verified=ok AND NOT label:Code-Review-2 AND NOT label:Code-Review-1)')
                    elif st_item == "need_to_address_comments":
                        cmd = "/changes/?q=%s" % "%20".join(query) + urllib.parse.quote_plus(' status:open  (label:Code-review-1 OR label:Code-review-2)')
                    elif st_item == "patch_review_info":
                        query += ["reviewedby:"+args.reviewer]
                        cmd = "/changes/?q=%s" % "%20".join(set(query))
                    else:
                        cmd = "/changes/?q=%s" % "%20".join(query)
                    changes = rest.get(cmd)
 
                    if st_item == "patch_review_info":
                        review_count = 0
                        change_ids = [each_review['change_id'] for each_review in changes if True]
                        review_count = len(change_ids)
                        sum_comments_count = 0
                        code_review_1_sum_comments_count = 0
                        cnt = 0
                        for change_id in change_ids:
                            tmp_query = "/changes/" + change_id + "/comments"
                            out = rest.get(tmp_query)
                            comments_count = 0
                            for item in out.values():
                                for i in item:
                                    if i["author"]["username"] == args.reviewer: 
                                        comments_count = comments_count + 1
                            sum_comments_count = sum_comments_count + comments_count
                            tmp_query = "/changes/" + change_id + "/detail"
                            out = rest.get(tmp_query)
                            code_review_1_comments_count = 0
                            for item in out["labels"]["Code-Review"]["all"]:
                                for key in item:
                                    if key == "username":
                                        if item[key] == args.reviewer:
                                            if item["value"] == 1:
                                                code_review_1_comments_count = code_review_1_comments_count + 1
                            code_review_1_sum_comments_count = code_review_1_sum_comments_count + code_review_1_comments_count

                            cnt = 0
                            if "approved" in out["labels"]["Code-Review"].keys():
                                if out["labels"]["Code-Review"]["approved"]["username"] == args.reviewer:
                                    cnt = cnt + 1
                            else:
                                cnt = 0
                    else:
                        summary_list = [item["subject"] for item in changes if True]
                        testfix_count = 0
                        libfix_count = 0
                        test_count = 0
                        lib_count = 0
                        uncategorised_count = 0
                        for str_item in summary_list:
                            if re.search(r'^\s*\[testfix\].*',str_item,re.IGNORECASE):
                                testfix_count += 1
                            elif re.search(r'^\s*\[libfix\].*',str_item,re.IGNORECASE):
                                libfix_count += 1
                            elif re.search(r'^\s*\[test\].*',str_item,re.IGNORECASE):
                                test_count += 1
                            elif re.search(r'^\s*\[lib\].*',str_item,re.IGNORECASE):
                                lib_count += 1
                            else:
                                uncategorised_count += 1

                        detailed_count = "TestFixF:" + str(testfix_count) + ",LibFixF:" + str(libfix_count) + ",Test:" + str(test_count) + ",Lib:" + str(lib_count) + ",Uncategorised:" + str(uncategorised_count)
                        detailed_count_list.append(detailed_count)
                        flag = 1

                    count = len(changes)
                    mon=mon+"-"+str(yr)
                    if index_o == 0:
                        if st_item == "patch_review_info":
                            tmp_list.append([mon, review_count, sum_comments_count, code_review_1_sum_comments_count, cnt])
                        else:
                            tmp_list.append([mon, count])
                    else:
                        for inde,chk in enumerate(tmp_list):
                            if mon in chk:
                                tmp_list[inde].append(count)
                tmp_detailed_list = copy.deepcopy(tmp_list)
                info_tmp_list.append(tmp_detailed_list)
                detailed_info_list.append(detailed_count_list)
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


        if flag:
            for index, outer in enumerate(info_tmp_list):
                tmp_list1 = outer[1:]
                for ind, inner in enumerate(detailed_info_list[index]):
                    tmp_list1[ind][-1] = str(tmp_list1[ind][-1]) + "," + inner
                if index == 0:
                    new_list = tmp_list1
                else:
                    li = [item[-1] for item in tmp_list1]
                    for i, item in enumerate(li):
                        new_list[i].append(item)
            new_list.insert(0, tmp_list[0])

            args.csv_output_file = "{0}_{2}.{1}".format(*args.csv_output_file.rsplit('.', 1) + ["detailed_info"])
            with open(args.csv_output_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(new_list)

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
    args.status = "patch_review_info"
    data = args.reviewer.split(',')
    tmp_csv_output_file = args.csv_output_file
    tmp_chart_output_file = args.chart_output_file
    for reviewer in data:
        args.reviewer = reviewer
        args.csv_output_file = "{0}_{2}{1}".format(*os.path.splitext(args.csv_output_file) + (args.reviewer,))
        args.chart_output_file = "{0}_{2}{1}".format(*os.path.splitext(args.chart_output_file) + (args.reviewer,))
        fetch_gerrit_statistics(args)
        args.csv_output_file = tmp_csv_output_file
        args.chart_output_file = tmp_chart_output_file

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
        '--http-username',
        help="Gerrit HTTP username.",
        metavar=('http_username'), dest='http_username', default=None,
        type=str)

    parser_obj.add_argument(
        '--http-password',
        help="Gerrit HTTP password. Note: Please generate this password in Settings->HTTP Password page.",
        metavar=('http_password'), dest='http_password', default=None,
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
    E_parser.add_argument(
        '--reviewer',
        help="reviewer usernames with comma separated values. Example: bob,kevin",
        metavar=('reviewer'), dest='reviewer', required=True,
        type=str)
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
