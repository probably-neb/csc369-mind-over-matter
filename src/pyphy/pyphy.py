import sqlite3
import os
import configparser

db = "./ncbi.db"
threads = 20

config_file = os.path.join(os.path.dirname(os.path.realpath(__file__) ),'pyphy.config')

if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)


    db = config['DEFAULT']['db']

    threads = int(config['DEFAULT']['threads'])


#print (db)

unknown = -1
no_rank = "no rank"

#pyphy.getTaxidByName("Bacteria",1)
def getTaxidByName(name,limit=1, synonym=True):
    """get taxid given a taxonomic name or a synonym
    
    Args:
        name (str): query taxonomic name
        limit (int, optional): how many taxid to return
        synonym (bool, optional): should a synonym search be performed
    
    Returns:
        list: return a list of taxid if the name is found otherwise a list of unknown
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT taxid FROM tree WHERE name = '" + str(name).replace("'", "''") +  "';"

    cursor.execute(command)
    results = cursor.fetchall()
    
    
    temp = []
    for result in results:
        temp.append(result[0])
    
    if len(temp) != 0:
        temp.sort()
        cursor.close()
        return temp[:limit]
    elif synonym == True:
  
        command = "SELECT taxid FROM synonym WHERE name = '" + str(name).replace("'", "''") +  "';"
        cursor.execute(command)
        results = cursor.fetchall()
        cursor.close()
        temp = []

        for result in results:
            temp.append(result[0])

        if len(temp) != 0:
            temp.sort()
            return temp[:limit]

        else:
            return [unknown]

    else:
        cursor.close()
        return [unknown]
    
#pyphy.getRankByTaxid("2")
def getRankByTaxid(taxid):
    """get the rank given a taxid
    
    Args:
        taxid (int or str):query taxid
    
    Returns:
        str: the rank of the taxid
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT rank FROM tree WHERE taxid = '" + str(taxid) +  "';"
    cursor.execute(command)
       
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return no_rank


def getRankByName(name, synonym=True):
    """get the rank given a taxonomic name or a synonym
    
    Args:
        name (str): query taxonomic name
        synonym (bool, optional): should a synonym search be performed
    
    Returns:
        str: the rank of the name if found otherwise no_rank
    """
    try:
        return getRankByTaxid(getTaxidByName(name, 1, synonym)[0])
    except:
        return no_rank



def getNameByTaxid(taxid):
    """get taxonomic name given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        str: return a taxonomic name if it is found otherwise unknown
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT name FROM tree WHERE taxid = '" + str(taxid) +  "';"
    cursor.execute(command)
    
    result = cursor.fetchone()
    cursor.close()   
    if result:
        return result[0]
    else:
        return "unknown"

def getAllNameByTaxid(taxid):
    """get taxonomic names and synonyms given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        list: return a list taxonomic names and synonyms if it is found otherwise unknown
    """
    result = []
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    command = "SELECT name FROM tree WHERE taxid = '" + str(taxid) +  "';"
    cursor.execute(command)
    
    name = cursor.fetchone()
       
    if name:
        result.append(name[0])
    
    command = "SELECT name FROM synonym WHERE taxid = '" + str(taxid) +  "';"
    cursor.execute(command)
    
    names = cursor.fetchall()
    cursor.close()   
    for name in names:
        result.append(name[0])

    if len(result) != 0:
        return result
    else:
        return ["unknown"]
    

def getParentByTaxid(taxid):
    """get parent taxid given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        int: return the parent taxid if it is found otherwise unknown
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT parent FROM tree WHERE taxid = '" + str(taxid) +  "';"
    cursor.execute(command)
    
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return unknown
    

#pyphy.getParentByName("Flavobacteriia")
def getParentByName(name, synonym=True):
    """get parent taxid given a taxonomic name
    
    Args:
        name (str): query name
        
    
    Returns:
        list: return the parent taxid if it is found otherwise unknown
    """

    try:
        return getParentByTaxid(getTaxidByName(name, 1, synonym)[0])
    except:
        return unknown
    

def getPathByTaxid(taxid):
    """get the taxonomic path given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        list: return a list of parent taxid if it is found otherwise an empty list
    """

    path = []
    
    current_id = -1

    try:
        current_id = int(taxid)
    except:
        pass
    path.append(current_id)
    
    while current_id != 1 and current_id != unknown:
        #print current_id
        current_id = int(getParentByTaxid(current_id))
        path.append(current_id)
    
    return path[::-1]


def getDictPathByTaxid(taxid):
    """get the taxonomic path with the ranks as keys given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        dict: return a dict of rank: parent taxid if it is found otherwise an empty dict
    """

    path = {}

    current_id = -1

    try:
        current_id = int(taxid)
    except:
        pass
    rank = getRankByTaxid(current_id)
    path[rank] = current_id
    
    while current_id != 1 and current_id != unknown:
        #print current_id
        current_id = int(getParentByTaxid(current_id))
        rank = getRankByTaxid(current_id)

        path[rank] = current_id
    
    return path


    
    
def getSonsByTaxid(taxid):

    """get the 1st-level sons given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        list: return a list of son taxid if it is found otherwise an empty list
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT taxid FROM tree WHERE parent = '" + str(taxid) +  "';"
    result = [row[0] for row in cursor.execute(command)]
    cursor.close()
    return result


def getSonsByName(name, synonym=False):
    """get the 1st-level sons given a taxonomic name
    
    Args:
        name (str): query name
        
    
    Returns:
        list: return a list of son taxid if it is found otherwise an empty list
    """

    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    command = "SELECT taxid FROM tree WHERE parent = '" + str(getTaxidByName(name, 1, synonym)[0]) +  "';"
    result = [row[0] for row in cursor.execute(command)]
    cursor.close()
    return result



def getAllSonsByTaxid(taxid):
    """get the sons of all levels given a taxid
    
    Args:
        taxid (str or int): query taxid
        
    
    Returns:
        list: return a list of son taxid if it is found otherwise an empty list
    """

    from threading import Thread
    import queue
    in_queue = queue.Queue()
    out_queue = queue.Queue()
    
    def work():
        while True:
            sonId = in_queue.get()
#
#if here use getAllSonsByTaxid, it will be true recursive,
#but it will run over the thread limit set by the os by trying "Flavobacteriia" (6000+)
#error: can't start new thread
#it is more elegant here

            for s_s_id in getSonsByTaxid(sonId):
                #print "s_s_id" + str(s_s_id)
                out_queue.put(s_s_id)
                in_queue.put(s_s_id)

       
            in_queue.task_done()
    
    for i in range(threads):
        
        t = Thread(target=work)
        t.daemon = True
        t.start()

    current_id = -1

    try:
        current_id = int(taxid)
    except:
        pass
    

    for son in getSonsByTaxid(current_id):
        out_queue.put(son)
        in_queue.put(son)
        
    
    in_queue.join()   
 
    result = []
    
    while not out_queue.empty():
        
        result.append( out_queue.get())

    #print result
    return result
    



    
if __name__ == '__main__':
    pass
