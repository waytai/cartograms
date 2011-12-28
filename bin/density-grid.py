#!/usr/bin/python
# -*- encoding: utf-8 -*-

import sys
import psycopg2

"""
Generate a density grid that can be fed to cart.
"""

XMAX, YMAX = 17005833.3305252, 8625154.47184994
X, Y = 500, 250


db = psycopg2.connect("host=localhost")

dataset_name = sys.argv[1]

def country_at_position(x, y):
  c = db.cursor()
  try:
    c.execute("""
      select gid from country
      where ST_Contains(the_geom, ST_Transform(ST_GeomFromText('POINT(%d %d)', 954030), 4326))
    """ % (x, -y))
    r = c.fetchone()
    return r[0] if r else None
  finally:
    c.close()

def get_global_density():
    c = db.cursor()
    try:
        c.execute("""
            select sum(data_value.value) / sum(country.area)
            from country
            join data_value on country.gid = data_value.country_gid
            join dataset on data_value.dataset_id = dataset.id
            where dataset.name = %s
        """, (dataset_name,))
        return c.fetchone()[0]
    finally:
        c.close()

def get_local_densities():
  c = db.cursor()
  try:
    c.execute("""
      select y, x, data_value.value / country.area density
      from grid
      left join data_value using (country_gid)
      left join dataset on data_value.dataset_id = dataset.id
      left join country on grid.country_gid = country.gid
      where dataset.name is null or dataset.name = %s
      order by y, x
    """, (dataset_name,))
    
    a = [ [None for i in range(X)] for j in range(Y) ]
    for r in c.fetchall():
      y, x, v = r
      a[y][x] = v
    
    return a
    
  finally:
    c.close()

global_density = get_global_density()
local_densities = get_local_densities()
def carbon_reserve_density_at_position(x, y):
  return local_densities[y][x] or global_density

padding = " ".join(["%.5f" % global_density] * X)
for y in range(Y):
  print padding, padding, padding
for y in range(Y):
  print padding, (" ".join(["%.5f"] * X)) % tuple((
    carbon_reserve_density_at_position(x, y) for x in range(X)
  )), padding
for y in range(Y):
  print padding, padding, padding

