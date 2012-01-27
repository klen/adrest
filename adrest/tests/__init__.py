if __name__ == '__main__':
    import sys
    import os.path
    from django.core.management import execute_manager

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from adrest.tests import settings

    execute_manager(settings, ['', 'test', 'main', '--failfast'])
