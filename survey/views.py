import datetime
from flask import render_template, jsonify, request, redirect, json, send_from_directory
from flask.ext.login import login_user, logout_user, current_user
from survey import app
from survey.models import User, Dataset, Question, Activity
from survey.utils import async, store_and_parse_uploaded_file, create_dynamic_images, save_raw_chart_images
from survey.utils import get_graph_data_from_solr


@app.route('/')
def splash():
    return render_template('splash.html', errors=['First error', 'Second error'])


@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
    if user:
        login_user(user, True)
        json_return = jsonify(status='ok')
    else:
        error_template = render_template('errors.html', errors=['Username or password now recognized.'])
        json_return = jsonify(status='error', error_template=error_template)
    return json_return


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/loading')
def loading():
    return render_template('loading.html')


@app.route('/home')
def user_home():
    return render_template('user_home.html')


@app.route('/home/init')
def user_home_init():
    most_recent_activity = Activity.GetLastForUser(current_user)
    if not most_recent_activity:
        no_activity_template = render_template('no_activity.html')
        return jsonify(configuration=None, no_activity_template=no_activity_template)
    return jsonify(
        dataset_id=most_recent_activity.dataset_id,
        dataset_name=most_recent_activity.dataset.display_name,
        configuration=most_recent_activity.configuration)


@app.route('/survey/<dataset_id>')
def survey(dataset_id):
    dataset = Dataset.GetById(dataset_id)
    questions = Question.GetForDataset(dataset)
    return render_template('survey.html', questions=questions)


@app.route('/survey/record_activity', methods=['POST'])
def record_activity():
    dataset_id = request.json['dataset_id']
    configuration = request.json['configuration']
    activity = Activity(current_user, Dataset.GetById(dataset_id), configuration).save()
    dynamic_images_config = save_raw_chart_images(activity.id, configuration)
    create_dynamic_images(activity.id, dynamic_images_config)
    return ''


@app.route('/survey/html/chart_area')
def html_chart_area():
    return render_template('chart_area.html')


@app.route('/survey/html/filters_list')
def html_filters_list():
    return render_template('filters_list.html', count=range(3))


@app.route('/survey/html/empty_capture')
def html_empty_capture():
    return render_template('empty_capture.html')


@app.route('/survey/html/empty_rewind')
def html_empty_rewind():
    return render_template('empty_rewind.html')


@app.route('/survey/get_graph_data', methods=['POST'])
def get_graph_data():
    chart_area_id = request.form.get('chart_area_id')
    search_data = json.loads(request.form.get('search_data'))
    questions = search_data['questions']
    filters = search_data['filters']
    dataset_id = request.form.get('dataset_id')
    return_data = get_graph_data_from_solr(chart_area_id, dataset_id, filters, questions)
    return jsonify(
        graph_type='pie',
        chart_area_id=return_data['chart_area_id'],
        graph_data=return_data['graph_data'],
        graph_colors=return_data['graph_colors'],
        filters=return_data['filters'])


@app.route('/survey/get_activity/<dataset_id>/<count>')
def get_user_activity(dataset_id, count):
    dataset = Dataset.GetById(dataset_id)
    user_activity = Activity.GetForUser(current_user, count, dataset)
    user_activity = [{
        'dataset_id': a.dataset.id,
        'dataset_name': a.dataset.display_name,
        'configuration': a.configuration}
        for a in user_activity]
    user_activity = reversed(user_activity)
    return render_template('activity_list.html', user_activity=user_activity)


@app.route('/survey/capture/<dataset_id>')
def get_capture(dataset_id):
    dataset = Dataset.GetById(dataset_id)
    activity = Activity.GetLastForUser(current_user, dataset)
    if not activity:
        return render_template('empty_capture.html')
    return render_template('capture.html', config=activity.configuration)


@app.route('/survey/capture/download/<activity_id>')
def get_image(activity_id):
    return send_from_directory(
        app.config['DYNAMIC_IMAGES_DIRECTORY'],
        activity_id + ".png",
        as_attachment=True,
        attachment_filename='MetaLayer-Survey-%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


@app.route('/your_datasets')
def your_datasets():
    datasets = Dataset.GetAllActiveForUser(current_user)
    if not datasets:
        return render_template(
            'info.html',
            infos=['You don\'t have any datasets yet, why not add one! <i class="icon-arrow-down"></i>'])
    return render_template('datasets_list.html', datasets=datasets)


@app.route('/add_dataset')
def dataset_manager():
    return render_template('dataset_add.html')


@app.route('/dataset/remove/<dataset_id>')
def remove_dataset(dataset_id):
    Dataset.GetById(dataset_id).deactivate().save()
    return ''


@app.route('/add_dataset/upload_file', methods=['POST'])
@async
def upload_file():
    uploaded_file = request.files['data_upload']
    file_id = request.form['file_id']
    Dataset(file_id, uploaded_file.filename, current_user).save()
    yield ''
    store_and_parse_uploaded_file(file_id, uploaded_file)


@app.route('/add_dataset/upload_file_progress/<file_id>')
def get_progress_for_file(file_id):
    dataset = Dataset.query.filter_by(file_id=file_id).first()
    if not dataset:
        error_message = '''Sorry, there was a system error while trying to process that file, please try again and
            if you still have issues, contact your systems administrator'''
        error_template = render_template('errors.html', errors=[error_message])
        return jsonify(status="error", error_template=error_template)
    if dataset.progress == -1:
        error_messages = dataset.error_messages()
        error_template = render_template('errors.html', errors=error_messages)
        return jsonify(status="error", error_template=error_template)
    return jsonify(status="processing", progress=dataset.progress)


@app.route('/add_dataset/edit_metadata/<file_id>', methods=['GET', 'POST'])
def edit_dataset_metadata(file_id):
    dataset = Dataset.GetByFileId(file_id)
    if request.method == 'POST':
        dataset.display_name = request.form.get('display_name')
        dataset.description = request.form.get('description', None)
        dataset.activate().save()
        return jsonify(dataset_id=dataset.id, dataset_name=dataset.display_name)
    questions = Question.GetAllForDataset(dataset)
    return render_template('dataset_metadata.html', dataset=dataset, questions=questions)
