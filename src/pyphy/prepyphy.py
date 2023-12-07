import sys, sqlite3, os
import configparser

#python prepyphy.py folder db


#taxid : Node
tree = {}

taxid_synonym = {}

folder = sys.argv[1]
conn = sqlite3.connect(sys.argv[2])

config_file = os.path.join(os.path.dirname(os.path.realpath(__file__) ),'pyphy.config')

if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    cfgfile = open(config_file, 'w')
    config.set("", "db", sys.argv[2])
    config.write(cfgfile)
    cfgfile.close()
    




if not folder.endswith("/"):
    folder += "/"


names_dmp = folder + "names.dmp"
#process the names.dmp
for line in open(names_dmp, 'r'):
    fields = line.strip().split("\t")
    notion = fields[6]
    taxid = fields[0]
    name = fields[2]

    if notion== "scientific name":
        #tree[taxid] = None or [name,"0",""]
        if taxid not in tree:
            tree[taxid] = [name,"0",""]
    elif notion== "synonym" or notion == "equivalent name":
        if taxid not in taxid_synonym:
            taxid_synonym[taxid] = set()

        taxid_synonym[taxid].add(name)
        
        #synonym_taxid[name] = None or taxid


nodes_dmp = folder + "nodes.dmp"
#process the nodes.dmp
for line in open(nodes_dmp, 'r'):
    fields = line.strip().split("\t")
    
    taxid = fields[0]
    parent = fields[2]
    rank = fields[4]
    
    if taxid in tree:
        tree.get(taxid)[1] = parent
        tree.get(taxid)[2] = rank
        


cursor = conn.cursor()
cursor.execute('''PRAGMA journal_mode = OFF''')
cursor.execute("CREATE TABLE tree (taxid integer, name text, parent integer, rank text);")


for taxid in tree.keys():
    command = "INSERT INTO tree VALUES ('" + str(taxid) + "', '" + tree[taxid][0].replace("'","''") + "', '" + str(tree[taxid][1]) + "','" + tree[taxid][2] +"');"

    cursor.execute(command)

###indexing

command = "CREATE UNIQUE INDEX taxid_on_tree ON tree(taxid);"
cursor.execute(command)

command = "CREATE INDEX name_on_tree ON tree(name);"
cursor.execute(command)

command = "CREATE INDEX parent_on_tree ON tree(parent);"
cursor.execute(command)


####synonym table

cursor.execute('''PRAGMA journal_mode = OFF''')
cursor.execute("CREATE TABLE synonym (id integer, taxid integer, name text);")


index = 0

for taxid in taxid_synonym:
    for taxon in taxid_synonym[taxid]:


        command = "INSERT INTO synonym VALUES ('" + str(index) + "', '" + str(taxid) + "', '" + taxon.replace("'","''") +"');"

        cursor.execute(command)

        index += 1


command = "CREATE INDEX name_on_synonym ON synonym(name);"
cursor.execute(command)

command = "CREATE INDEX taxid_on_synonym ON synonym(taxid);"
cursor.execute(command)

conn.commit()

