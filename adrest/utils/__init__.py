class MetaOptions(object):
    " Resource meta options "

    def __init__(self):
        self.name = ''
        self.url_name = ''
        self.url_regex = ''
        self.parents = []
        self.model_fields = set()

        self.emitters_dict = dict()
        self.emitters_types = []
        self.default_emitter = None

        self.parsers_dict = dict()
        self.default_parser = None

    def __str__(self):
        return "%(url_name)s(%(name)s) - %(url_regex)s %(parents)s" % self.__dict__

    __repr__ = __str__


class UpdatedList(list):

    @property
    def len(self):
        return len(self)
