# Import what we need
import functools
import random
import time
from flask import (
  Blueprint, flash, g, redirect, render_template,
  request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from .model import (
  User, HasilLab, JenisIkan, dbsession_required, HASIL_LAB_ATTRS,
  hasil_lab_attrs_view, array_from_hl, hl_from_array,
  HASIL_LAB_STRUCTURE
)
from .auth import login_required
from .knn import knn
from .nb import nb2
from .testing import test_all_with_indexing
from . import testing
from . import smote

bp = Blueprint('app', __name__, url_prefix='/app')

@bp.route('/')
@login_required
def appIndex():
    return render_template('app/index.html', uname=session['username'])

@bp.route('/data/list')
@dbsession_required
@login_required
def data():
    hasil_lab_attrs_only = [ attr[0] for attr in HASIL_LAB_ATTRS ]
    db_session = g.get('dbsession')
    list_hasil_lab = db_session.query(HasilLab, JenisIkan)\
                        .filter(HasilLab.jenis_ikan_id == JenisIkan.id)\
                        .all()
    return render_template('app/data-list.html',
      list_hasil_lab=list_hasil_lab,
      hasil_lab_attrs_only=hasil_lab_attrs_only,
      hasil_lab_attrs_view=hasil_lab_attrs_view)

@bp.route('/data/tambah', methods=['GET'])
@dbsession_required
@login_required
def appDataTambahView():
    db_session = g.get('dbsession')
    list_jenis_ikan = db_session.query(JenisIkan).all()
    return render_template('app/data-tambah.html', 
      uname=session['username'], 
      attrs=HASIL_LAB_ATTRS,
      list_jenis_ikan=list_jenis_ikan)

@bp.route('/data/edit', methods=['GET'])
@dbsession_required
@login_required
def appDataEditView():
    data_id = request.args['id']
    db_session = g.get('dbsession')
    list_jenis_ikan = db_session.query(JenisIkan).all()
    hl = db_session.query(HasilLab).filter(HasilLab.id == int(data_id)).first()

    # Get attributes with radio control and two values options.
    radio_2vals = [ pair for pair in HASIL_LAB_ATTRS if pair[1] == 'radio' and len(pair) == 2 ]

    # Get attributes with radio control and more than 2 values options.
    radio_multi = [ pair for pair in HASIL_LAB_ATTRS if pair[1] == 'radio' and len(pair) > 2 ]

    # Get attributes with select control and more than 2 values options.
    select_attrs = [ pair for pair in HASIL_LAB_ATTRS if pair[1] != 'radio' and len(pair) > 2 ]

    return render_template('app/data-edit.html',
      list_jenis_ikan=list_jenis_ikan,
      hl=hl,
      radio_2vals=radio_2vals,
      radio_multi=radio_multi,
      select_attrs=select_attrs,
      getattr=getattr) # Passing gettatr. because jinja hide it somehow.

@bp.route('/klasifikasi', methods=['GET'])
@dbsession_required
@login_required
def appKlasifikasiView():
    db_session = g.get('dbsession')
    list_jenis_ikan = db_session.query(JenisIkan).all()

    return render_template('app/klasifikasi.html', 
      uname=session['username'], 
      attrs=HASIL_LAB_ATTRS,
      list_jenis_ikan=list_jenis_ikan)

@bp.route('/klasifikasi', methods=['POST'])
@dbsession_required
@login_required
def appKlasifikasiProses():
    kw_hl_attrs = {
      it[0]: int(request.form[it[0]])
      for it in HASIL_LAB_ATTRS
    }
    hl = HasilLab(
      jenis_ikan_id=int(request.form['jenis_ikan_id']),
      # Now insert the remaining attributes
      **kw_hl_attrs)


    db_session = g.get('dbsession')
    hl = db_session.query(HasilLab).filter(HasilLab.kesimpulan == 1).first()
    # hl.indol = 0
    # hl.vp_test = 1
    raw_data = db_session.query(HasilLab).all()
    data = list(map(array_from_hl, raw_data))
    inputVector = array_from_hl(hl)[:-1]

    target_class = nb2(inputVector, data)

    # Find instance on target_class
    raw_data = db_session.query(HasilLab).filter(HasilLab.kesimpulan == target_class).all()
    data = list(map(array_from_hl, raw_data))
    sim, _, instance = knn(inputVector, data)

    # Convert array instance to HasilLab entity
    hl_knn = hl_from_array(instance)

    # Make tuple of attribute name and value
    most_sim_ins = [ (a, getattr(hl_knn, a), getattr(hl, a)) for a, *_ in HASIL_LAB_STRUCTURE ]

    # Save new case
    hl.kesimpulan = target_class
    db_session.add(hl)
    db_session.commit()

    kesimpulan = 'Positif ' if target_class == 1 else 'Negatif '
    kesimpulan += 'Vibrio Alginolytcus'

    return render_template('app/klasifikasi-result.html',
      sim=sim,
      kesimpulan=kesimpulan,
      most_sim_ins=most_sim_ins)


@bp.route('/testing', methods=['GET'])
@dbsession_required
@login_required
def appTestingView():
    return render_template('app/testing.html')

@bp.route('/testing', methods=['POST'])
@dbsession_required
@login_required
def appTestProcess():
    indexing = request.form['test-type'] == 'nb'
    npart = int(request.form['npart'])
    nsmote = int(request.form['nsmote']) * 100

    db_session = g.get('dbsession')
    all_hasil_lab = db_session.query(HasilLab).all()
    all_dataset = list( map( array_from_hl, all_hasil_lab ) )
    # Get synthetic data from smote
    smoted = smote.smote(N=nsmote)
    dataset = all_dataset + smoted
    random.shuffle(dataset)

    t0 = time.time()
    cv_result = testing.cross_validation(dataset, indexing=indexing, cv_p=npart)
    t1 = time.time()
    ttime =  t1 - t0

    return render_template('app/testing-result.html', 
      indexing=indexing, ttime=ttime, cv=cv_result)
