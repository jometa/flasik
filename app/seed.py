import csv
from model import HasilLab, create_session

desc_columns = [
  'jenis_ikan_id',
  'tsa',
  'tcbs',
  'gram',
  'koloni',
  'sel',
  'motility',
  'katalase',
  'oksidase',
  'butt',
  'slant',
  'h2s',
  'gas',
  'indol',
  'mr_test',
  'vp_test',
  'citrate',
  'urea',
  'of',
  'gelatin',
  'lysine_decarboxilase',
  'ornithin_decarboxiase',
  'glukosa',
  'sukrosa',
  'laktosa',
  'arabinosa',
  'maltosa',
  'manitol',
  'inositol',
  'nacl0',
  'nacl2',
  'nacl3',
  'nacl4',
  'nacl7',
  'nacl8',
  'nacl10',
  'kesimpulan'
]

with open('data-ikan.csv') as f:
    fdata = csv.reader(f)
    result = []
    db_session = create_session()
    for row in fdata:
        hl = HasilLab()
        for index, (d, v) in enumerate(zip(desc_columns, row)):
            if index == 0:
                if v == 'J4':
                    setattr(hl, d, 4)
                elif v == 'J1':
                    setattr(hl, d, 1)
                elif v == 'J2':
                    setattr(hl, d, 2)
                elif v == 'J3':
                    setattr(hl, d, 3)
                continue
            elif index == (len(desc_columns) - 1):
                if v == 'B1':
                    setattr(hl, d, 1)
                elif v == 'B2':
                    setattr(hl, d, 0)
                continue
            setattr(hl, d, int(v))
            db_session.add(hl)
    db_session.commit()