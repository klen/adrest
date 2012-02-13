class MetaOptions(object):
    " Resource meta options "

    def __init__(self):
        self.name = ''
        self.urlname = ''
        self.urlregex = ''
        self.parents = []
        self.models = []
        self.model_fields = set()

        self.emitters_dict = dict()
        self.emitters_types = []
        self.default_emitter = None

        self.parsers_dict = dict()
        self.default_parser = None

    def __str__(self):
        return "%(urlname)s(%(name)s) - %(urlregex)s %(parents)s %(models)s" % self.__dict__

    __repr__ = __str__
