FlowGraph
=========

## Summary
- [Overview](#overview)
 - [Demo](#demo)
- [Dependencies](#dependencies)
 - [Python](#python)
 - [NetFlow data and NfDump](#netflow-data-and-nfdump)
 - [Flask](#flask)
- [Installation](#installation)
- [Configuration](#configuration)
 - [Application specific configurations](#application-specific-configurations)
 - [Local var directory](#local-var-directory)
 - [Scheduler](#scheduler)
 - [Web front-end](#web-front-end)
   - [Flask builtin web server](#flask-builtin-web-server)
    - [Apache](#apache)
- [Usage](#usage)
 - [Filters](#filters)
 - [Resource details](#resource-details)
 - [Run queries manually](#run-queries-manually)
- [Bug and issues](#bug-and-issues)
- [Author](#author)

## Overview

FlowGraph allows to dynamically build graphs based on previously collected netflow data and to use them in a web-based front-end, adding details about Autonomous System Number holders, IPv4 and IPv6 prefixes, inet(6)num objects, netnames from [RIPE Stat](https://stat.ripe.net/).

Its core is written in Python and runs server-side, while the GUI is a web page powered by JavaScript and AJAX.

### Demo

A **demo** can be found at http://www.pierky.com/flowgraph/demo.

## Dependencies

### Python

Yes, Python 2.7 (probably it's already on your system).

- One step installation: `apt-get install python2.7` (Debian-like)

- More details: https://docs.python.org/2/

### NetFlow data and NfDump

Of course, FlowGraph needs to read netflow data and requires [nfdump](http://nfdump.sourceforge.net/) to parse them.

It has been tested with version [1.6.12](http://sourceforge.net/projects/nfdump/files/stable/nfdump-1.6.12/) and 1.6.3p1 (shipped, for example, with Ubuntu 12.04LTS).

- One step installation: `apt-get install nfdump` (Debian-like)

- More details: http://nfdump.sourceforge.net/

To setup a netflow data collector please refer to the [Principle of Operation](http://nfdump.sourceforge.net/) section of the NfDump page on SourceForge.

### Flask

The FlowGraph web front-end has been written within the [Flask](http://flask.pocoo.org/) 0.10.1 framework.

- One step installation: `pip install Flask`

- More details: http://flask.pocoo.org/docs/0.10/installation/

## Installation

Simply fetch the GitHub repository into your local directory:

- One step installation:

 `git clone https://github.com/pierky/flowgraph.git /usr/local/src/flowgraph`
 
 (replace /usr/local/src/flowgraph with your preferred destination directory)

- More details: https://help.github.com/articles/fetching-a-remote/

## Configuration

### Application specific configurations

Rename the **config-distrib.py** to **config.py** and edit it with your preferred text editor.

Some parameters must be configured in this file:

- `NFDUMP_PATH` must be set with the nfdump binary path (if it's within your $PATH directories can also be left to the "nfdump" default value);

- `NETFLOW_*` variables must be set depending on your netflow data files layout: a guide is provided in the *NetFlow data path* section of comments included in the configuration file.

The other parameters are less important and may be left to their default settings.

**IMPORTANT**: when done, set the `CONFIG_DONE` at the end of the file to `True`.

### Local var directory

Build the FlowGraph's *var* directory referenced by the `VAR_DIR` variable:

`mkdir var`

Cached data, nfdump filters and log files will be stored here.

### Scheduler

Drawing of graphs which are frequently used can be speeded up by continuously caching netflow data. In order to do so a process must be scheduled within **crontab**, by editing the **/etc/crontab** file or, even better, by placing a new file under the **/etc/cron.d** directory:

 `*/5 *   * * *   root    /usr/local/src/flowgraph/scheduler.py`

Tune it as you like depending on your netflow data rotation interval (replace /usr/local/src/flowgraph with your installation directory).

### Web front-end

The web front-end of FlowGraph can be deployed in two flavors:

- using the **Flask builtin web server**, not suitable for production environment but useful to have a working application in few minutes;

- using [WSGI containers](http://flask.pocoo.org/docs/0.10/deploying/wsgi-standalone/) or **Apache with mod_wsgi**.

In this document you can find two brief guides about the builtin server and the Apache configuration.

Please consider security aspects of your network before installing FlowGraph; it is intended for a restricted audience of trusted people and it does not implement any kind of security mechanism.

#### Flask builtin web server

- To change the listening IP address, edit the last line of **web.py**:

 `flowgraphapp.run(host="0.0.0.0")`

- From the directory where FlowGraph has been downloaded, run

 `python web.py`

The output will show how to reach the application:

  ```
  * Running on http://0.0.0.0:5000/
  * Restarting with reloader
  ```

Any output debug message will be written to stdout.

#### Apache

- Configure Apache to use **mod_wsgi**.

 An example is provided in the **flowgraph.apache** file.

 A quick setup guide is available on [Flask web-site](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/).

 See http://www.modwsgi.org/ for more details.

- Edit **web.wsgi** and set ```BASE_DIR``` to the directory where FlowGraph has been downloaded in.

- Ensure that the **var** directory has **write permissions** for the user used by Apache:

```
chown -R :www-data var
chmod -R g+w var
chmod g+s var
```

## Usage

Graphs can be created from the web front-end; for each graph some parameters must be provided in order to extract netflow data required to draw the chart:

- sources and an optional filter are used to narrow the scope of the query;

- aggregation details are needed to understand what to draw.

For each time interval included in the input date/time range the first *n* elements of the selected type are extracted, ordered by the given criteria, and used to draw the graph. These data are saved in a local cache file, so that the next queries will be faster.

A scheduler may be enabled in order to continuously extract data from netflow files and save them into the local cache, so that graphs will draw faster.

### Filters

The syntax used for filter is the same used by nfdump. See the *FILTER* section of `man nfdump` for details.

For the sake of readability filters may also be written to a local file and then included using the `@include` statement:

```
@include /path/to/my/dir/filter1.txt
@include %filters%/filter2
```

In the second example the `%filters%` macro will be expanded to the FlowGraph local **var** directory path.

### Resource details

Once the graph has been drawn, clicking on resources such as Autonomous System Numbers (ASN) and IP addresses or subnets (both v4 and v6) will open a tooltip containing details gathered using the [RIPE Stat](https://stat.ripe.net/) tool, like ASN holder, inet(6)num object details, reverse DNS.

### Run queries manually

The **manual.py** script can be used to manually run queries and extract netflow data to be used for later graph drawing. It can also be used to test that everything works fine.

## Bug and issues

Have a bug? Please create an issue here on GitHub at https://github.com/pierky/flowgraph/issues.

## Author

Pier Carlo Chiodi - http://pierky.com/aboutme

Blog: http://blog.pierky.com Twitter: [@pierky](http://twitter.com/pierky)
