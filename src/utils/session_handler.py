#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of commix (@commixproject) tool.
Copyright (c) 2014-2016 Anastasios Stasinopoulos (@ancst).
https://github.com/stasinopoulos/commix

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

For more see the file 'readme/COPYING' for copying permission.
"""

import os
import sys
import time
import base64
import sqlite3
import urllib2

from src.utils import menu
from src.utils import settings

from src.thirdparty.colorama import Fore, Back, Style, init

"""
Session handler via SQLite3 db.
"""
no_such_table = False

"""
Generate table name for SQLite3 db.
"""
def table_name(url):
  host = url.split('//', 1)[1].split('/', 1)[0]
  table_name =  "session_" + host.replace(".","_").replace(":","_")
  return table_name

"""
Flush session.
"""
def flush(url):
  try:
    conn = sqlite3.connect(settings.SESSION_FILE)
    tables = list(conn.execute("SELECT name FROM sqlite_master WHERE type is 'table'"))
    conn.executescript(';'.join(["DROP TABLE IF EXISTS %s" %i for i in tables]))
    conn.commit()
    conn.close()
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL

"""
Clear injection point records 
except latest for every technique.
"""
def clear(url):
  try:
    if no_such_table:
      conn = sqlite3.connect(settings.SESSION_FILE)
      conn.execute("DELETE FROM " + table_name(url) + "_ip WHERE \
                   id NOT IN (SELECT MAX(id) FROM " + \
                   table_name(url) + "_ip GROUP BY technique);")
      conn.commit()
      conn.close()
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL
  except:
    settings.LOAD_SESSION = False
    return False

"""
Import successful injection points to session file.
"""
def injection_point_importation(url, technique, injection_type, separator, shell, vuln_parameter, prefix, suffix, TAG, alter_shell, payload, http_request_method, url_time_response, delay, how_long, output_length, is_vulnerable):
  try:  
    conn = sqlite3.connect(settings.SESSION_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS " + table_name(url) + "_ip" + \
                 "(id INTEGER PRIMARY KEY, url VARCHAR, technique VARCHAR, injection_type VARCHAR, separator VARCHAR, \
                 shell VARCHAR, vuln_parameter VARCHAR, prefix VARCHAR, suffix VARCHAR, \
                 TAG VARCHAR, alter_shell VARCHAR, payload VARCHAR, http_header VARCHAR, http_request_method VARCHAR, url_time_response INTEGER, \
                 delay INTEGER, how_long INTEGER, output_length INTEGER, is_vulnerable VARCHAR);")

    conn.execute("INSERT INTO " + table_name(url) + "_ip(url, technique, injection_type, separator, \
                 shell, vuln_parameter, prefix, suffix, TAG, alter_shell, payload, http_header, http_request_method, \
                 url_time_response, delay, how_long, output_length, is_vulnerable) \
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", \
                 (str(url), str(technique), str(injection_type), \
                 str(separator), str(shell), str(vuln_parameter), str(prefix), str(suffix), \
                 str(TAG), str(alter_shell), str(payload), str(settings.HTTP_HEADER), str(http_request_method), \
                 int(url_time_response), int(delay), int(how_long), \
                 int(output_length), str(is_vulnerable)))
    conn.commit()
    conn.close()
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL
  except sqlite3.DatabaseError, err:
    error_msg = "An error occurred while accessing session file ('" + \
                 settings.SESSION_FILE + "'). " + \
                 "If the problem persists use the '--flush-session' option."
    print "\n" + Back.RED + settings.ERROR_SIGN + error_msg + Style.RESET_ALL
    sys.exit(0)

"""
Export successful applied techniques from session file.
"""
def applied_techniques(url, http_request_method):
  try:
    conn = sqlite3.connect(settings.SESSION_FILE)
    if settings.TESTABLE_PARAMETER: 
      applied_techniques = conn.execute("SELECT technique FROM " + table_name(url) + "_ip WHERE \
                                        url = '" + url + "' AND \
                                        vuln_parameter = '" + settings.TESTABLE_PARAMETER + "' AND \
                                        http_request_method = '" + http_request_method + "' \
                                        ORDER BY id DESC ;")
    else:
      applied_techniques = conn.execute("SELECT technique FROM " + table_name(url) + "_ip WHERE \
                                        url = '" + url + "' AND \
                                        http_header = '" + settings.HTTP_HEADER + "' AND \
                                        http_request_method = '" + http_request_method + "' \
                                        ORDER BY id DESC ;")
    values = []
    for session in applied_techniques:
      values += session[0][:1]
    applied_techniques = ''.join(list(set(values)))
    return applied_techniques
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL
    settings.LOAD_SESSION = False
    return False
  except:
    settings.LOAD_SESSION = False
    return False

"""
Export successful injection points from session file.
"""
def injection_point_exportation(url, http_request_method):
  try:
    if not menu.options.flush_session:
      conn = sqlite3.connect(settings.SESSION_FILE)
      result = conn.execute("SELECT * FROM sqlite_master WHERE name = '" + \
                             table_name(url) + "_ip' AND type = 'table';")
      if result:
        if settings.TESTABLE_PARAMETER:
          if menu.options.tech[:1] == "c" or \
             menu.options.tech[:1] == "e":
            select_injection_type = "R"
          elif menu.options.tech[:1] == "t":
            select_injection_type = "B"
          else:
            select_injection_type = "S"
          cursor = conn.execute("SELECT * FROM " + table_name(url) + "_ip WHERE \
                                url = '" + url + "' AND \
                                injection_type like '" + select_injection_type + "%' AND \
                                vuln_parameter = '" + settings.TESTABLE_PARAMETER + "' AND \
                                http_request_method = '" + http_request_method + "' \
                                ORDER BY id DESC limit 1;")
        else:
          cursor = conn.execute("SELECT * FROM " + table_name(url) + "_ip WHERE \
                                url = '" + url + "' AND \
                                injection_type like '" + select_injection_type + "%' AND \
                                http_header = '" + settings.HTTP_HEADER + "' AND \
                                http_request_method = '" + http_request_method + "' \
                                ORDER BY id DESC limit 1;")
        for session in cursor:
          url = session[1]
          technique = session[2]
          injection_type = session[3]
          separator = session[4]
          shell = session[5]
          vuln_parameter = session[6]
          prefix = session[7]
          suffix = session[8]
          TAG = session[9]
          alter_shell = session[10]
          payload = session[11]
          http_request_method = session[13]
          url_time_response = session[14]
          delay = session[15]
          how_long = session[16]
          output_length = session[17]
          is_vulnerable = session[18]
          return url, technique, injection_type, separator, shell, vuln_parameter, prefix, suffix, TAG, alter_shell, payload, http_request_method, url_time_response, delay, how_long, output_length, is_vulnerable
    else:
      no_such_table = True
      pass
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL
    settings.LOAD_SESSION = False
    return False
  except:
    settings.LOAD_SESSION = False
    return False

"""
Notification about session.
"""
def notification(url, technique):
  try:
    if settings.LOAD_SESSION == True:
      print Fore.YELLOW + settings.WARNING_SIGN + "A previously stored session has been held against that host." + Style.RESET_ALL  
      while True:
        settings.LOAD_SESSION = raw_input(settings.QUESTION_SIGN + "Do you want to resume to the "  + technique.rsplit(' ', 2)[0] + " injection point? [Y/n/q] > ").lower()
        if settings.LOAD_SESSION in settings.CHOISE_YES:
          return True
        elif settings.LOAD_SESSION in settings.CHOISE_NO:
          settings.LOAD_SESSION = False
          if technique[:1] != "c":
            while True:
              proceed_option = raw_input(settings.QUESTION_SIGN + "Which technique do you want to re-evaluate? [(C)urrent/(a)ll/(n)one] > ")
              if proceed_option.lower() in settings.CHOISE_PROCEED :
                if proceed_option.lower() == "a":
                  settings.RETEST = True
                  break
                elif proceed_option.lower() == "c":
                  settings.RETEST = False
                  break
                elif proceed_option.lower() == "n":
                  raise SystemExit()
                else:
                  pass  
              else:
                if proceed_option.lower()  == "":
                   proceed_option  = "enter"
                print Back.RED + settings.ERROR_SIGN + "'" +  proceed_option + "' is not a valid answer." + Style.RESET_ALL + "\n"
                pass
          return False
        elif settings.LOAD_SESSION in settings.CHOISE_QUIT:
          raise SystemExit()
        else:
          if settings.LOAD_SESSION == "":
            settings.LOAD_SESSION = "enter"
          print Back.RED + settings.ERROR_SIGN + "'" + settings.LOAD_SESSION + "' is not a valid answer." + Style.RESET_ALL + "\n"
          pass
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL

"""
Check for specific stored parameter.
"""
def check_stored_parameter(url, http_request_method): 
  if injection_point_exportation(url, http_request_method):
    if settings.TESTABLE_PARAMETER == injection_point_exportation(url, http_request_method)[5] or \
       settings.INJECT_TAG == injection_point_exportation(url, http_request_method)[5]:
      return True
    else:
      return False
  else:
    return False

"""
Import successful command execution outputs to session file.
"""
def store_cmd(url, cmd, shell, vuln_parameter):
  try:  
    conn = sqlite3.connect(settings.SESSION_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS " + table_name(url) + "_ir" + \
                 "(cmd VARCHAR, output VARCHAR, vuln_parameter VARCHAR);")
    conn.execute("INSERT INTO " + table_name(url) + "_ir(cmd, output, vuln_parameter) \
                 VALUES(?,?,?)", \
                 (str(base64.b64encode(cmd)), str(base64.b64encode(shell)), str(vuln_parameter)))
    conn.commit()
    conn.close()
  except sqlite3.OperationalError, err:
    print Back.RED + settings.ERROR_SIGN + str(err) + Style.RESET_ALL

"""
Export successful command execution outputs from session file.
"""
def export_stored_cmd(url, cmd, vuln_parameter):
  try:  
    if not menu.options.flush_session:
      conn = sqlite3.connect(settings.SESSION_FILE)
      output = None
      conn = sqlite3.connect(settings.SESSION_FILE)
      cursor = conn.execute("SELECT output FROM " + table_name(url) + \
                            "_ir WHERE cmd='" + base64.b64encode(cmd) + "' AND \
                            vuln_parameter= '" + vuln_parameter + "';").fetchall()
      for session in cursor:
        output = base64.b64decode(session[0])
      return output
    else:
      no_such_table = True
      pass
  except sqlite3.OperationalError, err:
    pass

# eof
