from .model import HasilLab, JenisIkan, User, create_session, HASIL_LAB_ATTRS, hasil_lab_attrs_view, array_from_hl
import random
from .nb import nb2
from .knn import knn
from . import model
from itertools import chain

def test_all_with_indexing(indexing=True):

    db_session = create_session()

    raw_data = db_session.query(HasilLab).all()
    data = list(map(array_from_hl, raw_data))

    random.shuffle(data)
    n = len(data)
    train_r = int(0.7 * n)
    test_r = n - train_r

    X_train = data[:train_r]
    X_test = data[train_r:]
    
    if indexing:
        hit = 0
        for x_test in X_test:
            inputVector = x_test[:-1]
            target_class = nb2(inputVector, data)

            raw_data = db_session.query(HasilLab).filter(HasilLab.kesimpulan == target_class).all()
            data = list(map(array_from_hl, raw_data))
            sim, _, __ = knn(inputVector, data)

            result = 1 if target_class == x_test[-1] else 0
            hit += result
        return (hit * 1.0 / test_r)
    else:
        hit = 0
        raw_data = db_session.query(HasilLab).all()
        for x_test in X_test:
            inputVector = x_test[:-1]
            sim, target = knn(inputVector, data)

            result = 1 if target == x_test[-1] else 0
            hit += result
        return (hit * 1.0 / test_r)

class PartResult:
    def __init__(self, tp=0, fp=0, tn=0, fn=0):
        self.tp = tp
        self.fp = fp
        self.tn = tn
        self.fn = fn
        self.acc = None
        self.f1 = None

    def accuracy(self):
        if self.acc is None:
            a = (self.tp + self.tn)
            self.acc = a * 1.0 / (a + self.fn + self.fp)
        return self.acc

    def f1(self):
        if self.f1 is None:
            self.f1 = 1.0
        return self.f1

    def __repr__(self):
        acc = self.accuracy()
        return '%0.2f' % acc

class CVResult:
    def __init__(self, presults):
        self.presults = presults
        self.acc = None

    def accuracy(self):
        if self.acc is None:
            n = len(self.presults)
            tot = sum([ p.accuracy() for p in self.presults ])
            self.acc = tot / n
        return self.acc

def cross_validation(data, cv_p=5, indexing=True):

    def split_data(n_parts=5, data=data):
        parts = [ [] for i in range(n_parts) ]
        for i, x in enumerate(data):
            index = i % n_parts
            parts[index].append(x[:])
        return parts

    def run_smote(data):
        return data[:]

    # Classify x with xs as training set.
    def classify(x, xs, indexing=indexing):
        target_data = xs
        if indexing:
            target_class = nb2(x, xs)
            target_data = [ r for r in xs if r[-1] == target_class ]
        # Damn!! we dont need knn right here.
        # All we needed is the target class.
        sim, label, __ = knn(x, target_data)
        return label

    # Run testing with (trains) as training set
    # ad (tests) as testing set.
    def _run_test(tests, trains):
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for x in tests:
            actual = x[-1]
            system = classify(x, trains)
            # True Positive
            if actual == 1 == system:
                tp += 1
            elif actual == 0 == system:
                tn += 1
            elif (actual == 1) and (system == 0):
                fn += 1
            elif (actual == 0) and (system == 1):
                fp += 1
            else:
                raise Exception('Fuck it! Should not be here!!!')
        pr = PartResult(tp=tp, tn=tn, fp=fp, fn=fn)
        return pr

    results = []
    parts = split_data()
    for i in range(cv_p):
        test_part = parts[i]
        trains = [ parts[j] for j in range(cv_p) if i != j ]
        trains = list(chain(*trains))
        smoted = run_smote(trains)
        results.append( _run_test(test_part, trains) )
    return CVResult(results)

def test_cv():
    # Creating session
    db_session = model.create_session()

    # Load all data.
    all_hasil_lab = db_session.query(HasilLab).all()
    all_dataset = list( map( model.array_from_hl, all_hasil_lab ) )

    results = cross_validation(data=all_dataset, indexing=False)
    
    print(results)


if __name__ == '__main__':
    test_cv()
