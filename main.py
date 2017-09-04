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

data_source = args.infile
html_output = args.outfile
repository_title = args.reponame
repository_path = args.repository
template_directory = os.path.join(os.path.abspath('templates'), 'github')

ENV = Environment(loader=FileSystemLoader(template_directory))

data = re.compile(r'\[(\w+=.*?)\](?=$|\[)')
changes = re.compile(r'(\d+) files? changed(?:, (\d+) insertions?[(][+][)])?(?:, (\d+) deletions?)?')

def provide_local_repository():
    repo = repository_path.rsplit('/', 1)[1]
    cmd = "git clone "
    cmd += repository_path + " " + repo
    os.system(cmd)
    return repo

if repository_path.startswith("http") or repository_path.startswith("git://") or repository_path.startswith("git@"):
    repository_path = provide_local_repository()

print("Using ", repository_path)
def generate_git_data():
    cmd = "git -C "
    cmd += repository_path
    cmd += " log --pretty=\"format:[START commit][author=%an][time=%at][message=%s][hash=%H]\""
    cmd += " --shortstat"
    cmd += " > git-data.txt"
    print("Will run: ", cmd)
    os.system(cmd)

if not os.path.exists('git-data.txt') and os.path.exists(".git"):
    generate_git_data()
if repository_title == 'RepoName':
    repository_title = os.path.basename(repository_path)

# Makes a big blob of CSS so you dont need to worry about external files.
def get_css(template):
    css = ''
    for fname in os.listdir(os.path.join(template, 'css')):
        fname = os.path.join(template, 'css', fname)
        if os.path.isfile(fname):
            with open(fname) as f:
                css += f.read() + '\n'
    return css


with open(data_source) as f:
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

# Provide data for grouping by date
prev_c = commits[0]
for c in commits[1:]:
    c['new_date'] = (c['date'] != prev_c['date'])
    prev_c = c
commits[0]['new_date'] = True

template = ENV.get_template('main.html')

data = {'title': repository_title,
        'style': get_css(template_directory),
        'commits': commits}

with open(html_output, 'w') as f:
    f.write(set_unicode(template.render(data)))

os.unlink("git-data.txt")

print("Generated: ", os.path.join(os.path.dirname(os.path.abspath(__file__)), html_output))
