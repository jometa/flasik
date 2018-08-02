from . import model
import math
import random

HasilLab = model.HasilLab
JenisIkan = model.JenisIkan

HASIL_LAB_STRUCTURE = [
  ('jenis_ikan_id', 1, 4),
  ('indol', 0, 1),
  ('vp_test', 0, 1),
  ('gram', 0, 1),
  ('oksidase', 0, 1),
  ('gas', 0, 1),
  ('gelatin', 0, 1),
  ('of', 0, 1),
  ('lysine_decarboxilase', 0, 1),
  ('laktosa', 0, 1),
  ('maltosa', 0, 1),
  ('inositol', 0, 1),
  ('nacl0', 0, 1),
  ('nacl2', 0, 1),
  ('nacl3', 0, 1),
  ('nacl4', 0, 1),
  ('nacl6', 0, 1),
  ('nacl7', 0, 1),
  ('nacl8', 0, 1),
  ('nacl10', 0, 1),
  ('tsa', 0, 2),
  ('tcbs', 0, 2),
  ('koloni', 0, 1),
  ('butt_a', 0, 1),
  ('urea', 0, 1),
  ('h2s', 0, 1),
  ('katalase', 0, 1),
  ('mr_test', 0, 1),
  ('citrate', 0, 1),
  ('ornithin_decarboxiase', 0, 1),
  ('sukrosa', 0, 1),
  ('arabinosa', 0, 1),
  ('manitol', 0, 1),
  ('glukosa', 0, 2),
  ('motility', 0, 2),
  ('sel', 0, 2),
  ('slant', 0, 1)
]

def load_major_minor():
    # Creating session
    db_session = model.create_session()

    # Load all data.
    all_hasil_lab = db_session.query(HasilLab).all()

    # Load minority class, target = 0
    minor_hasil_lab = db_session.query(HasilLab).filter(HasilLab.kesimpulan == 1).order_by(HasilLab.id).all()

    # Convert to array
    minor_dataset = list( map( model.array_from_hl, minor_hasil_lab ) )
    all_dataset = list( map( model.array_from_hl, all_hasil_lab ) )

    return all_dataset, minor_dataset

def smote(N=400, k=7):

    all_dataset, minor_dataset = load_major_minor()

    # Compute distance matrix
    def compute_distances():
        distances = {}
        for index, (attr, low, high) in enumerate(HASIL_LAB_STRUCTURE):

            distances[index] = {}
            for i in range(low, high + 1):
                # Total occurences of feature value-i
                Ci = len([ x for x in all_dataset if x[index] == i ]) + 1

                # Total occurences  of feature value-i in minority class.
                Ci0 = len([ x for x in minor_dataset if x[index] == i ]) + 1

                distances[index][i] = {}

                for j in range(low, high + 1):
                    if i == j:
                        distances[index][i][j] = 1
                        continue
                    # Total occurences of feature value-j
                    Cj = len([ x for x in all_dataset if x[index] == j ]) + 1

                    # Total occurences  of feature value-j in minority class.
                    Cj0 = len([ x for x in minor_dataset if x[index] == j ]) + 1

                    dij = abs(((Ci0 * 1.0) / Ci) - ((Cj0 * 1.0) / Cj))
                    distances[index][i][j] = dij
        return distances  

    # Calculate Value Differences Metric.
    def compute_VDM():
        VDM = [ [ 0 for j in minor_dataset ] for i in minor_dataset ]
        for index, x in enumerate(minor_dataset):
            for index2, y in enumerate(minor_dataset):
                if index == index2: continue

                delta = 0
                for index3, (attr, low, high) in enumerate(HASIL_LAB_STRUCTURE):
                    xval = x[index3]
                    yval = y[index3]
                    delta += pow(distances[index3][xval][yval], 2)
                VDM[index][index2] = delta
        return VDM

    # Function to compute k-nearest neighborhood of vector.
    def knn_min_vector(index, k=2):
        dist = [ 100 for i in range(k) ]
        tmp = list(enumerate(VDM[index]))

        # Remove distance to current position.
        tmp = [ (i, v) for i, v in tmp if i != index ]
        tmp_sorted = sorted(tmp, key=lambda pair: pair[1])

        return [ minor_dataset[i] for i, d in tmp_sorted[:k] ]

    # Return most occured elements in xs
    def max_occ(xs):
        f = lambda x: len([ v for v in xs if v == x ])
        g = lambda x: (x, f(x))
        return sorted(list(map(g, xs)), key=lambda pair: pair[1], reverse=True)[0][0]

    # Generate feature vector based on (xs)
    # Use voting on xs to decide attribute i
    def gen_x(xs):
        return [ max_occ(ais) for ais in zip(*xs) ]

    distances = compute_distances()
    VDM = compute_VDM()

    N_ = N / 100
    USE_MUT = False
    prob_mut = 0.4
    if N_ > k:
        USE_MUT = True
        print('WARNING: With N > k, there is probability that duplication occurs')
    
    synth = []
    T = len(minor_dataset)
    for i in range(T):
        neigh = knn_min_vector(i, k)
        xi = minor_dataset[i]
        ns = N / 100
        while ns > 0:
            # Choose random neighborhood.
            nn = random.randint(2, k)
            rand_neighs = random.sample(neigh, nn)
            rand_neighs.append(xi)
            newins = gen_x(rand_neighs)
            synth.append( newins )
            ns -= 1
    return synth

if __name__ == '__main__':
    for r in smote():
        print('r:', r)
        input()