#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    tagtests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.

from wxbanker.tests import testbase
from wxbanker.bankobjects.tag import Tag, EmptyTagException

class TagTests(testbase.TestCaseWithController):
    def getTransaction(self):
        return self.Model.CreateAccount("A").AddTransaction(1)
        
    def testEmptyModelHasNoTags(self):
        model = self.Model
        self.assertEqual(model.Tags, set())
        
        a = model.CreateAccount("A")
        t = a.AddTransaction(1)
        self.assertEqual(t.Tags, set())
        # For sanity.
        self.assertEqual(model.Tags, set())
        
    def testCannotCreateEmptyTag(self):
        self.assertRaisesWithMsg(Tag, [""], EmptyTagException, "Tags cannot be empty")
        
    def testTaggingTransferDoesNotNestDescription(self):
        model = self.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")
        ta, tb = a.AddTransaction(1, description="test", source=b)
        
        self.assertEqual(ta.Description, "Transfer from B (test)")
        ta.AddTag("dontmessup")
        self.assertEqual(ta.Description, "Transfer from B (test #dontmessup)")
        self.assertEqual(tb.Description, "Transfer to A (test #dontmessup)")
        
    def testTagStringValue(self):
        tag = Tag("Foobar")
        self.assertEqual(str(tag), "#Foobar")
        self.assertEqual(tag.Name, "Foobar")
        
    def testTagAddition(self):
        t = self.getTransaction()
        t.Description = "Bats and Snakes"
        self.assertEqual(t.Tags, set())
        
        t.AddTag("warning")
        self.assertEqual(t.Tags, set([Tag("warning")]))
        self.assertEqual(t.Description, "Bats and Snakes #warning")
        
        return t
        
    def testDuplicateTagAddition(self):
        # Test that adding a tag which already exists does nothing.
        t = self.testTagAddition()
        self.assertEqual(t.Description, "Bats and Snakes #warning")
        t.AddTag("warning")
        self.assertEqual(t.Description, "Bats and Snakes #warning")
        
    def testTagRemovalFromEndSubtag(self):
        t = self.getTransaction()
        # This is a test to make sure that when we replace '#greet' with nothing,
        # we don't also remove the beginning of the '#greeting' tag.
        t.Description = "hello there #greeting #greet"
        t.RemoveTag("greet")
        self.assertEqual(t.Description, "hello there #greeting")
        self.assertEqual(t.Tags, set([Tag("greeting")]))
        
    def testTagRemovalFromBeginning(self):
        t = self.getTransaction()
        t.Description = "#groceries Whole Foods"
        t.RemoveTag("groceries")
        self.assertEqual(t.Description, "Whole Foods")
        self.assertEqual(t.Tags, set())
        
    def testTagRemovalWithTagObject(self):
        # Remove a Tag object should also be valid, and this is how the OLV does it.
        t = self.getTransaction()
        t.Description = "#groceries Whole Foods"
        t.RemoveTag(Tag("groceries"))
        self.assertEqual(t.Description, "Whole Foods")
        self.assertEqual(t.Tags, set())
    
    def testTagEquality(self):
        a = Tag("A")
        self.assertEqual(a, a)
        self.assertNotEqual(a, None)
        
        a2 = Tag("A")
        self.assertEqual(a, a2)
        
        a3 = Tag("B")
        self.assertNotEqual(a3, a)
        self.assertNotEqual(a3, a2)
        
    def testTaggingAndUntagging(self):
        model = self.Model
        a = model.CreateAccount("A")
        t = a.AddTransaction(amount=1, description="testing #foo")
        
        self.assertEqual([Tag("foo")], [Tag("foo")])
        self.assertEqual(set([Tag("foo")]), set([Tag("foo")]))
        self.assertEqual(t.Tags, set([Tag("foo")]))
        self.assertEqual(model.Tags, set([Tag("foo")]))
        
        # foo should be untagged, bar should be tagged.
        t.Description = "another #bar"
        self.assertEqual(t.Tags, set([Tag("bar")]))
        self.assertEqual(model.Tags, set([Tag("bar")]))
        
        t2 = a.AddTransaction(amount=1, description="testing #bar #baz")
        self.assertEqual(t.Tags, set([Tag("bar")]))
        self.assertEqual(t2.Tags, set([Tag("bar"), Tag("baz")]))
        self.assertEqual(model.Tags, set([Tag("bar"), Tag("baz")]))

        # Make sure the transaction tags are expected, and model still has bar from 't'.
        t2.Description = "nothing special"
        self.assertEqual(t.Tags, set([Tag("bar")]))
        self.assertEqual(t2.Tags, set())
        self.assertEqual(model.Tags, set([Tag("bar")]))
        
        

if __name__ == "__main__":
    import unittest; unittest.main()