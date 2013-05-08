import StringIO
import os
import time
import csv
import re
from PIL import Image
import solr
import cairo
from random import randint
from threading import Thread
from hashlib import md5
from chardet.universaldetector import UniversalDetector
from survey import login_manager, app
from survey.models import User, Dataset, Question


#Flask-Login Functions
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


#Async function processing
def async(gen):
    def func(*args, **kwargs):
        it = gen(*args, **kwargs)
        result = it.next()
        Thread(target=lambda: list(it)).start()
        return result

    return func


class UnicodeCsvReader(object):
    # http://stackoverflow.com/questions/1846135/python-csv-library-with-unicode-utf-8-support-that-just-works
    chunk_size = 24576  # in bytes

    def __init__(self, f, encoding=None, **kwargs):
        if not encoding:
            chardet_detector = UniversalDetector()
            chardet_detector.reset()
            chunk = f.read(self.chunk_size)
            chardet_detector.feed(chunk)
            chardet_detector.close()
            chardet_encoding = chardet_detector.result['encoding']
            encoding = chardet_encoding if chardet_encoding and not chardet_encoding == 'ascii' else 'utf-8'
            f.seek(0)
        self.csv_reader = csv.reader(f, **kwargs)
        self.encoding = encoding

    def __iter__(self):
        return self

    def next(self):
        # read and split the csv row into fields
        row = self.csv_reader.next()
        # now decode
        return [unicode(cell, self.encoding).encode('ascii', 'ignore') for cell in row]

    @property
    def line_num(self):
        return self.csv_reader.line_num


class UnicodeDictReader(csv.DictReader):
    def __init__(self, f, encoding="utf-8", fieldnames=None, **kwds):
        csv.DictReader.__init__(self, f, fieldnames=fieldnames, **kwds)
        self.reader = UnicodeCsvReader(f, encoding=encoding, **kwds)


def can_parse_based_on_test_pass(file_object):
    def _first_row_is_header(rows):
        if max([len(r) for r in rows]) > len(rows[0]):  # No row is longer
            return False, ['At least one other row is longer than the header row']
        if len([c for c in rows[0] if not isinstance(c, basestring)]):  # all are strings
            return False, ['At least one header value is not a string']
        passed = failed = 0.0
        for x in range(1, len(rows)):
            for y in range(len(rows[0])):
                try:
                    column_value = rows[x][y]
                except IndexError:
                    continue
                if rows[0][y] == column_value:
                    failed += 1
                else:
                    passed += 1
        if not passed or failed / passed > 0.10:
            return False, ['The header names must be unique throughout the column they represent']
        return True, []

    try:
        file_as_csv = UnicodeCsvReader(file_object)
        first_ten_rows = []
        for row in file_as_csv:
            first_ten_rows.append(row)
            if len(first_ten_rows) > 9:
                break
    except Exception as e:
        return ['The file you uploaded is not a CSV file.']

    if len(first_ten_rows) < 3:
        return ['There is not enough data in this file.']

    if len([r for r in first_ten_rows if not r or not len([c for c in r if c])]):
        return ['No rows in the file can be empty.']

    first_row_is_header, errors = _first_row_is_header(first_ten_rows)
    if not first_row_is_header:
        return ['The first row did not contain column headers:'] + errors
    return None


def read_file_and_return_content(file_object):
    def _clean_row(row):
        common_none_values = ['none', 'n/a', 'n/d', 'null']
        for column_count in range(len(row)):
            if isinstance(row[column_count], basestring):
                if row[column_count].lower() in common_none_values:
                    row[column_count] = None
        return row

    def _is_text_facet_column(content_rows, column):
        values = {}
        for row in range(len(content_rows)):
            value = content_rows[row][column]
            if not value:
                continue
            if value in values.keys():
                values[value] += 1
            else:
                values[value] = 1
        if values and max([count for count in values.values()]) > 1 < len(values):
            return True
        return False

    def _create_facet_name_from_column_header(column_header):
        is_character = re.compile('^[a-z]$')
        column_header = column_header.lower()
        only_word_characters = ''.join([c for c in column_header if is_character.search(c)])
        return only_word_characters + "_s"

    all_rows = [r for r in UnicodeCsvReader(file_object)]
    header_objects = [{'name': c, 'facet_name': _create_facet_name_from_column_header(c)} for c in all_rows[0]]
    item_rows = [_clean_row(r) for r in all_rows[1:] if r]
    items = []

    for column in range(len(header_objects)):
        header = header_objects[column]
        if _is_text_facet_column(item_rows, column):
            header['type'] = 'text_facet'
            continue
        header['type'] = 'unknown'

    for row in item_rows:
        item = {}
        for column_count in range(len(header_objects)):
            if not row[column_count]:
                continue
            column_header = header_objects[column_count]
            if column_header['type'] == 'unknown':
                continue
            item[column_header['facet_name']] = row[column_count]
        items.append(item)

    return header_objects, items


