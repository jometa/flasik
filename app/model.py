import click
import os
import os.path
import sys
from sqlalchemy import Column, ForeignKey, Integer, Float, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from functools import wraps

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)

class JenisIkan(Base):
    __tablename__ = 'jenis_ikan'
    id = Column(Integer, primary_key=True)
    nama = Column(String(250), nullable=False)

class HasilLab(Base):
    __tablename__ = 'hasil_lab'

    id = Column(Integer, primary_key=True)

    indol = Column(Integer, default=0)
    vp_test = Column(Integer, default=0)
    gram = Column(Integer, default=0)
    oksidase = Column(Integer, default=0)
    gas = Column(Integer, default=0)
    gelatin = Column(Integer, default=0)
    of = Column(Integer, default=0)
    lysine_decarboxilase = Column(Integer, default=0)
    laktosa = Column(Integer, default=0)
    maltosa = Column(Integer, default=0)
    inositol = Column(Integer, default=0)
    nacl0 = Column(Integer, default=0)
    nacl2 = Column(Integer, default=0)
    nacl3 = Column(Integer, default=0)
    nacl4 = Column(Integer, default=0)
    nacl6 = Column(Integer, default=0)
    nacl7 = Column(Integer, default=0)
    nacl8 = Column(Integer, default=0)
    nacl10 = Column(Integer, default=0)
    tsa = Column(Integer, default=0)
    tcbs = Column(Integer, default=0)
    koloni = Column(Integer, default=0)
    butt_a = Column(Integer, default=0)
    urea = Column(Integer, default=0)
    h2s = Column(Integer, default=0)
    katalase = Column(Integer, default=0)
    mr_test = Column(Integer, default=0)
    citrate = Column(Integer, default=0)
    ornithin_decarboxiase = Column(Integer, default=0)
    sukrosa = Column(Integer, default=0)
    arabinosa = Column(Integer, default=0)
    manitol = Column(Integer, default=0)
    glukosa = Column(Integer, default=0)
    motility = Column(Integer, default=0)
    sel = Column(Integer, default=0)
    slant = Column(Integer, default=0)

    # 1 = Positive VA, 0 Negative VA
    kesimpulan = Column(Integer, default=0)

    jenis_ikan_id = Column(Integer, ForeignKey('jenis_ikan.id'))
    jenis_ikan = relationship(JenisIkan)

# DB Name
dbname = 'flasik.db'

# Engine to must  be singleton. Python caching its module.
engine = create_engine('sqlite:///{}'.format(dbname))

# Session Maker must be global scope
DBSession = sessionmaker(autoflush=True)

def seed_data():
    import csv

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
      'nacl6',
      'nacl7',
      'nacl8',
      'nacl10',
      'kesimpulan'
    ]

    with open('app/data-ikan.csv') as f:
        fdata = csv.reader(f)
        result = []
        db_session = create_session()
        for row in fdata:
            hl = HasilLab()
            for index, (d, vraw) in enumerate(zip(desc_columns, row)):
                v = vraw.strip()
                if index == 0:
                    if v == 'J4':
                        setattr(hl, d, 4)
                    elif v == 'J1':
                        setattr(hl, d, 1)
                    elif v == 'J2':
                        setattr(hl, d, 2)
                    elif v == 'J3':
                        setattr(hl, d, 3)
                    else:
                        raise Exception('Unknown jenis_ikan_id')
                

                elif index == (len(row) - 1):
                    if v == 'B1':
                        setattr(hl, d, 1)
                    elif v == 'B0':
                        setattr(hl, d, 0)
                
                else:
                    setattr(hl, d, int(v))

            db_session.add(hl)
        db_session.commit()

# Function to initialize db
# You can call it from flask-cli
@click.command('init-db')
@with_appcontext
def init_db():
    def create_default_user():
        session = create_session()
        user = User(name='admin', password='admin')
        session.add(user)
        session.commit()

    def create_default_jenis_ikan():
        session = create_session()
        for ji in ('Lobster', 'Kepiting', 'Udang', 'Kerapu'):
            ji_obj = JenisIkan(nama=ji)
            session.add(ji_obj)
        session.commit()

    # Remove db
    if (os.path.isfile('flasik.db')):
        os.remove('flasik.db')
        print('Removing db')

    Base.metadata.create_all(engine)
    dbsession = DBSession(bind=engine)
    phash = generate_password_hash('admin')
    user = User(name='admin', password=phash)
    dbsession.add(user)
    dbsession.commit()

    create_default_user()
    create_default_jenis_ikan()
    seed_data()

    print('Database created')

# Create the session and attach it to request context.
def create_session():
    Base.metadata.bind = engine
    session = DBSession(bind=engine)
    return session

# Decorator to inject dbsession into app_context
def dbsession_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        dbsession = g.pop('dbsession', None)
        if dbsession is None:
            g.dbsession = create_session()
        return f(*args, **kwargs)
    return wrap

# Remove the session from request context and close it.
# What the fuck is 'e'
def close_session(e=None):
    session = g.pop('dbsession', None)
    if session is not None:
        session.close()

# Register session lifecycle hook to instance.
# Using function since we use factory.
def init_app(app=None):
    if app is None: raise Exception('App is none!')
    app.teardown_appcontext(close_session)
    app.cli.add_command(init_db)

HASIL_LAB_ATTRS = [
  ('indol', 'radio'),
  ('vp_test', 'radio'),
  ('gram', 'radio'),
  ('oksidase', 'radio'),
  ('gas', 'radio'),
  ('gelatin', 'radio'),
  ('of', 'radio'),
  ('lysine_decarboxilase', 'radio'),
  ('laktosa', 'radio'),
  ('maltosa', 'radio'),
  ('inositol', 'radio'),
  ('nacl0', 'radio'),
  ('nacl2', 'radio'),
  ('nacl3', 'radio'),
  ('nacl4', 'radio'),
  ('nacl6', 'radio'),
  ('nacl7', 'radio'),
  ('nacl8', 'radio'),
  ('nacl10', 'radio'),
  ('tsa', 'select', [
    ( 0, 'Negatif' ),
    ( 1, 'Positif' ),
    ( 2, 'Positif Swarming' )
  ]),
  ('tcbs', 'select', [
    ( 0, 'Yellow' ),
    ( 1, 'Green' ),
    ( 2, 'Negatif' )
  ]),
  ('koloni', 'radio', [
    ( 0, 'Bulat' ),
    ( 1, 'Bulat Konvex' )
  ]),
  ('butt_a', 'radio'),
  ('urea', 'radio'),
  ('h2s', 'radio'),
  ('katalase', 'radio'),
  ('mr_test', 'radio'),
  ('citrate', 'radio'),
  ('ornithin_decarboxiase', 'radio'),
  ('sukrosa', 'radio'),
  ('arabinosa', 'radio'),
  ('manitol', 'radio'),
  ('glukosa', 'select', [
    ( 0, 'Negatif' ),
    ( 1, 'Positif' ),
    ( 2, 'Positif Gas' )
  ]),
  ('motility', 'select', [
    ( 0, 'Negatif' ),
    ( 1, 'Positif' ),
    ( 2, 'Positif H2S' )
  ]),
  ('sel', 'radio', [
    ( 0, 'Batang' ),
    ( 1, 'Bukan Batang' )
  ]),
  ('slant', 'radio', [
    ( 0, 'A' ),
    ( 1, 'K' )
  ])
]

HASIL_LAB_STRUCTURE = [
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


def array_from_hl(hl):
    # jenis ikan 1 to 4
    ji = hl.jenis_ikan_id
    kes = hl.kesimpulan

    attrs = [ getattr(hl, a) for a, *_ in HASIL_LAB_STRUCTURE ]

    # First attribute is jenis_ikan
    data =  [ ji ]
    
    data.extend(attrs)
    # Last attribute is target class
    data.append(kes)
    return data

def hl_from_array(array):
    hl = HasilLab()
    attrs = [ a for a, *_ in HASIL_LAB_STRUCTURE ]

    # Set jenis_ikan and target class.
    hl.jenis_ikan_id = array[0]
    hl.kesimpulan = array[-1]

    del array[0]
    del array[-1]

    for k, v in zip(attrs, array):
        if v is None:
            raise Exception('v is None')
        setattr(hl, k, v)
    return hl

def hasil_lab_pull_attrs(hl):
    attrs = ( attr[0] for attr in HASIL_LAB_ATTRS )
    return [ getattr(hl, attr) for attr in attrs ]
  
def hasil_lab_attrs_view(hl):
    result = []
    for attr in HASIL_LAB_ATTRS:
        raw_val = getattr(hl, attr[0])
        if len(attr) > 2:
            # It has special display
            list_display = attr[2]
            for v, k in list_display:
                if v == raw_val:
                    result.append(k)
        else:
            # Remember!! 1 for positive, 0 for negative
            display_val = '+' if raw_val == 1 else '-'
            result.append(display_val)
    return result

def all_dataset():
    db_session = create_session()
    all_hasil_lab = db_session.query(HasilLab).all()
    all_dataset = list( map( model.array_from_hl, all_hasil_lab ) )
    return all_dataset



if __name__ == '__main__':
    create_default_user()
    create_default_jenis_ikan()