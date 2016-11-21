# -*- coding: utf-8 -*-
import json
import boto3
import requests
import csv

MR_ENDPOINT = 'http://files.export.gov/ng_mr.txt'
CCG_ENDPOINT = 'http://files.export.gov/ng_cgg.txt'
REPORT_TYPE_HASH = {'bmr11': 'Best Market Research', 'ccg1': 'Country Commercial Guide'}

s3 = boto3.resource('s3')


def handler(event, context):
    items = get_items(MR_ENDPOINT) + get_items(CCG_ENDPOINT)
    entries = [get_research_note(item) for item in items]
    if len(entries) > 0:
        s3.Object('market-research-notes', 'market_research_notes.json').put(Body=json.dumps(entries),
                                                                             ContentType='application/json')
        return "Uploaded market_research_notes.json file with %i notes" % len(entries)
    else:
        return "No entries loaded so there is no JSON file to upload"


def get_items(url):
    items = []
    print "Fetching weirdly formatted text feed of notes from {}...".format(url)
    response = requests.get(url)
    txt = response.text
    csv_txt = txt.replace("\t", " ").replace("\r\n", " ").replace("\r", " ").replace("<MRL_COL_END>", "\t").replace(
        "<MRL_ROW_END>", "\r\n").encode("utf-8")
    with open("/tmp/csv.txt", 'w') as tmpfile:
        tmpfile.write(csv_txt.strip())
        tmpfile.close()
    with open("/tmp/csv.txt", 'r') as csvfile:
        reader = csv.DictReader(csvfile, dialect="excel-tab")
        for row in reader:
            items.append(row)
    print "Found {} items in {}".format(len(items), url)
    return items


def get_research_note(item_dict):
    note = {k: v.strip() for k, v in item_dict.iteritems()}
    note["country"] = split_or_empty(note["country"])
    note["industry"] = split_or_empty(note["industry"])
    note["report_type"] = REPORT_TYPE_HASH.get(note["origform"], 'Market Research Report')
    if note["doc"]: note["doc"] = "http://files.export.gov/" + note["doc"]
    del note["doc_lang"]
    return note


def split_or_empty(str):
    if str: return str.split('|')
    return []
