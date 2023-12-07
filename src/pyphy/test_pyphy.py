import unittest
import pyphy

class TestPyphy (unittest.TestCase):
	def test_TaxidToName(self):
		self.assertEqual(pyphy.getNameByTaxid(2), "Bacteria")

	def test_NameToTaxid(self):
		self.assertEqual(pyphy.getTaxidByName("Proteobacteria")[0], 1224)

	def test_getRankByName(self):
		self.assertEqual(pyphy.getRankByName("Proteobacteria"), "phylum")

	def test_getAllNameByTaxid(self):
		self.assertCountEqual(pyphy.getAllNameByTaxid(976), ['Bacteroidetes', 'Bacteroides-Cytophaga-Flexibacter group', 'BCF group', 'Bacteroidaeota', 'Bacteroidota', 'Cytophaga-Flexibacter-Bacteroides phylum', 'CFB group'])

	def test_getParentByName(self):
		self.assertEqual(pyphy.getParentByName("Bacteroidetes"), 68336)

	def test_getDictPathByTaxid(self):
		self.assertEqual(pyphy.getDictPathByTaxid(1224), {'phylum': 1224, 'superkingdom': 2, 'no rank': 1})
		self.assertEqual(pyphy.getDictPathByTaxid("N/A"), {'no rank': -1})

	def test_getSonsByName(self):
		self.assertCountEqual(pyphy.getSonsByName("Leptospirillum"), [184209, 261385, 261386, 655606, 1260982, 2629551])

	def test_getAllSonsByTaxid(self):
		self.assertCountEqual(pyphy.getAllSonsByTaxid(2629551), [181, 90965, 90966, 90968, 133855, 133856, 133857, 392727, 502582, 511488, 511489, 694040, 948304, 948305, 948306, 948307, 948308, 948309, 1090554, 1402919, 1484337, 1502095, 1572228, 1572229])
