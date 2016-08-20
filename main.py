#!/usr/bin/env python
# Use this is generate log data for the default template

from __future__ import print_function, unicode_literals

import re
import os
import sys
from datetime import datetime
import argparse
import webbrowser
from subprocess import call
import subprocess
from jinja2 import Environment, FileSystemLoader

from compat import get_unicode, set_unicode

parser = argparse.ArgumentParser(description='Build html logbook for git')
parser.add_argument('-r', '--repository', help='path to a git repository',
                    default='./')
parser.add_argument('-i', '--infile', help='log file', default='git-data.txt',
                    dest='infile')
parser.add_argument('-o', '--outfile', help='destination file',
                    default='gitBook.html', dest='outfile')
parser.add_argument('-n', '--reponame', default='RepoName', dest='reponame',
                    help='Repository name')

args = parser.parse_args()

DATAFILE = args.infile
HTMLFILE = args.outfile
HEADING = args.reponame
REPOSITORY = args.repository
TEMPLATE_DIR = os.path.join(os.path.abspath('templates'), 'github')

ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

data = re.compile(r'\[(\w+=.*?)\](?=$|\[)')
changes = re.compile(r'(\d+) files? changed(?:, (\d+) insertions?[(][+][)])?(?:, (\d+) deletions?)?')

def provide_local_repository():
    cmd = "git clone "
    cmd += REPOSITORY
    os.system(cmd)
    return REPOSITORY.rsplit('/', 1)[1]

if REPOSITORY.startswith("http"):
    REPOSITORY = provide_local_repository()

print("Using ", REPOSITORY)
def generate_git_data():
    cmd = "git -C "
    cmd += REPOSITORY
    cmd += " log --pretty=\"format:[START commit][author=%an][time=%at][message=%s][hash=%H]\""
    cmd += " --shortstat"
    cmd += " > git-data.txt"
    print("Will run: ", cmd)
    os.system(cmd)

def guess_repository_name():
    cmd = "basename "
    cmd += "`git -C "
    cmd += REPOSITORY
    cmd += " rev-parse --show-toplevel`"
    print("Will run: ", cmd)
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return out

if not os.path.exists('git-data.txt') and os.path.exists(".git"):
    generate_git_data()
if HEADING == 'RepoName':
    HEADING = guess_repository_name()

# Makes a big blob of CSS so you dont need to worry about external files.
def get_css(template):
    css = ''
    for fname in os.listdir(os.path.join(template, 'css')):
        fname = os.path.join(template, 'css', fname)
        if os.path.isfile(fname):
            with open(fname) as f:
                css += f.read() + '\n'
    return css


with open(DATAFILE) as f:
    r_commits = [x.strip().split('\n') for x in get_unicode(f.read()).split('\n[START commit]')]

commits = []

for r_commit in r_commits:
    commit = {}

    for item in re.findall(data, r_commit[0]):
        key, value = item.split('=', 1)
        commit[key] = value

    if len(r_commit) > 1:
        commit['changed'], commit['inserts'], commit['deletes'] = re.search(changes, r_commit[1]).groups()
    else:
        commit['changed'] = '-'
        commit['inserts'] = '-'
        commit['deletes'] = '-'

    if 'time' in commit:
        datet = datetime.fromtimestamp(int(commit['time']))
        commit['date'] = datet.strftime('%d-%m-%Y')
        commit['time'] = datet.strftime('%I:%M:%S %p')
    commits.append(commit)

template = ENV.get_template('main.html')

data = {'title': HEADING,
        'style': get_css(TEMPLATE_DIR),
        'commits': commits}

with open(HTMLFILE, 'w') as f:
    f.write(set_unicode(template.render(data)))

os.system("mv git-data.txt /tmp/")
#sys.exit()
webbrowser.open_new_tab('file://%s' % os.path.join(os.path.dirname(os.path.abspath(__file__)), HTMLFILE))
