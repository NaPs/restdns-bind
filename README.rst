restdns-bind
============

A Bind9 zonefile generator for `Restdns <https://github.com/NaPs/restdns>`_.


Setup
-----

The fastest and more common way to install restdns-bind is using pip::

    pip install restdns-bind


Debian
~~~~~~

If you use Debian Wheezy, you can also use the Tecknet repositories. Add theses
lines in your ``/etc/apt/source.list`` file::

    deb http://debian.tecknet.org/debian wheezy tecknet
    deb-src http://debian.tecknet.org/debian wheezy tecknet

Add the Tecknet repositories key in your keyring:

    # wget http://debian.tecknet.org/debian/public.key -O - | apt-key add -

Then, update and install the ``restdns-bind`` package::

    # aptitude update
    # aptitude install restdns-bind


Tutorial
--------

restdns-bind is designed to be executed periodically by a cron job. If you use
the Debian package, an example crontab file has been installed in
``/etc/cron.d/restdns-bind``. Otherwise, you can use this example file::

    * * * * * bind restdns-bind http://my-restdns-server/ /etc/bind/restdns/

Where:

* bind is the user used to launch restdns-bind (this used must be able to reload
  bind configuration)
* http://my-restdns-server/ the base URL of your restdns instance
* /etc/bind/restdns/ the path where to write the zone files

You can read the crontab manual to learn more about its format.

Once generated for a first time, you can start to configure your Bind daemon
to serve your zones. restdns-bind generates for you a ``zones.conf`` file you
can include in your Bind configuration. For example, add the following line
in your ``/etc/bind/named.conf`` file::

    include "/etc/bind/restdns/zones.conf";


Legal
-----

restdns-bind is released under MIT license, copyright 2013 Antoine Millet.


Contribute
----------

You can send your pull-request for restdns-bind through Github:

    https://github.com/NaPs/restdns-bind

I also accept well formatted git patches sent by email.

Feel free to contact me for any question/suggestion/patch: <antoine@inaps.org>.
