import random
import math
import operator
from functools import reduce
from .model import HASIL_LAB_STRUCTURE
from .model import HasilLab, create_session, array_from_hl

def prod(iterable):
    return reduce(operator.mul, iterable)

def randomData():
    # jenis ikan 1 to 4
    ji = random.randint(1, 4)
    kes = random.randint(0, 1)

    attrs = [ random.randint(a, b) for _, a, b in HASIL_LAB_STRUCTURE ]
    # First attribute is jenis_ikan
    data =  [ ji ]
    data.extend(attrs)
    # Last attribute is target class
    data.append(kes)
    return data

def separateByClass(data):
    result = {
      1:  [],
      0: []
    }
    for d in data:
        target = d[-1]
        result[target].append(d)
    return result

def nb2(X, data):
    X_ = X[1:-1]
    separated = separateByClass(data)
    pc0 = len(separated[0])
    pc1 = len(separated[1])
    lenc0 = len(separated[0]) * 1.0
    lenc1 = len(separated[1]) * 1.0

    probs = {
      0: [],
      1: []
    }

    for i, x in enumerate(X_, start=1):
        din0 = len([d for d in separated[0]  if d[i] == x]) * 1.0
        din1 = len([d for d in separated[1]  if d[i] == x]) * 1.0

        probs[0].append( (din0 + 1) / (lenc0 + 1)  )
        probs[1].append( (din1 + 1) / (lenc1 + 1)  )
    
    pec0 = pc0 * prod(probs[0])
    pec1 = pc1 * prod(probs[1])
    pe = pec0 + pec1

    pec0= pec0 / pe
    pec1= pec1 / pe

    if pec1 > pec0: return 1
    else: return 0

def test():
    db_session = create_session()
    raw_data = db_session.query(HasilLab).all()
    data = list(map(array_from_hl, raw_data))
    inputVector = randomData()
    # print( nb2(inputVector, data) )

if __name__ == '__main__':
    test()