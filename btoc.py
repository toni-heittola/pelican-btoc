# -*- coding: utf-8 -*-
"""
Dynamic TOC -- BTOC
========================
Author: Toni Heittola (toni.heittola@gmail.com)

"""

import os
import shutil
import logging
import copy
from bs4 import BeautifulSoup
from jinja2 import Template
from pelican import signals, contents
import re

logger = logging.getLogger(__name__)
__version__ = '0.1.0'

btoc_default_settings = {
    'levels': [1, 2],
    'panel_color': 'panel-primary',
    'header': 'Content',
    'template': """
        <div class="btoc-container hidden-print" role="complementary">
            <div class="panel {{panel_color}}">
                <div class="panel-heading">
                    <h3 class="panel-title">{{toc_header}}</h3>
                </div>
                {{ toc }}
            </div>
        </div>
    """,
    'show': False,
    'minified': True,
    'generate_minified': False,
    'site-url': ''
}

btoc_settings = copy.deepcopy(btoc_default_settings)


def btoc(content):
    """
    Main processing

    """

    if isinstance(content, contents.Static):
        return

    soup = BeautifulSoup(content._content, 'html.parser')

    btoc_settings['levels'].sort()

    heading_regex = '|'.join([str(level) for level in btoc_settings['levels']])
    search = re.compile('^h(%s)$' % (heading_regex))
    headings = soup.findAll(search)

    headers = []
    tocc = []

    for heading in headings:
        this_num = int(heading.name[-1])
        title = None
        if heading.string:
            title = heading.string.strip()

        elif heading.img:
            title = heading.img.get('alt', None)
            if not title:
                title = heading.img.get('title', None)
        if title:
            title = title.strip()
            anchor = title.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '')
            if anchor not in headers:
                headers.append(anchor)

            else:
                id = 1
                for item in headers:
                    if item.startswith(anchor+'-'):
                        id += 1
                anchor += '-' + str(id)
                headers.append(anchor)

            heading['id'] = anchor
            tocc.append({
                'level': this_num,
                'anchor': anchor,
                'title': title
            })

    toc_html = "\n"+'<ul class="nav btoc-nav">'+"\n"
    for i in range(0, len(tocc)):
        toc_html += tocc[i]['level']*" " + "<li>"
        toc_html += '<a href="#' + tocc[i]['anchor'] + '">' + tocc[i]['title'] + '</a>'

        if (i+1) < len(tocc):
            next_i = i+1

        else:
            next_i = i

        if tocc[next_i]['level'] == tocc[i]['level'] or tocc[next_i]['level'] < tocc[i]['level']:
            toc_html += "</li>\n"

        if tocc[next_i]['level'] > tocc[i]['level']:
            for i in range(0, tocc[next_i]['level']-tocc[i]['level']):
                toc_html += "\n"+tocc[next_i]['level']*" " + '<ul>'+"\n"

        elif tocc[next_i]['level'] < tocc[i]['level']:
            for i in range(0, tocc[i]['level']-tocc[next_i]['level']):
                toc_html += tocc[next_i]['level']*" " + "</ul>\n"
                toc_html += tocc[next_i]['level']*" " + "</li>\n"

    toc_html += '</ul>'+"\n"

    toc_element_default = None
    if not toc_element_default:  # [TOC]
        toc_element_default = soup.find(text='[TOC]')

        if toc_element_default:
            btoc_settings['show'] = True

    if not toc_element_default:  # default Markdown reader
        toc_element_default = soup.find('div', class_='toc')

        if toc_element_default:
            btoc_settings['show'] = True

    if not toc_element_default:  # default reStructuredText reader
        toc_element_default = soup.find('div', class_='contents topic')

        if toc_element_default:
            btoc_settings['show'] = True

    if not toc_element_default:  # Pandoc reader
        toc_element_default = soup.find('nav', id='TOC')

        if toc_element_default:
            btoc_settings['show'] = True

    if btoc_settings['show']:
        if btoc_settings['minified']:
            html_elements = {
                'js_include': [
                    '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/btoc.min.js"></script>'
                ],
                'css_include': [
                    '<link rel="stylesheet" href="'+btoc_default_settings['site-url']+'/theme/css/btoc.min.css">'
                ]
            }

        else:
            html_elements = {
                'js_include': [
                    '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/btoc.js"></script>'
                ],
                'css_include': [
                    '<link rel="stylesheet" href="'+btoc_default_settings['site-url']+'/theme/css/btoc.css">'
                ]
            }

        if u'scripts' not in content.metadata:
            content.metadata[u'scripts'] = []

        for element in html_elements['js_include']:
            if element not in content.metadata[u'scripts']:
                content.metadata[u'scripts'].append(element)

        if u'styles' not in content.metadata:
            content.metadata[u'styles'] = []

        for element in html_elements['css_include']:
            if element not in content.metadata[u'styles']:
                content.metadata[u'styles'].append(element)

        if toc_element_default:
            toc_element_default.extract()  # remove from tree

        template = Template(btoc_settings['template'].strip('\t\r\n').replace('&gt;', '>').replace('&lt;', '<'))

        toc_element2 = BeautifulSoup(
            template.render(
                toc=toc_html,
                panel_color=btoc_settings['panel_color'],
                toc_header=btoc_settings['header']
            )
            , "html.parser"
        )

        content._content = soup.decode()
        content.toc = toc_element2.decode()


