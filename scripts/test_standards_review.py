#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Hermetic semantic-boundary and standards-review regression tests."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import standards_review as review

CONTRACT = {"canonical_fields":["id","kind","statement","qualifications","evidence_refs"],
            "minimum_representation_kinds":2,"representation_kinds":["prose","table","chart","diagram","equation"]}


def unit():
    u={"id":"U1","kind":"question","statement":"Does this evidence settle the question? It may not.",
       "qualifications":["scope remains narrow"],"evidence_refs":["source:1"]}
    h=review.digest(review.canonical(u))
    u['representations']=[{'kind':k,'unit_id':'U1','unit_sha256':h} for k in ('prose','diagram')]
    u['semantic_review']={'status':'accepted','reviewer':'synthetic reviewer','unit_sha256':h,'source_ref':'fixture:review'}
    return u


class ArgumentContract(unittest.TestCase):
    def codes(self,u):return {x['code'] for x in review.check_units([u],CONTRACT)}
    def test_valid_multiple_sentence_single_paragraph(self):self.assertEqual(self.codes(unit()),set())
    def test_multiple_paragraphs_rejected(self):
        u=unit();u['statement']+='\n\nAnother argument.';self.assertIn('not-one-paragraph',self.codes(u))
    def test_html_and_pdf_are_not_two_representations(self):
        u=unit();u['representations'][1]['kind']='prose';self.assertIn('representation-coverage-gap',self.codes(u))
    def test_changed_qualification_invalidates_views_and_review(self):
        u=unit();u['qualifications']=[];c=self.codes(u)
        self.assertIn('representation-version-drift',c);self.assertIn('semantic-review-pending-or-stale',c)
    def test_question_cannot_silently_become_observation(self):
        u=unit();u['kind']='observation';self.assertIn('representation-version-drift',self.codes(u))
    def test_acceptance_word_alone_is_not_a_bound_review(self):
        u=unit();u['semantic_review']={'status':'accepted'};self.assertIn('semantic-review-pending-or-stale',self.codes(u))
    def test_duplicate_identity_rejected(self):
        self.assertIn('missing-or-duplicate-id',{x['code'] for x in review.check_units([unit(),unit()],CONTRACT)})
    def test_unavailable_report_runtime_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(review.probe_report_cli(Path(d))['status'],'unknown')


if __name__=='__main__':unittest.main()
