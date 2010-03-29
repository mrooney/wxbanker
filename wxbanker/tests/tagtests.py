#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    tagtests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.bankobjects.tag import Tag

class TagTests(testbase.TestCaseWithController):
    def assertStringTagsEqual(self, tagList, strList):
        self.assertEqual([str(x) for x in tagList], strList)
        
    def testEmptyModelHasNoTags(self):
        model = self.Model
        self.assertEqual(model.Tags, set())
        
        a = model.CreateAccount("A")
        t = a.AddTransaction(1)
        self.assertEqual(t.Tags, set())
        # For sanity.
        self.assertEqual(model.Tags, set())
        
    def testTagStringValue(self):
        tag = Tag(0, "Foobar")
        self.assertEqual(str(tag), "Foobar")
        
    def testTagEquality(self):
        a = Tag(1, "A")
        self.assertEqual(a, a)
        self.assertNotEqual(a, None)
        
        a2 = Tag(2, "A")
        self.assertNotEqual(a, a2)
        
        a3 = Tag(1, "A")
        self.assertEqual(a, a3)
        
    def testTaggingAndUntagging(self):
        model = self.Model
        a = model.CreateAccount("A")
        t = a.AddTransaction(amount=1, description="testing #foo")
        
        self.assertEqual(t.Tags, set(["foo"]))
        self.assertEqual(model.Tags, set(["foo"]))
        
        # foo should be untagged, bar should be tagged.
        t.Description = "another #bar"
        self.assertEqual(t.Tags, set(["bar"]))
        self.assertEqual(model.Tags, set(["bar"]))
        
        t2 = a.AddTransaction(amount=1, description="testing #bar #baz")
        self.assertEqual(t.Tags, set(["bar"]))
        self.assertEqual(t2.Tags, set(["bar", "baz"]))
        self.assertEqual(model.Tags, set(["bar", "baz"]))

        # Make sure the transaction tags are expected, and model still has bar from 't'.
        t2.Description = "nothing special"
        self.assertEqual(t.Tags, set(["bar"]))
        self.assertEqual(t2.Tags, set())
        self.assertEqual(model.Tags, set(["bar"]))
        
        

if __name__ == "__main__":
    import unittest; unittest.main()