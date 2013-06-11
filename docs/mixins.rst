ADRest Mixins
#############

**ADRest** based on mixin classes. You can use
:class:`adrest.views.ResourceView` as base for your REST_ controlers. Or you
can use a ADRest's mixins separately.


EmitterMixin
============

.. autoclass:: adrest.mixin.emitter.EmitterMixin
   :members:


ParserMixin
===========

.. autoclass:: adrest.mixin.parser.ParserMixin


.. autoclass:: adrest.mixin.throttle.ThrottleMixin

.. autoclass:: adrest.mixin.auth.AuthMixin

.. autoclass:: adrest.mixin.handler.HandlerMixin


.. == links ==
.. _links:
.. include:: ../README.rst
    :start-after: .. _links:
