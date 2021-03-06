"""Dependency injector config providers unit tests."""

import contextlib
import os
import sys
import tempfile

import unittest2 as unittest

from dependency_injector import containers, providers, errors


class ConfigTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

    def tearDown(self):
        del self.config

    def test_default_name(self):
        config = providers.Configuration()
        self.assertEqual(config.get_name(), 'config')

    def test_providers_are_providers(self):
        self.assertTrue(providers.is_provider(self.config.a))
        self.assertTrue(providers.is_provider(self.config.a.b))
        self.assertTrue(providers.is_provider(self.config.a.b.c))
        self.assertTrue(providers.is_provider(self.config.a.b.d))

    def test_providers_are_not_delegates(self):
        self.assertFalse(providers.is_delegated(self.config.a))
        self.assertFalse(providers.is_delegated(self.config.a.b))
        self.assertFalse(providers.is_delegated(self.config.a.b.c))
        self.assertFalse(providers.is_delegated(self.config.a.b.d))

    def test_providers_identity(self):
        self.assertIs(self.config.a, self.config.a)
        self.assertIs(self.config.a.b, self.config.a.b)
        self.assertIs(self.config.a.b.c, self.config.a.b.c)
        self.assertIs(self.config.a.b.d, self.config.a.b.d)

    def test_get_name(self):
        self.assertEqual(self.config.a.b.c.get_name(), 'config.a.b.c')

    def test_providers_value_setting(self):
        a = self.config.a
        ab = self.config.a.b
        abc = self.config.a.b.c
        abd = self.config.a.b.d

        self.config.update({'a': {'b': {'c': 1, 'd': 2}}})

        self.assertEqual(a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(ab(), {'c': 1, 'd': 2})
        self.assertEqual(abc(), 1)
        self.assertEqual(abd(), 2)

    def test_providers_with_already_set_value(self):
        self.config.update({'a': {'b': {'c': 1, 'd': 2}}})

        a = self.config.a
        ab = self.config.a.b
        abc = self.config.a.b.c
        abd = self.config.a.b.d

        self.assertEqual(a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(ab(), {'c': 1, 'd': 2})
        self.assertEqual(abc(), 1)
        self.assertEqual(abd(), 2)

    def test_providers_value_override(self):
        a = self.config.a
        ab = self.config.a.b
        abc = self.config.a.b.c
        abd = self.config.a.b.d

        self.config.override({'a': {'b': {'c': 1, 'd': 2}}})

        self.assertEqual(a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(ab(), {'c': 1, 'd': 2})
        self.assertEqual(abc(), 1)
        self.assertEqual(abd(), 2)

    def test_providers_with_already_overridden_value(self):
        self.config.override({'a': {'b': {'c': 1, 'd': 2}}})

        a = self.config.a
        ab = self.config.a.b
        abc = self.config.a.b.c
        abd = self.config.a.b.d

        self.assertEqual(a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(ab(), {'c': 1, 'd': 2})
        self.assertEqual(abc(), 1)
        self.assertEqual(abd(), 2)

    def test_providers_with_default_value(self):
        self.config = providers.Configuration(
            name='config', default={'a': {'b': {'c': 1, 'd': 2}}})

        a = self.config.a
        ab = self.config.a.b
        abc = self.config.a.b.c
        abd = self.config.a.b.d

        self.assertEqual(a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(ab(), {'c': 1, 'd': 2})
        self.assertEqual(abc(), 1)
        self.assertEqual(abd(), 2)

    def test_providers_with_default_value_overriding(self):
        self.config = providers.Configuration(
            name='config', default={'a': {'b': {'c': 1, 'd': 2}}})

        self.assertEqual(self.config.a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(self.config.a.b(), {'c': 1, 'd': 2})
        self.assertEqual(self.config.a.b.c(), 1)
        self.assertEqual(self.config.a.b.d(), 2)

        self.config.override({'a': {'b': {'c': 3, 'd': 4}}})
        self.assertEqual(self.config.a(), {'b': {'c': 3, 'd': 4}})
        self.assertEqual(self.config.a.b(), {'c': 3, 'd': 4})
        self.assertEqual(self.config.a.b.c(), 3)
        self.assertEqual(self.config.a.b.d(), 4)

        self.config.reset_override()
        self.assertEqual(self.config.a(), {'b': {'c': 1, 'd': 2}})
        self.assertEqual(self.config.a.b(), {'c': 1, 'd': 2})
        self.assertEqual(self.config.a.b.c(), 1)
        self.assertEqual(self.config.a.b.d(), 2)

    def test_value_of_undefined_option(self):
        self.assertIsNone(self.config.a())

    def test_getting_of_special_attributes(self):
        with self.assertRaises(AttributeError):
            self.config.__name__

    def test_getting_of_special_attributes_from_child(self):
        a = self.config.a
        with self.assertRaises(AttributeError):
            a.__name__

    def test_deepcopy(self):
        provider = providers.Configuration('config')
        provider_copy = providers.deepcopy(provider)

        self.assertIsNot(provider, provider_copy)
        self.assertIsInstance(provider, providers.Configuration)

    def test_deepcopy_from_memo(self):
        provider = providers.Configuration('config')
        provider_copy_memo = providers.Configuration('config')

        provider_copy = providers.deepcopy(
            provider, memo={id(provider): provider_copy_memo})

        self.assertIs(provider_copy, provider_copy_memo)

    def test_deepcopy_overridden(self):
        provider = providers.Configuration('config')
        object_provider = providers.Object(object())

        provider.override(object_provider)

        provider_copy = providers.deepcopy(provider)
        object_provider_copy = provider_copy.overridden[0]

        self.assertIsNot(provider, provider_copy)
        self.assertIsInstance(provider, providers.Configuration)

        self.assertIsNot(object_provider, object_provider_copy)
        self.assertIsInstance(object_provider_copy, providers.Object)

    def test_repr(self):
        self.assertEqual(repr(self.config),
                         '<dependency_injector.providers.'
                         'Configuration({0}) at {1}>'.format(
                             repr('config'),
                             hex(id(self.config))))

    def test_repr_child(self):
        self.assertEqual(repr(self.config.a.b.c),
                         '<dependency_injector.providers.'
                         'ConfigurationOption({0}) at {1}>'.format(
                             repr('config.a.b.c'),
                             hex(id(self.config.a.b.c))))


class ConfigLinkingTests(unittest.TestCase):

    class TestCore(containers.DeclarativeContainer):
        config = providers.Configuration('core')
        value_getter = providers.Callable(lambda _: _, config.value)

    class TestServices(containers.DeclarativeContainer):
        config = providers.Configuration('services')
        value_getter = providers.Callable(lambda _: _, config.value)

    def test(self):
        root_config = providers.Configuration('main')
        core = self.TestCore(config=root_config.core)
        services = self.TestServices(config=root_config.services)

        root_config.override(
            {
                'core': {
                    'value': 'core',
                },
                'services': {
                    'value': 'services',
                },
            },
        )

        self.assertEqual(core.config(), {'value': 'core'})
        self.assertEqual(core.config.value(), 'core')
        self.assertEqual(core.value_getter(), 'core')

        self.assertEqual(services.config(), {'value': 'services'})
        self.assertEqual(services.config.value(), 'services')
        self.assertEqual(services.value_getter(), 'services')

    def test_double_override(self):
        root_config = providers.Configuration('main')
        core = self.TestCore(config=root_config.core)
        services = self.TestServices(config=root_config.services)

        root_config.override(
            {
                'core': {
                    'value': 'core1',
                },
                'services': {
                    'value': 'services1',
                },
            },
        )
        root_config.override(
            {
                'core': {
                    'value': 'core2',
                },
                'services': {
                    'value': 'services2',
                },
            },
        )

        self.assertEqual(core.config(), {'value': 'core2'})
        self.assertEqual(core.config.value(), 'core2')
        self.assertEqual(core.value_getter(), 'core2')

        self.assertEqual(services.config(), {'value': 'services2'})
        self.assertEqual(services.config.value(), 'services2')
        self.assertEqual(services.value_getter(), 'services2')


class ConfigFromIniTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

        _, self.config_file_1 = tempfile.mkstemp()
        with open(self.config_file_1, 'w') as config_file:
            config_file.write(
                '[section1]\n'
                'value1=1\n'
                '\n'
                '[section2]\n'
                'value2=2\n'
            )

        _, self.config_file_2 = tempfile.mkstemp()
        with open(self.config_file_2, 'w') as config_file:
            config_file.write(
                '[section1]\n'
                'value1=11\n'
                'value11=11\n'
                '[section3]\n'
                'value3=3\n'
            )

    def tearDown(self):
        del self.config
        os.unlink(self.config_file_1)
        os.unlink(self.config_file_2)

    def test(self):
        self.config.from_ini(self.config_file_1)

        self.assertEqual(self.config(), {'section1': {'value1': '1'}, 'section2': {'value2': '2'}})
        self.assertEqual(self.config.section1(), {'value1': '1'})
        self.assertEqual(self.config.section1.value1(), '1')
        self.assertEqual(self.config.section2(), {'value2': '2'})
        self.assertEqual(self.config.section2.value2(), '2')

    def test_merge(self):
        self.config.from_ini(self.config_file_1)
        self.config.from_ini(self.config_file_2)

        self.assertEqual(
            self.config(),
            {
                'section1': {
                    'value1': '11',
                    'value11': '11',
                },
                'section2': {
                    'value2': '2',
                },
                'section3': {
                    'value3': '3',
                },
            },
        )
        self.assertEqual(self.config.section1(), {'value1': '11', 'value11': '11'})
        self.assertEqual(self.config.section1.value1(), '11')
        self.assertEqual(self.config.section1.value11(), '11')
        self.assertEqual(self.config.section2(), {'value2': '2'})
        self.assertEqual(self.config.section2.value2(), '2')
        self.assertEqual(self.config.section3(), {'value3': '3'})
        self.assertEqual(self.config.section3.value3(), '3')


class ConfigFromIniWithEnvInterpolationTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

        os.environ['CONFIG_TEST_ENV'] = 'test-value'

        _, self.config_file = tempfile.mkstemp()
        with open(self.config_file, 'w') as config_file:
            config_file.write(
                '[section1]\n'
                'value1=${CONFIG_TEST_ENV}\n'
            )

    def tearDown(self):
        del self.config
        del os.environ['CONFIG_TEST_ENV']
        os.unlink(self.config_file)

    def test_env_variable_interpolation(self):
        self.config.from_ini(self.config_file)

        self.assertEqual(
            self.config(),
            {
                'section1': {
                    'value1': 'test-value',
                },
            },
        )
        self.assertEqual(self.config.section1(), {'value1': 'test-value'})
        self.assertEqual(self.config.section1.value1(), 'test-value')



class ConfigFromYamlTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

        _, self.config_file_1 = tempfile.mkstemp()
        with open(self.config_file_1, 'w') as config_file:
            config_file.write(
                'section1:\n'
                '  value1: 1\n'
                '\n'
                'section2:\n'
                '  value2: 2\n'
            )

        _, self.config_file_2 = tempfile.mkstemp()
        with open(self.config_file_2, 'w') as config_file:
            config_file.write(
                'section1:\n'
                '  value1: 11\n'
                '  value11: 11\n'
                'section3:\n'
                '  value3: 3\n'
            )

    def tearDown(self):
        del self.config
        os.unlink(self.config_file_1)
        os.unlink(self.config_file_2)

    @unittest.skipIf(sys.version_info[:2] == (3, 4), 'PyYAML does not support Python 3.4')
    def test(self):
        self.config.from_yaml(self.config_file_1)

        self.assertEqual(self.config(), {'section1': {'value1': 1}, 'section2': {'value2': 2}})
        self.assertEqual(self.config.section1(), {'value1': 1})
        self.assertEqual(self.config.section1.value1(), 1)
        self.assertEqual(self.config.section2(), {'value2': 2})
        self.assertEqual(self.config.section2.value2(), 2)

    @unittest.skipIf(sys.version_info[:2] == (3, 4), 'PyYAML does not support Python 3.4')
    def test_merge(self):
        self.config.from_yaml(self.config_file_1)
        self.config.from_yaml(self.config_file_2)

        self.assertEqual(
            self.config(),
            {
                'section1': {
                    'value1': 11,
                    'value11': 11,
                },
                'section2': {
                    'value2': 2,
                },
                'section3': {
                    'value3': 3,
                },
            },
        )
        self.assertEqual(self.config.section1(), {'value1': 11, 'value11': 11})
        self.assertEqual(self.config.section1.value1(), 11)
        self.assertEqual(self.config.section1.value11(), 11)
        self.assertEqual(self.config.section2(), {'value2': 2})
        self.assertEqual(self.config.section2.value2(), 2)
        self.assertEqual(self.config.section3(), {'value3': 3})
        self.assertEqual(self.config.section3.value3(), 3)

    def test_no_yaml_installed(self):
        @contextlib.contextmanager
        def no_yaml_module():
            yaml = providers.yaml
            providers.yaml = None

            yield

            providers.yaml = yaml

        with no_yaml_module():
            with self.assertRaises(errors.Error) as error:
                self.config.from_yaml(self.config_file_1)

        self.assertEqual(
            error.exception.args[0],
            'Unable to load yaml configuration - PyYAML is not installed. '
            'Install PyYAML or install Dependency Injector with yaml extras: '
            '"pip install dependency-injector[yaml]"',
        )


class ConfigFromYamlWithEnvInterpolationTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

        os.environ['CONFIG_TEST_ENV'] = 'test-value'

        _, self.config_file = tempfile.mkstemp()
        with open(self.config_file, 'w') as config_file:
            config_file.write(
                'section1:\n'
                '  value1: ${CONFIG_TEST_ENV}\n'
            )

    def tearDown(self):
        del self.config
        del os.environ['CONFIG_TEST_ENV']
        os.unlink(self.config_file)

    @unittest.skipIf(sys.version_info[:2] == (3, 4), 'PyYAML does not support Python 3.4')
    def test_env_variable_interpolation(self):
        self.config.from_yaml(self.config_file)

        self.assertEqual(
            self.config(),
            {
                'section1': {
                    'value1': 'test-value',
                },
            },
        )
        self.assertEqual(self.config.section1(), {'value1': 'test-value'})
        self.assertEqual(self.config.section1.value1(), 'test-value')


class ConfigFromDict(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')

        self.config_options_1 = {
            'section1': {
                'value1': '1',
            },
            'section2': {
                'value2': '2',
            },
        }
        self.config_options_2 = {
            'section1': {
                'value1': '11',
                'value11': '11',
            },
            'section3': {
                'value3': '3',
            },
        }

    def test(self):
        self.config.from_dict(self.config_options_1)

        self.assertEqual(self.config(), {'section1': {'value1': '1'}, 'section2': {'value2': '2'}})
        self.assertEqual(self.config.section1(), {'value1': '1'})
        self.assertEqual(self.config.section1.value1(), '1')
        self.assertEqual(self.config.section2(), {'value2': '2'})
        self.assertEqual(self.config.section2.value2(), '2')

    def test_merge(self):
        self.config.from_dict(self.config_options_1)
        self.config.from_dict(self.config_options_2)

        self.assertEqual(
            self.config(),
            {
                'section1': {
                    'value1': '11',
                    'value11': '11',
                },
                'section2': {
                    'value2': '2',
                },
                'section3': {
                    'value3': '3',
                },
            },
        )
        self.assertEqual(self.config.section1(), {'value1': '11', 'value11': '11'})
        self.assertEqual(self.config.section1.value1(), '11')
        self.assertEqual(self.config.section1.value11(), '11')
        self.assertEqual(self.config.section2(), {'value2': '2'})
        self.assertEqual(self.config.section2.value2(), '2')
        self.assertEqual(self.config.section3(), {'value3': '3'})
        self.assertEqual(self.config.section3.value3(), '3')


class ConfigFromEnvTests(unittest.TestCase):

    def setUp(self):
        self.config = providers.Configuration(name='config')
        os.environ['CONFIG_TEST_ENV'] = 'test-value'

    def tearDown(self):
        del self.config
        del os.environ['CONFIG_TEST_ENV']

    def test(self):
        self.config.from_env('CONFIG_TEST_ENV')
        self.assertEqual(self.config(), 'test-value')

    def test_default(self):
        self.config.from_env('UNDEFINED_ENV', 'default-value')
        self.assertEqual(self.config(), 'default-value')

    def test_with_children(self):
        self.config.section1.value1.from_env('CONFIG_TEST_ENV')

        self.assertEqual(self.config(), {'section1': {'value1': 'test-value'}})
        self.assertEqual(self.config.section1(), {'value1': 'test-value'})
        self.assertEqual(self.config.section1.value1(), 'test-value')
