from unittest import TestCase

from bson import ObjectId

import eduid.userdb.db as db
from eduid.userdb.fixtures.users import mocked_user_standard_2, new_unverified_user_example, new_user_example
from eduid.userdb.identity import IdentityType
from eduid.userdb.testing import MongoTestCase


class DummyDatabase(object):
    def __init__(self, name):
        self.name = name
        self.is_authenticated = False

    def authenticate(self, user, password):
        self.is_authenticated = True


class DummyConnection(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __getitem__(self, key):
        return DummyDatabase(key)


class TestMongoDB(TestCase):
    def test_full_uri(self):
        # full specified uri
        uri = "mongodb://db.example.com:1111/testdb"
        mdb = db.MongoDB(uri, db_name="testdb", connection_factory=DummyConnection)
        conn = mdb.get_connection()
        database = mdb.get_database()
        self.assertIsNotNone(conn)
        self.assertEqual(mdb._db_uri, uri)
        self.assertEqual(mdb._database_name, "testdb")
        self.assertFalse(database.is_authenticated)

    def test_uri_without_path_component(self):
        uri = "mongodb://db.example.com:1111"
        mdb = db.MongoDB(uri, db_name="testdb", connection_factory=DummyConnection)
        database = mdb.get_database()
        self.assertEqual(mdb._db_uri, uri + "/testdb")
        self.assertEqual(mdb._database_name, "testdb")
        self.assertFalse(database.is_authenticated)

    def test_uri_without_port(self):
        uri = "mongodb://db.example.com/"
        mdb = db.MongoDB(uri, connection_factory=DummyConnection)
        self.assertEqual(mdb._db_uri, uri)
        database = mdb.get_database("testdb")
        self.assertFalse(database.is_authenticated)
        self.assertEqual(mdb.sanitized_uri, "mongodb://db.example.com/")

    def test_uri_with_username_and_password(self):
        uri = "mongodb://john:s3cr3t@db.example.com:1111/testdb"
        mdb = db.MongoDB(uri, db_name="testdb", connection_factory=DummyConnection)
        conn = mdb.get_connection()
        self.assertIsNotNone(conn)
        database = mdb.get_database()
        self.assertEqual(mdb._db_uri, uri)
        self.assertEqual(mdb._database_name, "testdb")
        self.assertEqual(mdb.sanitized_uri, "mongodb://john:secret@db.example.com:1111/testdb")

    def test_uri_with_replicaset(self):
        uri = "mongodb://john:s3cr3t@db.example.com,db2.example.com:27017,db3.example.com:1234/?replicaSet=rs9"
        mdb = db.MongoDB(uri, db_name="testdb", connection_factory=DummyConnection)
        self.assertEqual(mdb.sanitized_uri, "mongodb://john:secret@db.example.com/testdb?replicaset=rs9")
        self.assertEqual(
            mdb._db_uri,
            "mongodb://john:s3cr3t@db.example.com,db2.example.com,db3.example.com:1234" "/testdb?replicaset=rs9",
        )

    def test_uri_with_options(self):
        uri = "mongodb://john:s3cr3t@db.example.com:27017/?ssl=true&replicaSet=rs9"
        mdb = db.MongoDB(uri, db_name="testdb", connection_factory=DummyConnection)
        self.assertEqual(mdb.sanitized_uri, "mongodb://john:secret@db.example.com/testdb?replicaset=rs9&tls=true")


class TestDB(MongoTestCase):
    def setUp(self):
        self._am_users = [new_unverified_user_example, mocked_user_standard_2, new_user_example]
        super().setUp(am_users=self._am_users)

    def test_db_count(self):
        self.assertEqual(len(self._am_users), self.amdb.db_count())

    def test_db_count_limit(self):
        self.assertEqual(1, self.amdb.db_count(limit=1))
        self.assertEqual(2, self.amdb.db_count(limit=2))

    def test_db_count_spec(self):
        self.assertEqual(1, self.amdb.db_count(spec={"_id": ObjectId("012345678901234567890123")}))

    def test_get_documents_by_filter_skip(self):
        docs = self.amdb._get_documents_by_filter(spec={}, skip=2)
        self.assertEqual(1, len(docs))

    def test_get_documents_by_filter_limit(self):
        docs = self.amdb._get_documents_by_filter(spec={}, limit=1)
        self.assertEqual(1, len(docs))

    def test_get_verified_users_count_NIN(self):
        count = self.amdb.get_verified_users_count(identity_type=IdentityType.NIN)
        assert count == 1

    def test_get_verified_users_count_EIDAS(self):
        count = self.amdb.get_verified_users_count(identity_type=IdentityType.EIDAS)
        assert count == 1

    def test_get_verified_users_count_SVIPE(self):
        count = self.amdb.get_verified_users_count(identity_type=IdentityType.SVIPE)
        assert count == 1

    def test_get_verified_users_count_None(self):
        count = self.amdb.get_verified_users_count()
        assert count == 1

    def test_get_documents_by_aggregate(self):
        match = {
            "eduPersonPrincipalName": "hubba-bubba",
        }
        docs = self.amdb._get_documents_by_aggregate(match=match)
        assert docs[0]["eduPersonPrincipalName"] == "hubba-bubba"
