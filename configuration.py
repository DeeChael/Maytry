import json
import os
from abc import ABC
from copy import deepcopy
from typing import Union, List


class Configuration(ABC):
    def get(self, key: str):
        pass

    def get_or_default(self, key: str, default):
        pass

    def set(self, key: str, value: Union[str, int, bool, float, List[Union[str, int, bool, float]]]) -> bool:
        pass

    def set_default(self, key: str, value: Union[str, int, bool, float, List[Union[str, int, bool, float]]]) -> bool:
        if not self.contains(key):
            self.set(key, value)
            return True
        return False

    def remove(self, key: str) -> bool:
        pass

    def contains(self, key: str) -> bool:
        pass

    def save(self):
        pass

    def load(self):
        pass

    def as_dict(self) -> dict:
        pass

    def __str__(self):
        return self.as_dict()


class JsonConfiguration(Configuration):
    """
    Don't use '*' in key, because this is a character to split!
    """

    _file: str
    _content: dict

    def __init__(self, file: str):
        self._file = file
        self.load()

    def get(self, key: str):
        return self.get_or_default(key, None)

    def get_or_default(self, key: str, default):
        key = key.lstrip('*').lstrip('*')
        if len(key) <= 0:
            return default
        if '*' in key:
            split_str = key.split('*', count(key, '*') - 1)
            cache_split_str_last_object = split_str[len(split_str) - 1]
            split_str[len(split_str) - 1] = cache_split_str_last_object.split("*")[0]
            last_key = key.rsplit('*', 1)[1]
            cache_dict = self._content
            for sub in split_str:
                if sub in cache_dict:
                    if not isinstance(cache_dict[sub], dict):
                        return default
                    cache_dict = cache_dict[sub]
                else:
                    return default

            if last_key in cache_dict:
                return cache_dict[last_key]
            else:
                return default
        else:
            if key in self._content:
                return self._content[key]
            else:
                return default

    def set(self, key: str, value: Union[str, int, bool, float, List[Union[str, int, bool, float]], Configuration]) -> bool:
        key = key.lstrip('*').lstrip('*')
        if len(key) <= 0:
            return False
        if '*' in key:
            split_str = key.split('*', count(key, '*') - 1)
            cache_split_str_last_object = split_str[len(split_str) - 1]
            split_str[len(split_str) - 1] = cache_split_str_last_object.split("*")[0]
            last_key = key.rsplit('*', 1)[1]
            cache_dict = self._content
            for sub in split_str:
                if sub in cache_dict:
                    if not isinstance(cache_dict[sub], dict):
                        return False
                    cache_dict = cache_dict[sub]
                else:
                    new_dict = dict()
                    cache_dict[sub] = new_dict
                    cache_dict = new_dict
            cache_dict[last_key] = value
            return True
        else:
            self._content[key] = value
            return True

    def remove(self, key: str) -> bool:
        key = key.lstrip('*').lstrip('*')
        if len(key) <= 0:
            return False
        if '*' in key:
            split_str = key.split('*', count(key, '*') - 1)
            cache_split_str_last_object = split_str[len(split_str) - 1]
            split_str[len(split_str) - 1] = cache_split_str_last_object.split("*")[0]
            last_key = key.rsplit('*', 1)[1]
            cache_dict = self._content
            for sub in split_str:
                if sub in cache_dict:
                    if not isinstance(cache_dict[sub], dict):
                        return False
                    cache_dict = cache_dict[sub]
                else:
                    return False
            if last_key in cache_dict:
                cache_dict.pop(last_key)
                return True
            else:
                return False
        else:
            if key in self._content:
                self._content.pop(key)
                return True
            else:
                return False

    def contains(self, key: str) -> bool:
        key = key.lstrip('*').lstrip('*')
        if len(key) <= 0:
            return False
        if '*' in key:
            split_str = key.split('*', count(key, '*') - 1)
            cache_split_str_last_object = split_str[len(split_str) - 1]
            split_str[len(split_str) - 1] = cache_split_str_last_object.split("*")[0]
            last_key = key.rsplit('*', 1)[1]
            cache_dict = self._content
            for sub in split_str:
                if sub in cache_dict:
                    if not isinstance(cache_dict[sub], dict):
                        return False
                    cache_dict = cache_dict[sub]
                else:
                    return False
            if last_key in cache_dict:
                return True
            else:
                return False
        else:
            if key in self._content:
                return True
            else:
                return False

    def save(self):
        with open(self._file, 'w') as configuration_file:
            configuration_file.write(json.dumps(self._content))

    def load(self):
        self._content = dict()
        if os.path.exists(self._file) and os.path.isfile(self._file):
            with open(self._file, 'r') as configuration_file:
                self._content = json.loads(configuration_file.read())

    def as_dict(self) -> dict:
        return deepcopy(self._content)


class SimpleConfiguration(Configuration):

    """
    Key cannot contains ' '
    But value can
    """

    _file: str
    _content: dict

    def __init__(self, file: str):
        self._file = file
        self.load()

    def get(self, key: str):
        return self.get_or_default(key, None)

    def get_or_default(self, key: str, default):
        key = key.replace(' ', '')
        if key in self._content:
            return self._content[key]
        return default

    def set(self, key: str, value: Union[str, int, bool, float, List[Union[str, int, bool, float]], Configuration]) -> bool:
        self._content[key.replace(' ', '')] = value
        return True

    def remove(self, key: str) -> bool:
        return self._content.pop(key.replace(' ', ''))

    def contains(self, key: str) -> bool:
        return key.replace(' ', '') in self._content

    def save(self):
        string_content = ''
        for key in self._content.keys():
            string_content += str(key) + ' ' + str(self._content[key]) + '\n'
        with open(self._file, 'w') as configuration_file:
            configuration_file.write(string_content)

    def load(self):
        self._content = dict()
        if os.path.exists(self._file) and os.path.isfile(self._file):
            with open(self._file, 'r') as configuration_file:
                temp_dict = dict()
                string_content = configuration_file.read()
                for key_value in string_content.split('\n'):
                    if ' ' in key_value:
                        split_string = key_value.split(' ', 1)
                        if len(split_string[0]) > 0 and len(split_string[1]) > 0:
                            temp_dict[split_string[0]] = split_string[1]
                self._content = temp_dict

    def as_dict(self) -> dict:
        return deepcopy(self._content)


def count(to_be_count: str, char: str) -> int:
    return int((len(to_be_count) - len(to_be_count.replace(char, ''))) / len(char))