def send_content_to_solr(items, file_id):
    solr_connection = solr.SolrConnection('http://dashboard.metalayer.com:8080/solr/')
    for item in items:
        item['file_id_s'] = file_id
        item['scope_s'] = 'survey'
        item['id'] = md5('%f - %i' % (time.time(), randint(0, 1000000))).hexdigest()
        try:
            solr_connection.add_many([item], _commit=True)
        except Exception as e:
            pass
    #solr_connection.add_many(items, _commit=True)


def generate_color_pallet(number_needed, color='green'):
    if color == 'orange':
        start_rgb = (255, 146, 1)
        end_rgb = (193, 78, 23)
    elif color == 'blue':
        start_rgb = (0, 185, 255)
        end_rgb = (38, 81, 98)
    elif color == 'grey':
        return ['#00adee' for x in range(number_needed)]
    else:
        start_rgb = (216, 229, 39)
        end_rgb = (112, 120, 21)
    gaps = ((start_rgb[0] - end_rgb[0]) / number_needed, (start_rgb[1] - end_rgb[1]) / number_needed,
            (start_rgb[2] - end_rgb[2]) / number_needed)
    colors = []
    for x in range(number_needed):
        colors.append(((start_rgb[0] - (gaps[0] * x)), (start_rgb[1] - (gaps[1] * x)), (start_rgb[2] - (gaps[2] * x))))
    return ['#' + format((c[0] << 16) | (c[1] << 8) | c[2], '06x') for c in colors]


def get_graph_data_from_solr(chart_area_id, file_id, filters, questions):
    def stringify_label(label):
        if label.isdigit():
            return '&nbsp;%s' % label
        return label

    return_data = {'chart_area_id': chart_area_id, 'graph_data': {}, 'filters': {}}
    query = 'file_id_s:%s' % file_id
    if len([f for f in filters if 'facet_value' in f and f['facet_value']]):
        query += ' AND ' + ' AND '.join(
            '%s:"%s"' % (f['facet_name'], f['facet_value'])
            for f in filters if 'facet_value' in f and f['facet_value'])

    return_data['graph_type'] = 'pie'
    facet_names = [q['facet_name'] for q in questions]
    facet_names += [f['facet_name'] for f in filters]

    solr_connection = solr.SolrConnection('http://dashboard.metalayer.com:8080/solr/')
    results = solr_connection.select(query, row=0, facet='true', facet_field=facet_names, facet_limit=100)

    for question in questions:
        facet_name = question['facet_name']
        graph_dict = results.facet_counts['facet_fields'][facet_name]
        sum_of_values = sum(v for v in graph_dict.values()) or 1
        graph_data = [
            {'label': stringify_label(key), 'value': int(100 * (float(value) / sum_of_values))}
            for key, value in graph_dict.items()]
        graph_data = sorted(graph_data, key=lambda x: x['value'], reverse=True)
        graph_data = graph_data[:10]
        graph_data = sorted(graph_data, key=lambda x: x['label'])
        return_data['graph_data'] = {
            'key': question['display_name'],
            'values': [[g['label'], g['value']] for g in graph_data],
            'labels': ['%s : %i%s' % (g['label'], g['value'], "%") for g in graph_data]}
        return_data['graph_colors'] = generate_color_pallet(
            len(graph_data),
            'green' if chart_area_id == 'chart-area-one' else 'orange')
        for f in filters:
            filter_facet_name = f['facet_name']
            filter_graph_dict = results.facet_counts['facet_fields'][filter_facet_name]
            sum_of_values = sum(v for v in filter_graph_dict.values()) or 1
            filter_graph_data = [{'label': stringify_label(key),
                                  'value': int(100 * (float(value) / sum_of_values))}
                                 for key, value in filter_graph_dict.items()]
            filter_graph_data = sorted(filter_graph_data, key=lambda x: x['value'], reverse=True)
            filter_graph_data = filter_graph_data[:10]
            filter_graph_data = sorted(filter_graph_data, key=lambda x: x['label'], reverse=True)
            return_data['filters'][filter_facet_name] = {
                'key': f['display_name'],
                'colors': generate_color_pallet(len(filter_graph_data), 'blue') if not (
                    'facet_value' in f and f['facet_value']) else generate_color_pallet(len(filter_graph_data), 'grey'),
                'values': [[g['label'], g['value']] for g in filter_graph_data],
                'labels': ['%s : %i%s' % (g['label'], g['value'], "%") for g in filter_graph_data],
                'is_selected': bool('facet_value' in f and f['facet_value'])}
    return return_data


