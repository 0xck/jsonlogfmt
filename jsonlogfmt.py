# Copyright 2018 by Constantine Kormashev. All Rights Reserved.
# Licensed under Mozilla Public License Version 2.0 (the "License");
# You may obtain a copy of the License at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Formatting class for logging.Logger, composes JSON message from logging.Logger message.
# Using is pretty simple, just use JSONMapFormatter obj in `setFormatter` of logging.Handler obj

from logging import Formatter
from collections import Mapping, MutableMapping, OrderedDict
from functools import reduce
from json import dumps
from random import randrange

# sentiel for some checkings
SENTINEL = hex(randrange(10**16)).encode()

# default JSON map
JSONMAP = OrderedDict({
    'time': '',
    'levelname': '',
    'name': '',
    'msg': '',
    'extra': OrderedDict({
            'funcName': '',
            'lineno': '',
            'pathname': '',
            'exception': OrderedDict({
                'exctype': '',
                'excvalue': '',
                'exctrace': ''
            })
    })
})

AUXMAP = {
    'time': 'time',
    'exctype': 'exctype',
    'excvalue': 'excvalue',
    'exctrace': 'exctrace'
}


class JSONMapFormatter(Formatter):
    """ JSONMapFormatter allows format standard logging messasges to JSON

    One uses dict-like map which describes keys are included in new formatted message.
    Moreover standard logging fuction partially saved, default formatting style is still supported,
    e.g. define format as '%(asctime)s %(name)s' and logger returns those values in log message.
    That may be useful for some purposes e.g. for creating standard syslog entry with extra JSON message.
    """

    def __init__(
            self, jsonmap=JSONMAP, remap=None, auxmap={},
            extrakeys=['extra', 'data'], argskey=['args'], null='',
            strip=False, fmt='%(message)s', datefmt=None, style='%'):
        """ init function

        parameters:
            kwargs:
                jsonmap (Mapping): dict-like obj describes JSON message default: JSONMAP
                remap (Mapping): dict-like obj allows to remap default Logger attributes names; default: None
                auxmap (Mapping): dict-like obj allows to remap auxiliary dict-like obj,
                    which serves for contain additional values for time and exception; default: {}
                extrakeys (MutableSequence): sequence contains path to extra key,
                    which serves for additional values created from dict-like message entries;
                    default: ['extra', 'data']
                argskey (MutableSequence): sequence contains path to args key,
                    which serves for additional values from nondict-like enties; default: ['args'];
                    this value will be added to `extrakeys` path
                null (any): terminator shows empty values, useful in `jsonmap`; default: ''
                strip (bool): defines if empty `jsonmap` values will be added to message; default: False
                fmt (str): logging message format; default: '%(message)s'
                datefmt (str): logging date format; default: None
                style (str): logging type of format; default: '%'
        """

        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.jsonmap = jsonmap
        self.remap = remap
        self.extrakeys = extrakeys
        self.argskey = argskey
        self.null = null
        self.strip = strip
        # dict-like (MutableMapping) obj for future msg which will be based on `jsonmap`
        self.msg = OrderedDict()
        # dict-like (MutableMapping) obj for auxiliary values
        # one is always used for generating messages
        self.aux = OrderedDict()
        # make new auxmap from AUXMAP and given
        if auxmap:
            tmp_auxmap = AUXMAP.copy()
            tmp_auxmap.update(auxmap)
            self.auxmap = tmp_auxmap
        else:
            self.auxmap = AUXMAP

    def _set_extra(self, data, keys, value):
        """ sets values to nested dict from keys path

        parameters:
            args:
                data (Mapping): dict-like obj for adding
                keys (list): sequence contains path
                value (any): value for adding to `data`
        """

        # set extra path
        # type(a)() is more universal than {}
        reduce(lambda x, key: x.setdefault(key, type(data)()), keys[:-1], data)
        # set value
        reduce(lambda x, key: x.setdefault(key, value), keys, data)

    def _msg_filler(self, jsonmap, data, msg=None):
        """ fills msg from given data recursively bypassing jsonmap

        parameters:
            args:
                jsonmap (Mapping): dict-like obj describes JSON message
                data (Mapping): dict-like obj contains values for adding
            kwargs:
                msg (MutableMapping): dict-like obj for adding; default: None

            returns (bool): if values was added to keys
        """
        empty = True
        # defines msg from self, that means 1st enter to recursively bypassing
        msg = self.msg if msg is None else msg

        # recursively bypassing each jsonmap entry
        for i in jsonmap:

            # if value is dict-like obj than recursively bypassing one
            if isinstance(jsonmap[i], Mapping):
                # creates a new dict-like (MutableMapping) obj
                # which will be used for filling new values
                msg[i] = OrderedDict()
                emp = self._msg_filler(jsonmap[i], data, msg=msg[i])
                # in case strip is enabled removes latest key in case no one value was added
                if self.strip and emp:
                    del msg[i]

            # adding value in case one does not exist
            else:
                item = data.pop(i, self.null)
                # does not add empty value in case strip is enabled
                if self.strip and item is self.null:
                    continue

                # remap JSON message key with remap dict-like obj
                if self.remap:
                    i = self.remap.get(i, i)

                # set key if one does not exist
                # SENTINEL is for preventing crossing with self.null because one for example can be None
                if msg.get(i, SENTINEL) is SENTINEL:
                    msg[i] = item
                    if empty:
                        empty = False

        return empty

    def generate_msg(self, record):
        """ set msg data from given log messages and args

        parameters:
            args:
                record (LogRecord): logger obj contains logging info
        """

        # create entry contains processed data
        extramsg = record.__dict__.copy()
        extramsg.update(self.aux)
        # getting data from args
        # only MutableMapping can be used because values will be poped from them
        emsglist = [record.args] if isinstance(record.args, MutableMapping) else [i for i in record.args if isinstance(i, MutableMapping)]
        # !!! be careful
        # values of dict-like obj if they have similar values on one level will be rewritten on value of latest obj
        # as  dict.update() does it
        for i in emsglist:
            extramsg.update(i)

        # filling from args, set new keys and values from given in log message args
        self._msg_filler(self.jsonmap, extramsg)

        # getting rest values, excludes native log items
        extramsg = {k: v for k, v in extramsg.items() if k not in set(extramsg).intersection(set(record.__dict__))}
        # set rest args dict as extra value
        if extramsg:
            self._set_extra(self.msg, self.extrakeys, extramsg)

        # if no more args
        if isinstance(record.args, MutableMapping):
            return

        # set rest args (nondict)
        eargs = [i for i in record.args if not isinstance(i, MutableMapping)]
        if eargs:
            self._set_extra(self.msg, self.extrakeys + self.argskey, eargs)

    def prep_aux(self, record):
        """ Handle auxiliary entries which will be used in message generating process.

        Usually those are different values of record that need to be preprocessed in some way.

        parameters:
            args:
                record (LogRecord): logger obj contains logging info
        """

        # formatted time entry
        self.aux[self.auxmap['time']] = super().formatTime(record)

        # formatted exception entry
        if record.exc_info:
            self.aux[self.auxmap['exctype']] = record.exc_info[0].__name__
            self.aux[self.auxmap['excvalue']] = record.exc_info[1].args
            self.aux[self.auxmap['exctrace']] = record.exc_text if record.exc_text else super().formatException(record.exc_info)

    def format(self, record):
        """ rewriting Formatter().format method

        Makes new JSON message from given logger obj,
        changes record.msg attribute to new message,
        returns Formatter().format method.

        parameters:
            args:
                record (LogRecord): logger obj contains logging info
        returns (str): log string created by Formatter class
        """

        # only one passing is needed for first handler, other handlers can use earlier msg
        if self.msg:
            return super().format(record)

        # preprocess auxiliary entries
        self.prep_aux(record)
        # filling data from record
        self.generate_msg(record)

        # if exception, msg has to me changed because exceptions is not JSON serializable
        if record.exc_info:
            self.msg['msg'] = self.aux[self.auxmap['excvalue']][0] if self.aux[self.auxmap['excvalue']] else self.aux[self.auxmap['exctype']]
            # prevents generate additional message from Formatter
            record.exc_info = None

        # set record message
        record.msg = dumps(self.msg)
        # deleting args, needs for Formatter().format
        record.args = ()

        return super().format(record)
