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
from pelican.generators import ArticlesGenerator, PagesGenerator
import re
import unicodedata

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
    'type': 'normal',  # normal, dictionary
    'generate_minified': False,
    'site-url': '',
    'debug_processing': False
}

btoc_settings = copy.deepcopy(btoc_default_settings)


def btoc(content):
    """
    Main processing

    """

    if isinstance(content, contents.Static):
        return

    # Process page metadata and assign css and styles
    btoc_settings = copy.deepcopy(btoc_default_settings)  # page wise settings

    if u'styles' not in content.metadata:
        content.metadata[u'styles'] = []
    if u'scripts' not in content.metadata:
        content.metadata[u'scripts'] = []

    if u'btoc' in content.metadata and content.metadata['btoc'] == 'True':
        btoc_settings['show'] = True

    else:
        btoc_settings['show'] = False

    if u'btoc_levels' in content.metadata:
        btoc_settings['levels'] = list(map(int, content.metadata['btoc_levels'].split(',')))

    if u'btoc_panel_color' in content.metadata:
        btoc_settings['panel_color'] = content.metadata['btoc_panel_color']

    if u'btoc_header' in content.metadata:
        btoc_settings['header'] = content.metadata['btoc_header']

    if u'btoc_type' in content.metadata:
        btoc_settings['type'] = content.metadata['btoc_type']

    btoc_settings['levels'].sort()

    soup = BeautifulSoup(content._content, 'html.parser')

    heading_regex = '|'.join([str(level) for level in btoc_settings['levels']])
    search = re.compile('^h(%s)$' % (heading_regex))
    headings = soup.findAll(search)

    if btoc_settings['debug_processing'] and btoc_settings['show']:
        logger.debug(msg='[{plugin_name}] title:[{title}] headings:[{heading_count}]'.format(
            plugin_name='btoc',
            title=content.title,
            heading_count=len(headings)
        ))

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
            anchor = title.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '').replace('/', '').replace('?', '').replace(',', '').replace(':', '').replace(';', '').replace('#', '')
            anchor = unicodedata.normalize('NFKD', anchor).encode('ascii', 'ignore').decode('utf-8')

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

    if btoc_settings['type'] == 'alphabet':
        toc_html = "\n" + '<ul class="nav btoc-nav btoc-alphabet">' + "\n"
    else:
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

    if 'BTOC_TYPE' in pelican.settings:
        btoc_default_settings['type'] = pelican.settings['BTOC_TYPE']

    if 'BTOC_TEMPLATE' in pelican.settings:
        btoc_default_settings['template'] = pelican.settings['BTOC_TEMPLATE']

    if 'BTOC_MINIFIED' in pelican.settings:
        btoc_default_settings['minified'] = pelican.settings['BTOC_MINIFIED']

    if 'BTOC_GENERATE_MINIFIED' in pelican.settings:
        btoc_default_settings['generate_minified'] = pelican.settings['BTOC_GENERATE_MINIFIED']

    if 'BTOC_DEBUG_PROCESSING' in pelican.settings:
        btoc_default_settings['debug_processing'] = pelican.settings['BTOC_DEBUG_PROCESSING']


def run_plugin(generators):
    """
    Run plugin to generators

    """

    for generator in generators:
        if isinstance(generator, ArticlesGenerator):
            for article in generator.articles:
                btoc(article)

        if isinstance(generator, PagesGenerator):
            for page in generator.pages:
                btoc(page)


def register():
    """
    Register signals

    """

    signals.initialized.connect(init_default_config)
    signals.article_generator_finalized.connect(move_resources)
    signals.all_generators_finalized.connect(run_plugin)
