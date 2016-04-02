#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    xmlexporter.py: Copyright 2016 Evgenii Sopov <mrseakg@gmail.com>
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

import cStringIO
# import xml.dom.minidom
import xml.etree.cElementTree as xmlElementTree

class XmlExporter:
	"""Iterate through the list of transactions for an account and
	export to a XML file."""
    
	@staticmethod
	def Indent(elem, level=0):
		""" Code for pretty xml format I got from here: https://norwied.wordpress.com/2013/08/27/307/ """
		i = "\n" + level*"\t"
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = i + "\t"
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				XmlExporter.Indent(elem, level+1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i

	@staticmethod
	def Export(model, exportPath):
		root = xmlElementTree.Element("wxbanker")
		for account in model.Accounts:
			xmlAccount = xmlElementTree.SubElement(root, "account", name=account.Name.encode("utf8"))
			for transaction in account.Transactions:
				date=str(transaction.GetDate()).encode("utf8")
				amount=str(transaction.GetAmount()).encode("utf8")
				descr=transaction.GetDescription() # .encode("utf8")
				xmlElTransaction = xmlElementTree.SubElement(xmlAccount, "transaction", amount=amount, date=date, description=descr)
		XmlExporter.Indent(root)
		tree = xmlElementTree.ElementTree(root)
		tree.write(exportPath,encoding="utf8",xml_declaration=True)
