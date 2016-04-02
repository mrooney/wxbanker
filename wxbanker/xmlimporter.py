#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    xmlimporter.py: Copyright 2016 Evgenii Sopov <mrseakg@gmail.com>
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

from datetime import date, datetime
import codecs, os, re
from cStringIO import StringIO
from wxbanker.bankobjects.transaction import Transaction
import xml.etree.cElementTree as xmlElementTree

class XmlImporter:
	"""
	Parses a xml file and extracts the data for import into the wxBanker data structures.
	"""

	@staticmethod
	def Import(model, xmlpath):
		parser = xmlElementTree.XMLParser(encoding="utf-8")
		tree = xmlElementTree.parse(xmlpath, parser=parser)
		root = tree.getroot()

		# removing all accounts
		accounts = []
		for acc in model.Accounts:
			accounts.append(acc.GetName())
		for acc in accounts:
			model.Accounts.Remove(acc)

		for xmlAccount in root:
			accountName = xmlAccount.attrib['name']
			accountIndex = model.Accounts.AccountIndex(accountName)
			if accountIndex == -1:
				model.Accounts.Create(accountName)
				accountIndex = model.Accounts.AccountIndex(accountName)
			
			accountModel = model.Accounts[accountIndex]
			for xmlTransaction in xmlAccount:
				date = xmlTransaction.attrib['date']
				amount = xmlTransaction.attrib['amount']
				description = xmlTransaction.attrib['description']
				accountModel.AddTransaction(amount=amount, date=date, description=description)			
