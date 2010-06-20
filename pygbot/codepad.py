"""
Stolen from infobat.

http://launchpad.net/infobat
"""


import sys
import lxml.html

from urllib import urlencode
from urlparse import urljoin

from twisted.internet import defer
from twisted.web import client

_EXEC_PRELUDE = """#coding:utf-8
import os, sys, math, re, random
"""

@defer.inlineCallbacks
def codepad(code, run=True):
    post_data = dict(
        code=code, lang='Python', submit='Submit', private='True')
    if run:
        post_data['run'] = 'True'
    post_data = urlencode(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    ign, fac = yield client.getPage('http://codepad.org/',
        method='POST', postdata=post_data, headers=headers)
    paste_url = urljoin('http://codepad.org/',
        fac.response_headers['location'][0])
    defer.returnValue(paste_url)

@defer.inlineCallbacks
def codepad_exec(code):
    try:
        paste_url = yield codepad(_EXEC_PRELUDE + ' '.join(code))
        page, ign = yield client.getPage(paste_url)
    except:
        defer.returnValue("Error: %r" % (sys.exc_info()[2],))
    else:
        doc = lxml.html.fromstring(page.decode('utf8', 'replace'))
        response = u''.join(doc.xpath("//a[@name='output']"
            "/following-sibling::div/table/tr/td[2]/div/pre/text()"))
        response = [line.rstrip()
            for line in response.encode('utf-8').splitlines()
            if line.strip()]
        nlines = len(response)
        if nlines > 2:
            response[1:] = [u'(... %(nlines)d lines, '
            u'entire response in %(url)s ...)' %
            {'nlines': nlines, 'url': paste_url}]
        defer.returnValue('\n'.join(response))

def codepad_eval(code):
    return codepad_exec('print ' + code)
