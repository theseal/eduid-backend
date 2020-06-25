# -*- coding: utf-8 -*-

from eduid_groupdb.db import BaseGraphDB, Neo4jDB
from eduid_groupdb.groupdb.db import GroupDB

# TODO: Remove later, backwards compatibility
# Depending applications should use eduid_graphdb.groupdb instead of eduid_groupdb
from eduid_groupdb.groupdb.group import Group
from eduid_groupdb.groupdb.user import User

__author__ = 'lundberg'
