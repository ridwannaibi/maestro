import os
import sys
import yaml
import pytest
from maestro.input import read_roles, read_groups
from maestro.playbooks import gen_concerto, gen_individual_playbook, gen_all_groups_playbook


orchestra = \
"""
databases:
  sql: 1
  mongo: 1

computing: 7
"""

groups = read_groups(yaml.safe_load(orchestra))

instruments = \
"""
databases:
  create_server:
    image: cirros
    external_network: public
    flavor: m1.nano

sql:
  create_server:
    image: cirros
    flavor: m1.medium
    username: l337
  docker:

computing:
  docker:
    username: JorgeJesus
"""

groups = read_roles(yaml.safe_load(instruments), groups)

expected_databases_playbook = \
"""- import_playbook: mongo.yml

- import_playbook: sql.yml
"""

expected_sql_playbook = \
"""- hosts: sql
  gather_facts: yes
  remote_user: l337

  tasks:

    - name: Execute role \'docker\'
      include_role:
        name: docker
"""

expected_mongo_playbook = \
"""- hosts: mongo
  gather_facts: yes
  remote_user: dummy

  tasks:
"""

expected_computing_playbook = \
"""- hosts: computing
  gather_facts: yes
  remote_user: dummy

  tasks:

    - name: Execute role \'docker\'
      include_role:
        name: docker
      vars:
        username: JorgeJesus
"""

expected_intermezzo = \
"""- import_playbook: group/databases.yml

- import_playbook: group/computing.yml"""

expected_concerto = \
"""# Play 1: Create all servers
- hosts: localhost
  gather_facts: no
  vars:
    provider: openstack

  tasks:

    - name: Setup image for servers of group 'computing'
      include_role:
        name: setup_image
        defaults_from: "{{ provider }}.yml"

    - name: Create servers of group 'computing'
      include_role:
        name: create_server
        defaults_from: "{{ provider }}.yml"
      with_items:
        - computing-001
        - computing-002
        - computing-003
        - computing-004
        - computing-005
        - computing-006
        - computing-007
      loop_control:
        loop_var: server

    - name: Setup image for servers of group 'mongo'
      include_role:
        name: setup_image
        defaults_from: "{{ provider }}.yml"

    - name: Create servers of group 'mongo'
      include_role:
        name: create_server
        defaults_from: "{{ provider }}.yml"
      vars:
        image: cirros
        external_network: public
        flavor: m1.nano
      with_items:
        - databases-mongo-001
      loop_control:
        loop_var: server

    - name: Setup image for servers of group 'sql'
      include_role:
        name: setup_image
        defaults_from: "{{ provider }}.yml"

    - name: Create servers of group 'sql'
      include_role:
        name: create_server
        defaults_from: "{{ provider }}.yml"
      vars:
        username: l337
        flavor: m1.medium
        image: cirros
        external_network: public
      with_items:
        - databases-sql-001
      loop_control:
        loop_var: server

    - name: Refresh in-memory openstack cache
      meta: refresh_inventory
"""

def test_gen_individual_playbook():

    databases_playbook = gen_individual_playbook(groups["databases"], "dummy")
    sql_playbook = gen_individual_playbook(groups["sql"], "dummy")
    mongo_playbook = gen_individual_playbook(groups["mongo"], "dummy")
    computing_playbook = gen_individual_playbook(groups["computing"], "dummy")

    assert databases_playbook == expected_databases_playbook
    assert sql_playbook == expected_sql_playbook
    assert mongo_playbook == expected_mongo_playbook
    assert computing_playbook == expected_computing_playbook

def test_gen_intermezzo():
    intermezzo = gen_all_groups_playbook(groups)
    assert intermezzo == expected_intermezzo

def test_gen_concerto():
    concerto = gen_concerto(groups, "openstack")
    assert concerto == expected_concerto
