# This file was taken from https://bitbucket.org/lgs/pyramidsaml2/overview
# this was modified from django to pyramid and then to nothing.
#
# Original copyright and licence
# Copyright (C) 2011-2012 Yaco Sistemas (http://www.yaco.es)
# Copyright (C) 2010 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict

from saml2.cache import Cache


class SessionCacheAdapter(dict):
    """A cache of things that are stored in some backend"""

    key_prefix = "_saml2"

    def __init__(self, backend: Dict[str, Any], key_suffix: str):
        self.session = backend
        self.key = self.key_prefix + key_suffix

        super().__init__(self._get_objects())

    def _get_objects(self) -> Any:
        return self.session.get(self.key, {})

    def _set_objects(self, objects: Any):
        self.session[self.key] = objects

    def sync(self):
        objs: Dict[str, Any] = {}
        objs.update(self)
        self._set_objects(objs)


class OutstandingQueriesCache(object):
    """Handles the queries that have been sent to the IdP and have not
    been replied yet.
    """

    def __init__(self, backend):
        self._db = SessionCacheAdapter(backend, "_outstanding_queries")

    def outstanding_queries(self):
        return self._db._get_objects()

    def set(self, saml2_session_id, came_from):
        self._db[saml2_session_id] = came_from
        self._db.sync()

    def delete(self, saml2_session_id):
        if saml2_session_id in self._db:
            del self._db[saml2_session_id]
            self._db.sync()


class IdentityCache(Cache):
    """Handles information about the users that have been successfully logged in.

    This information is useful because when the user logs out we must
    know where does he come from in order to notify such IdP/AA.
    """

    def __init__(self, backend):
        self._db = SessionCacheAdapter(backend, "_identities")
        self._sync = True

    def delete(self, subject_id):
        super(IdentityCache, self).delete(subject_id)
        # saml2.Cache doesn't do a sync after a delete
        # I'll send a patch to fix this in that side, after which this
        # could be removed
        self._db.sync()


class StateCache(SessionCacheAdapter):
    """Store state information that is needed to associate a logout
    request with its response.
    """

    def __init__(self, backend):
        super(StateCache, self).__init__(backend, "_state")
