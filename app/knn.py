def knn(X, data, k=1):
    '''
      X: list (n-1)
      data: m x n Int
    '''
    best_sim = 0
    best_label = -1
    best_D = None
    for D in data:
        d_ = D[:-1]
        common = len([ 1 for e1, e2 in zip(X, d_) if e1 == e2 ])
        diff = len(X) - common
        sim = (common * 1.0) / (common + diff)
        if sim > best_sim:
            best_sim = sim
            best_label = D[-1]
            best_D = D
    return best_sim, best_label, best_D