def process_page_metadata(generator, metadata):
    """
    Process page metadata and assign css and styles

    """
    global btoc_settings
    btoc_settings = copy.deepcopy(btoc_default_settings)  # page wise settings

    if u'styles' not in metadata:
        metadata[u'styles'] = []
    if u'scripts' not in metadata:
        metadata[u'scripts'] = []

    if u'btoc' in metadata and metadata['btoc'] == 'True':
        btoc_settings['show'] = True

    else:
        btoc_settings['show'] = False

    if u'btoc_levels' in metadata:
        btoc_settings['levels'] = map(int, metadata['btoc_levels'].split(','))

    if u'btoc_panel_color' in metadata:
        btoc_settings['panel_color'] = metadata['btoc_panel_color']

    if u'btoc_header' in metadata:
        btoc_settings['header'] = metadata['btoc_header']


def move_resources(gen):
    """
    Move files from js/css folders to output folder, use minified files.

    """

    plugin_paths = gen.settings['PLUGIN_PATHS']
    if btoc_settings['minified']:
        if btoc_settings['generate_minified']:
            minify_css_directory(gen=gen, source='css', target='css.min')
            minify_js_directory(gen=gen, source='js', target='js.min')

        css_target = os.path.join(gen.output_path, 'theme', 'css', 'btoc.min.css')
        if not os.path.exists(os.path.join(gen.output_path, 'theme', 'css')):
            os.makedirs(os.path.join(gen.output_path, 'theme', 'css'))

        js_target = os.path.join(gen.output_path, 'theme', 'js', 'btoc.min.js')
        if not os.path.exists(os.path.join(gen.output_path, 'theme', 'js')):
            os.makedirs(os.path.join(gen.output_path, 'theme', 'js'))

        for path in plugin_paths:
            css_source = os.path.join(path, 'pelican-btoc', 'css.min', 'btoc.min.css')
            js_source = os.path.join(path, 'pelican-btoc', 'js.min', 'btoc.min.js')

            if os.path.isfile(css_source):  # and not os.path.isfile(css_target):
                shutil.copyfile(css_source, css_target)

            if os.path.isfile(js_source):  # and not os.path.isfile(js_target):
                shutil.copyfile(js_source, js_target)

            if os.path.isfile(css_target) and os.path.isfile(js_target):
                break
    else:
        css_target = os.path.join(gen.output_path, 'theme', 'css', 'btoc.css')
        if not os.path.exists(os.path.join(gen.output_path, 'theme', 'css')):
            os.makedirs(os.path.join(gen.output_path, 'theme', 'css'))

        js_target = os.path.join(gen.output_path, 'theme', 'js', 'btoc.js')
        if not os.path.exists(os.path.join(gen.output_path, 'theme', 'js')):
            os.makedirs(os.path.join(gen.output_path, 'theme', 'js'))

        for path in plugin_paths:
            css_source = os.path.join(path, 'pelican-btoc', 'css', 'btoc.css')
            js_source = os.path.join(path, 'pelican-btoc', 'js', 'btoc.js')

            if os.path.isfile(css_source):  # and not os.path.isfile(css_target):
                shutil.copyfile(css_source, css_target)

            if os.path.isfile(js_source):  # and not os.path.isfile(js_target):
                shutil.copyfile(js_source, js_target)

            if os.path.isfile(css_target) and os.path.isfile(js_target):
                break