def store_and_parse_uploaded_file(file_id, uploaded_file):
    try:
        pass
        #uploaded_file.save(os.path.join(app.config['DATASET_UPLOAD_DIRECTORY'], file_id))
    except Exception as e:
        Dataset.GetByFileId(file_id).update_progress(-1, [e]).save()
        return
    Dataset.GetByFileId(file_id).update_progress(1).save()  # Update the progress to show saved
    try:
        parse_errors = can_parse_based_on_test_pass(
            uploaded_file)  # Find out if this this kind of file we can work with
    except Exception as e:
        Dataset.GetByFileId(file_id).update_progress(-1, [e]).save()
        return
    if parse_errors:
        Dataset.GetByFileId(file_id).update_progress(-1, parse_errors).save()
        return
    Dataset.GetByFileId(file_id).update_progress(2).save()  # Update the progress to passed parse tests
    try:
        headers, items = read_file_and_return_content(
            uploaded_file)  # Read the file and get the headers and the content
    except Exception as e:
        Dataset.GetByFileId(file_id).update_progress(-1, [e]).save()
        return
    dataset = Dataset.GetByFileId(file_id)
    for index in range(len(headers)):
        header = headers[index]
        question = Question(index, header['name'], header['facet_name'], header['type'], dataset)
        if header['type'] == 'text_facet':
            question.activate()
        question.save()
    dataset.update_progress(3).save()  # Update the progress to read content
    try:
        send_content_to_solr(items, file_id)
    except Exception as e:
        Dataset.GetByFileId(file_id).update_progress(-1, [e]).save()
        return
    Dataset.GetByFileId(file_id).update_progress(4).save()  # Update the progress to saved file to solr


def save_raw_chart_images(activity_id, configuration):
    dynamic_images_config = {
        'dataset_name': configuration.get('dataset_name', 'No Name'),
        'chart_area_one': {'is_empty': True},
        'chart_area_two': {'is_empty': True}}
    for side in ['chart_area_one', 'chart_area_two']:
        chart_area = configuration.get(side, None)
        if not chart_area or chart_area['is_empty']:
            continue
        main_chart = chart_area['main_question'].get('chart', None)
        if main_chart:
            main_chart_file_name = '%s_%s_main_chart.png' % (activity_id, side)
            write_image_to_disk(main_chart, main_chart_file_name)
            dynamic_images_config[side] = {
                'is_empty': False,
                'main_question': {
                    'display_name': chart_area['main_question'].get('display_name', ''),
                    'chart_file_name': main_chart_file_name},
                'filters': []}
            for x in range(len(chart_area['filters'])):
                subject_filter = chart_area['filters'][x]
                if subject_filter['is_empty']:
                    continue
                filter_chart_file_name = '%s_%s_filter_image_%i.png' % (activity_id, side, x + 1)
                write_image_to_disk(subject_filter['chart'], filter_chart_file_name)
                dynamic_images_config[side]['filters'].append({
                    'facet_name': subject_filter['facet_name'],
                    'facet_value': subject_filter.get('facet_value', None),
                    'display_name': subject_filter['display_name'],
                    'chart_file_name': filter_chart_file_name})
    return dynamic_images_config


