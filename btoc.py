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
__version__ = '0.2.0'

btoc_default_settings = {
    'levels': [1, 2],
    'mode': 'bs3',  # bs3, bs-toc
    'panel_color': 'panel-primary',
    'header': 'Content',
    'template': {
        'bs3': """
            <div class="btoc-container hidden-print" role="complementary">
                <div class="panel panel-{{panel_color}} {{text_color}}">
                    <div class="panel-heading">
                        <h3 class="panel-title">{{toc_header}}</h3>
                    </div>
                    {{ toc }}
                </div>
            </div>
        """,
        'bs-toc': """
            <div class="btoc-container hidden-print sticky-top" role="complementary">
                <div class="btoc-header {{panel_color}} {{text_color}}">{{toc_header}}</div>
                <div class="btoc-body">{{ toc }}</div>                
            </div>    
            
        """,
        'tocbot': """
            <div class="btoc-container hidden-print sticky-top" role="complementary">
                <div class="btoc-header {{panel_color}} {{text_color}}">{{toc_header}}</div>
                <div class="btoc-body">{{ toc }}</div>                
            </div>    
            
        """
    },
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

    if u'btoc_mode' in content.metadata:
        btoc_settings['mode'] = content.metadata['btoc_mode']

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

    text_color = ''
    toc_html = ''
    if btoc_settings['mode'] == 'bs3':
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

    elif btoc_settings['mode'] == 'bs-toc':
        if 'panel-' in btoc_settings['panel_color']:
            btoc_settings['panel_color'] = btoc_settings['panel_color'].replace('panel-', 'bg-')

        if btoc_settings['panel_color'] in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark', 'body', 'white', 'transparent']:
            btoc_settings['panel_color'] = 'bg-'+btoc_settings['panel_color']

        if btoc_settings['panel_color'] == 'bg-default':
            btoc_settings['panel_color'] = 'bg-light'

        if btoc_settings['panel_color'] not in ['bg-light', 'bg-secondary', 'bg-primary', 'bg-success', 'bg-danger', 'bg-transparent']:
            text_color = 'text-white'
        else:
            text_color = 'text-muted'

        levels =[]
        for level in btoc_settings['levels']:
            levels.append('h{level}'.format(level=level))
        levels = ','.join(levels)

        if btoc_settings['type'] == 'alphabet':
            toc_html = "\n" + '<nav class="btoc-nav btoc-alphabet" data-toc-levels="{levels}"></nav>'.format(levels=levels) + "\n"
        else:
            toc_html = "\n"+'<nav class="btoc-nav" data-toc-levels="{levels}"></nav>'.format(levels=levels)+"\n"

    elif btoc_settings['mode'] == 'tocbot':
        if 'panel-' in btoc_settings['panel_color']:
            btoc_settings['panel_color'] = btoc_settings['panel_color'].replace('panel-', 'bg-')

        if btoc_settings['panel_color'] in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark', 'body', 'white', 'transparent']:
            btoc_settings['panel_color'] = 'bg-'+btoc_settings['panel_color']

        if btoc_settings['panel_color'] == 'bg-default':
            btoc_settings['panel_color'] = 'bg-light'

        if btoc_settings['panel_color'] not in ['bg-light', 'bg-secondary', 'bg-primary', 'bg-success', 'bg-danger', 'bg-transparent']:
            text_color = 'text-white'
        else:
            text_color = 'text-muted'

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


        levels =[]
        for level in btoc_settings['levels']:
            levels.append('h{level}'.format(level=level))
        levels = ','.join(levels)

        if btoc_settings['type'] == 'alphabet':
            toc_html = "\n" + '<nav class="btoc-nav btoc-alphabet" data-toc-levels="{levels}"></nav>'.format(levels=levels) + "\n"
        else:
            toc_html = "\n"+'<nav class="btoc-nav" data-toc-levels="{levels}"></nav>'.format(levels=levels)+"\n"

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

    if toc_element_default:
        toc_element_default.extract()  # remove from tree

    if btoc_settings['show']:
        if btoc_settings['minified']:
            if btoc_settings['mode'] == 'bs3':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/btoc.min.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="'+btoc_default_settings['site-url']+'/theme/css/btoc.min.css">'
                    ]
                }
            elif btoc_settings['mode'] == 'bs-toc':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="' + btoc_default_settings['site-url'] + '/theme/js/bootstrap-toc.min.js"></script>',
                        '<script type="text/javascript" src="' + btoc_default_settings['site-url'] + '/theme/js/btoc-bs.min.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="' + btoc_default_settings['site-url'] + '/theme/css/btoc-bs.min.css">'
                    ]
                }
            elif btoc_settings['mode'] == 'tocbot':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/tocbot.min.js"></script>',
                        '<script type="text/javascript" src="' + btoc_default_settings['site-url'] + '/theme/js/btoc-bot.min.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="' + btoc_default_settings['site-url'] + '/theme/css/btoc-bot.min.css">',
                    ]
                }

        else:
            if btoc_settings['mode'] == 'bs3':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/btoc.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="'+btoc_default_settings['site-url']+'/theme/css/btoc.css">'
                    ]
                }
            elif btoc_settings['mode'] == 'bs-toc':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/bootstrap-toc.js"></script>',
                        '<script type="text/javascript" src="' + btoc_default_settings['site-url'] + '/theme/js/btoc-bs.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="' + btoc_default_settings['site-url'] + '/theme/css/btoc-bs.css">',
                    ]
                }
            elif btoc_settings['mode'] == 'tocbot':
                html_elements = {
                    'js_include': [
                        '<script type="text/javascript" src="'+btoc_default_settings['site-url']+'/theme/js/tocbot.js"></script>',
                        '<script type="text/javascript" src="' + btoc_default_settings['site-url'] + '/theme/js/btoc-bot.js"></script>'
                    ],
                    'css_include': [
                        '<link rel="stylesheet" href="' + btoc_default_settings['site-url'] + '/theme/css/btoc-bot.css">',
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

        template = Template(btoc_settings['template'][btoc_settings['mode']].strip('\t\r\n').replace('&gt;', '>').replace('&lt;', '<'))

        toc_element2 = BeautifulSoup(
            template.render(
                toc=toc_html,
                panel_color=btoc_settings['panel_color'],
                text_color=text_color,
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
    btoc_settings = copy.deepcopy(btoc_default_settings)

    plugin_paths = gen.settings['PLUGIN_PATHS']
    files = []

    if btoc_settings['minified']:
        if btoc_settings['generate_minified']:
            minify_css_directory(gen=gen, source='css', target='css.min')
            minify_js_directory(gen=gen, source='js', target='js.min')

        if btoc_settings['mode'] == 'bs3':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc.min.css'),
                    'source': os.path.join('pelican-btoc', 'css.min', 'btoc.min.css'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc.min.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'btoc.min.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bs.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'btoc-bs.js'),
                }
            ]

        elif btoc_settings['mode'] == 'bs-toc':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'bootstrap-toc.min.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'bootstrap-toc.min.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bs.min.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'btoc-bs.min.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc-bs.min.css'),
                    'source': os.path.join('pelican-btoc', 'css.min', 'btoc-bs.min.css'),
                }
            ]

        elif btoc_settings['mode'] == 'tocbot':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'tocbot.min.css'),
                    'source': os.path.join('pelican-btoc', 'css.min', 'tocbot.min.css'),
                 },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc-bot.min.css'),
                    'source': os.path.join('pelican-btoc', 'css.min', 'btoc-bot.min.css'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'tocbot.min.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'tocbot.min.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bot.min.js'),
                    'source': os.path.join('pelican-btoc', 'js.min', 'btoc-bot.min.js'),
                }
            ]

    else:
        if btoc_settings['mode'] == 'bs3':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc.css'),
                    'source': os.path.join('pelican-btoc', 'css', 'btoc.css'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'btoc.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bs.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'btoc-bs.js'),
                }
            ]

        elif btoc_settings['mode'] == 'bs-toc':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc-bs.css'),
                    'source': os.path.join('pelican-btoc', 'css', 'btoc-bs.css'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'bootstrap-toc.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'bootstrap-toc.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bs.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'btoc-bs.js'),
                }
            ]

        elif btoc_settings['mode'] == 'tocbot':
            files = [
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'tocbot.css'),
                    'source': os.path.join('pelican-btoc', 'css', 'tocbot.css'),
                 },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'css', 'btoc-bot.css'),
                    'source': os.path.join('pelican-btoc', 'css', 'btoc-bot.css'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'tocbot.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'tocbot.js'),
                },
                {
                    'target': os.path.join(gen.output_path, 'theme', 'js', 'btoc-bot.js'),
                    'source': os.path.join('pelican-btoc', 'js', 'btoc-bot.js'),
                }
            ]

    if not os.path.exists(os.path.join(gen.output_path, 'theme', 'css')):
        os.makedirs(os.path.join(gen.output_path, 'theme', 'css'))
    if not os.path.exists(os.path.join(gen.output_path, 'theme', 'js')):
        os.makedirs(os.path.join(gen.output_path, 'theme', 'js'))

    for file in files:
        for path in plugin_paths:
            current_source = os.path.join(path, file['source'])
            if os.path.isfile(current_source):
                shutil.copyfile(current_source, file['target'])
            if os.path.isfile(file['target']):
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

    if 'BTOC_MODE' in pelican.settings:
        btoc_default_settings['mode'] = pelican.settings['BTOC_MODE']

    if 'BTOC_LEVELS' in pelican.settings:
        btoc_default_settings['levels'] = pelican.settings['BTOC_LEVELS']

    if 'BTOC_PANEL_COLOR' in pelican.settings:
        btoc_default_settings['panel_color'] = pelican.settings['BTOC_PANEL_COLOR']

    if 'BTOC_HEADER' in pelican.settings:
        btoc_default_settings['header'] = pelican.settings['BTOC_HEADER']

    if 'BTOC_TYPE' in pelican.settings:
        btoc_default_settings['type'] = pelican.settings['BTOC_TYPE']

    if 'BTOC_TEMPLATE' in pelican.settings:
        btoc_default_settings['template']['custom'] = pelican.settings['BTOC_TEMPLATE']
        btoc_default_settings['theme'] = 'custom'

    if 'BTOC_MINIFIED' in pelican.settings:
        btoc_default_settings['minified'] = pelican.settings['BTOC_MINIFIED']

    if 'BTOC_GENERATE_MINIFIED' in pelican.settings:
        btoc_default_settings['generate_minified'] = pelican.settings['BTOC_GENERATE_MINIFIED']

    if 'BTOC_DEBUG_PROCESSING' in pelican.settings:
        btoc_default_settings['debug_processing'] = pelican.settings['BTOC_DEBUG_PROCESSING']

    btoc_settings = copy.deepcopy(btoc_default_settings)

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