def minify_css_directory(gen, source, target):
    """
    Move CSS resources from source directory to target directory and minify. Using rcssmin.

    """
    import rcssmin

    plugin_paths = gen.settings['PLUGIN_PATHS']
    for path in plugin_paths:
        source_ = os.path.join(path, 'pelican-btoc', source)
        target_ = os.path.join(path, 'pelican-btoc', target)

        if os.path.isdir(source_):
            if not os.path.exists(target_):
                os.makedirs(target_)

            for root, dirs, files in os.walk(source_):
                for current_file in files:
                    if current_file.endswith(".css"):
                        current_file_path = os.path.join(root, current_file)
                        with open(current_file_path) as css_file:
                            with open(os.path.join(target_, current_file.replace('.css', '.min.css')), "w") as minified_file:
                                minified_file.write(rcssmin.cssmin(css_file.read(), keep_bang_comments=True))


def minify_js_directory(gen, source, target):
    """
    Move JS resources from source directory to target directory and minify.

    """

    from jsmin import jsmin

    plugin_paths = gen.settings['PLUGIN_PATHS']
    for path in plugin_paths:
        source_ = os.path.join(path, 'pelican-btoc', source)
        target_ = os.path.join(path, 'pelican-btoc', target)

        if os.path.isdir(source_):
            if not os.path.exists(target_):
                os.makedirs(target_)

            for root, dirs, files in os.walk(source_):
                for current_file in files:
                    if current_file.endswith(".js"):
                        current_file_path = os.path.join(root, current_file)
                        with open(current_file_path) as js_file:
                            with open(os.path.join(target_, current_file.replace('.js', '.min.js')), "w") as minified_file:
                                minified_file.write(jsmin(js_file.read()))


def init_default_config(pelican):
    """
    Handle settings from pelicanconf.py

    """

    btoc_default_settings['site-url'] = pelican.settings['SITEURL']

    if 'BTOC_LEVELS' in pelican.settings:
        btoc_default_settings['levels'] = pelican.settings['BTOC_LEVELS']

    if 'BTOC_PANEL_COLOR' in pelican.settings:
        btoc_default_settings['panel_color'] = pelican.settings['BTOC_PANEL_COLOR']

    if 'BTOC_HEADER' in pelican.settings:
        btoc_default_settings['header'] = pelican.settings['BTOC_HEADER']

    if 'BTOC_TEMPLATE' in pelican.settings:
        btoc_default_settings['template'] = pelican.settings['BTOC_TEMPLATE']

    if 'BTOC_MINIFIED' in pelican.settings:
        btoc_default_settings['minified'] = pelican.settings['BTOC_MINIFIED']

    if 'BTOC_GENERATE_MINIFIED' in pelican.settings:
        btoc_default_settings['generate_minified'] = pelican.settings['BTOC_GENERATE_MINIFIED']

def register():
    """
    Register signals

    """

    signals.initialized.connect(init_default_config)
    signals.article_generator_context.connect(process_page_metadata)
    signals.page_generator_context.connect(process_page_metadata)

    signals.content_object_init.connect(btoc)
    signals.article_generator_finalized.connect(move_resources)
