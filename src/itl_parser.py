#!/usr/bin/python

# ITL parser

import sys

class SexprParser(object):
  def __init__(self, body):
    self.stack = [[]]
    self.cur = ''
    self.body = body

  def top(self):
    return self.stack[-1]
  def pop(self):
    ret = self.top()
    self.stack.pop()
    return ret
  def end_atom(self):
    if self.cur != '':
      self.top().append(self.cur)
      self.cur = ''

  def parse(self):
    i = 0
    while i < len(self.body):
      c = self.body[i]
      if c in [' ', '\n']:
        self.end_atom()
      elif c == '(':
        self.end_atom()
        self.stack.append([])
      elif c == ')':
        self.end_atom()
        top = self.pop()
        self.top().append(top)
      else:
        self.cur += c
      i += 1
    return self.pop()

def parse(body):
  return SexprParser(body).parse()
