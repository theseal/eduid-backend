# -*- coding: utf-8 -*-

from unittest import TestCase
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from eduid.userdb.ladok import Ladok, University

__author__ = 'lundberg'


class LadokTest(TestCase):
    def setUp(self) -> None:
        self.external_uuid = uuid4()

    def test_create_ladok(self):
        university = University(
            abbr='AB', name_sv='Lärosätesnamn', name_en='University Name', created_by='test created_by'
        )
        ladok = Ladok(external_id=self.external_uuid, university=university, created_by='test created_by')

        self.assertEqual(ladok.external_id, self.external_uuid)
        self.assertEqual(ladok.created_by, 'test created_by')
        self.assertIsNotNone(ladok.created_ts)

        self.assertEqual(ladok.university.abbr, 'AB')
        self.assertEqual(ladok.university.name_sv, 'Lärosätesnamn')
        self.assertEqual(ladok.university.name_en, 'University Name')
        self.assertEqual(ladok.university.created_by, 'test created_by')
        self.assertIsNotNone(ladok.university.created_ts)
