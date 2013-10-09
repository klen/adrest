ADRest Mixins
#############

**ADRest** based on mixin classes. You can use
:class:`adrest.views.ResourceView` as base for your REST_ controlers. Or you
can use a ADRest's mixins separately.

.. contents::


Common Options
==============

.. autoclass:: adrest.utils.meta.Meta
   :members:


EmitterMixin
============

.. autoclass:: adrest.mixin.emitter.EmitterMixin
   :members:


ParserMixin
===========

.. autoclass:: adrest.mixin.parser.ParserMixin


ThrottleMixin
=============

.. autoclass:: adrest.mixin.throttle.ThrottleMixin


AuthMixin
=========

.. autoclass:: adrest.mixin.auth.AuthMixin


DynamicMixin
============

.. autoclass:: adrest.mixin.handler.DynamicMixin


HandlerMixin
============

.. autoclass:: adrest.mixin.handler.HandlerMixin


.. == links ==
.. _links:
.. include:: ../README.rst
    :start-after: .. _links:
