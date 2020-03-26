import os

def split_path(path):
  parts = []

  while True:
    head, tail = os.path.split(path)
    if tail.strip() != '':
      parts = [tail] + parts
    if not head: break
    path = head

  return parts