def create_dynamic_images(activity_id, dynamic_images_config):
    def paint_words_within_bounds(context, text, font_size, font_color, bounds_width, bounds_height, top, right):
        context.set_font_size(font_size)
        context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        context.set_source_rgb(*font_color)
        text_pieces = text.split(' ')
        words_used = 0
        row_count = 0
        number_of_words = len(text_pieces)
        while words_used < number_of_words:
            row_words = []
            while context.text_extents(' '.join(row_words))[2] <= bounds_width and words_used < number_of_words:
                row_words.append(text_pieces[words_used])
                words_used += 1
            if context.text_extents(' '.join(row_words))[2] > bounds_width:
                row_words = row_words[:-1]
                words_used -= 1
            context.move_to(right, top + (row_count * int(font_size * 1.5)))
            context.show_text(' '.join(row_words))
            row_count += 1
            if row_count == 1:
                words_used -= 1

    rgb_colors = {
        'light_great_background': (0.98, 0.98, 0.98),  # #FBFBFB
        'dark_grey_header': (0.1, 0.1, 0.1),  # #1B1B1B
        'white': (1.0, 1.0, 1.0),  # #FFFFFF
        'grey': (0.6, 0.6, 0.6),  # #999999
    }

    #Draw the basic page
    page_width = 1200  # 16 x 9 aspect ratio
    page_height = 675
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, page_width, page_height)
    context = cairo.Context(surface)
    #Paint the page background
    context.set_source_rgb(*rgb_colors['light_great_background'])
    context.rectangle(0, 0, page_width, page_height)
    context.fill()
    #Paint the page header
    header_height = 40
    context.set_source_rgb(*rgb_colors['dark_grey_header'])
    context.rectangle(0, 0, page_width, header_height)
    context.fill()
    #Draw the title
    context.set_font_size(18)
    context.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    context.set_source_rgb(*rgb_colors['grey'])
    context.move_to(20, 28)
    context.show_text('MetaLayer - Survey > ' + dynamic_images_config['dataset_name'])

    #Pain the chart areas with data is there is any
    gap_between_chart_areas = 40
    chart_areas_template = {
        'file_name': os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/img/template_chart_area.png'),
        'height': 500,
        'width': 558
    }
    chart_areas_top = int(float(page_height - chart_areas_template['height']) / 2)
    chart_area_one_config = {
        'top': chart_areas_top,
        'right': int(float(page_width - (chart_areas_template['width'] * 2) - gap_between_chart_areas) / 2),
        'data': dynamic_images_config['chart_area_one']}
    chart_area_two_config = {
        'top': chart_areas_top,
        'right': chart_area_one_config['right'] + chart_areas_template['width'] + gap_between_chart_areas,
        'data': dynamic_images_config['chart_area_two']}
    for chart_area_config in [chart_area_one_config, chart_area_two_config]:
        #Paint the chart area template
        image_surface = cairo.ImageSurface.create_from_png(chart_areas_template['file_name'])
        context.set_source_surface(image_surface, chart_area_config['right'], chart_area_config['top'])
        context.paint()
        if chart_area_config['data']['is_empty']:
            continue
        #Paint the main chart
        main_chart_top = chart_area_config['top'] + 15
        main_chart_right = chart_area_config['right'] + 190
        file_name = chart_area_config['data']['main_question']['chart_file_name']
        file_path = os.path.join(app.config['DYNAMIC_IMAGES_DIRECTORY'], file_name)
        image_surface = cairo.ImageSurface.create_from_png(file_path)
        context.set_source_surface(image_surface, main_chart_right, main_chart_top)
        context.paint()
        #Paint the main question
        paint_words_within_bounds(
            context, chart_area_config['data']['main_question']['display_name'], 10,
            rgb_colors['white'], 150, 100, chart_area_config['top'] + 160,
            chart_area_config['right'] + 25)
        #Paint the filters
        for filter_x in range(len(chart_area_config['data']['filters'])):
            filters_top = chart_area_config['top'] + 370
            filters_right = chart_area_config['right'] + [40, 212, 384][filter_x]
            file_name = chart_area_config['data']['filters'][filter_x]['chart_file_name']
            file_path = os.path.join(app.config['DYNAMIC_IMAGES_DIRECTORY'], file_name)
            image_surface = cairo.ImageSurface.create_from_png(file_path)
            context.set_source_surface(image_surface, filters_right, filters_top)
            context.paint()
            paint_words_within_bounds(
                context, chart_area_config['data']['filters'][filter_x]['display_name'], 9,
                rgb_colors['white'], 150, 100, filters_top, filters_right)

    #Write out the image to file
    string_io = StringIO.StringIO()
    surface.write_to_png(string_io)
    string_io.seek(0)
    file_name = '%s.png' % activity_id
    image_path = os.path.join(app.config['DYNAMIC_IMAGES_DIRECTORY'], file_name)
    output = open(image_path, 'wb')
    output.write(string_io.read())
    output.close()

    #Create thumbnails
    image = Image.open(image_path)
    size = (int(float(page_width) / 2), (int(float(page_height) / 2)))
    image.thumbnail(size, Image.ANTIALIAS)
    image.save(image_path.replace('.png', '_medium.png'))
    size = (int(float(page_width) / 4), (int(float(page_height) / 4)))
    image.thumbnail(size, Image.ANTIALIAS)
    image.save(image_path.replace('.png', '_small.png'))


def write_image_to_disk(image_data, file_name):
    file_path = os.path.join(app.config['DYNAMIC_IMAGES_DIRECTORY'], file_name)
    image_string = re.search(r'base64,(.*)', image_data).group(1)
    output = open(file_path, 'wb')
    output.write(image_string.decode('base64'))
    output.close()
