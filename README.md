Pelican-btoc - Automatic generation of TOC for Pelican
======================================================

`pelican-btoc` is an open source Pelican plugin to produce table of content for content page. Plugin is based on bootstrap components `scrollspy` and `affix`. The plugin is inspired by the similar TOC in the [Bootstrap documentation page](http://getbootstrap.com/). The plugin is mostly developed to be used with Markdown content. 

**Author**

Toni Heittola (toni.heittola@gmail.com), [GitHub](https://github.com/toni-heittola), [Home page](http://www.cs.tut.fi/~heittolt/)

Installation instructions
=========================

## Requirements

**bs4** is required. To ensure that all external modules are installed, run:

    pip install -r requirements.txt

**bs4** (BeautifulSoup) for parsing HTML content

    pip install beautifulsoup4

In order to regenerate minified CSS and JS files you need also: 

**rcssmin** a CSS Minifier

    pip install rcssmin
    
**jsmin** a JS Minifier

    pip install jsmin

## Pelican installation

Make sure you include [Bootstrap](http://getbootstrap.com/) in your template.

Make sure the directory where the plugin was installed is set in `pelicanconf.py`. For example if you installed in `plugins/pelican-btoc`, add:

    PLUGIN_PATHS = ['plugins']

Enable `pelican-btoc` with:

    PLUGINS = ['pelican-btoc']

To allow plugin in include css and js files, one needs to add following to the `base.html` template, in the head (to include css files):

    {% if article %}
        {% if article.styles %}
            {% for style in article.styles %}
    {{ style }}
            {% endfor %}
        {% endif %}
    {% endif %}
    {% if page %}
        {% if page.styles %}
            {% for style in page.styles %}
    {{ style }}
            {% endfor %}
        {% endif %}
    {% endif %}

At the bottom of the page before `</body>` tag (to include js files):

    {% if article %}
        {% if article.scripts %}
            {% for script in article.scripts %}
    {{ script }}
            {% endfor %}
        {% endif %}
    {% endif %}

    {% if page %}
        {% if page.scripts %}
            {% for script in page.scripts %}
    {{ script }}
            {% endfor %}
        {% endif %}
    {% endif %}

Insert TOC in the page template:
 
    {% if page.toc %}
        {{ page.toc }}
    {% endif %}

Insert TOC in the article template:

    {% if article.toc %}
        {{ article.toc }}
    {% endif %}

Usage
=====

TOC generation is triggered for the page either by setting BTOC metadata for the content (page or article) or inserting `[TOC]` tag somewhere in the content. 

## Global parameters

Parameters for the plugin can be set in  `pelicanconf.py' with following parameters:

| Parameter                 | Type      | Default       | Description  |
|---------------------------|-----------|---------------|--------------|
| BTOC_LEVELS               | List      | [1,2]         | List of integers, Indicates the levels of headers which are included into TOC  |
| BTOC_PANEL_COLOR          | String    | panel-primary |  CSS class used to color the TOC panel in the default template. Possible values: panel-default, panel-primary, panel-success, panel-info, panel-warning, panel-danger |
| BTOC_HEADER               | String    | Content       | Header used for the TOC panel  |
| BTOC_TEMPLATE             | String    |               | Jinja2 template to wrap the TOC. Parameters `panel_color`, `toc_header`, and `toc`. |
| BTOC_MINIFIED             | Boolean   | True          | Do we use minified CSS and JS files. Disable in case of debugging.  |
| BTOC_GENERATE_MINIFIED    | Boolean   | False         | CSS and JS files are minified each time, Enable in case of development.   |
| BTOC_DEBUG_PROCESSING     | Boolean   | False         | Show extra information in when run with `DEBUG=1` |

## Content wise parameters

| Parameter                 | Example value     | Description  |
|---------------------------|-----------|--------------|
| BTOC                      | True      | Enable TOC for the page
| BTOC_LEVELS               | 1,2     | Comma separated integers, Indicates the levels of headers which are included into TOC  |
| BTOC_PANEL_COLOR          | panel-primary | CSS class used to color the TOC panel in the default template. Possible values: panel-default, panel-primary, panel-success, panel-info, panel-warning, panel-danger |

Example:

    Title: TOC
    Date: 2010-10-03 10:20
    BTOC: True
    BTOC_LEVELS: 1,2,3
    
    # H1
    Text
        
    ## Head 1
    
    Text
    
    ### Head 1.1
    
    Text
     
    ### Head 1.2
    
    Text
    
    ### Head 1.3
    
    Text 
    
    # H2
    
    Text
    
    ## Head 2
    
    Text
    
    ### Head 2.1
    
    Text
    
    ### Head 2.2
    
    Text
    
    ## Head 3
    
    Text
    
    ### Head 3.1
    
    Text
    
    ### Head 3.2
    
    Text

