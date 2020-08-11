.. django-eveuniverse documentation master file, created by
   sphinx-quickstart on Sun Aug  9 16:09:32 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-eveuniverse's documentation!
==============================================

*django-eveuniverse* is a foundation app meant to help speed up the development of Django apps that are using data from ESI. It provides all Eve classes from the Universe category in ESI as Django models, including all relationships between then, ready to be used in your project. Furthermore, all Eve models have an on-demand loading mechanism with database caching that will load eve objects from ESI as needed.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   operations   
   developer
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
