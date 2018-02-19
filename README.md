# JSON formatter for logging.Logger
Allows format standard logging messasges to JSON

## Usage
import `JSONMapFormatter` and use one for `logging.Handler` obj.

### Terms
Look at logger argumets for `logger.info('MESSAGE', {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2}, 'value': 1}, 'more value', 'one more value', {'4th': 4})`:
* 1st is always message obj, in this example: _'MESSAGE'_
* dict-like objs that may be described by JSONMap or just stored in one of JSON path, in this example: _{'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2}, 'value': 1}_ and _{'4th': 4}_
*  non dict-like objs or **args** that just stored in one of JSON path, in this example: _'more value'_ and _'one more value'_

### Simple example:

_test.py:_

```python
import logging
from jsonlogfmt import JSONMapFormatter

fmt = JSONMapFormatter()

console = logging.StreamHandler()
console.setFormatter(fmt)
console.setLevel(logging.INFO)

logger = logging.getLogger()
logger.addHandler(console)
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    logger.info('MESSAGE', {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2}, 'value': 1}, 'more value', 'one more value', {'4th': 4})
```

_Output:_

_(output was formatted, original is ordinary flat string)_

```json
{'extra': {'data': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                    '4th': 4,
                    'args': ['more value', 'one more value']},
           'exception': {'type': '', 'value': 1},
           'funcName': '<module>',
           'lineno': 18,
           'pathname': './test.py'},
 'levelname': 'INFO',
 'msg': 'MESSAGE',
 'name': 'root',
 'time': '2018-02-05 21:06:25,618'}

```

### Default logging format example:
Default logging formatting is also supported. That may be useful for some purposes e.g. for creating standard syslog entry with extra JSON message. Changing `JSONMapFormatter()` to `JSONMapFormatter(fmt='%(name)s / %(asctime)s / %(message)s')` gives:

_Output:_

_(output was formatted, original is ordinary flat string)_

```json
root / 2018-02-05 21:08:20,876 / 
{'extra': {'data': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                    '4th': 4,
                    'args': ['more value', 'one more value']},
           'exception': {'type': '', 'value': 1},
           'funcName': '<module>',
           'lineno': 18,
           'pathname': './test.py'},
 'levelname': 'INFO',
 'msg': 'MESSAGE',
 'name': 'root',
 'time': '2018-02-05 21:08:20,876'}

```

### Custom JSONMap
By default `JSONMapFormatter` uses JSONMAP dict-like obj, one can be changed.

```python
newJSONMap = {'created': '',
    'extra': OrderedDict([('funcName', '')]),
    'levelname': '',
    'msg': '',
    'time': ''}

fmt = JSONMapFormatter(jsonmap=newJSONMap)

```

_Output:_

_(output was formatted, original is ordinary flat string)_

```json
{'created': 1517855408.837364,
 'extra': {'data': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                    '4th': 4,
                    'args': ['more value', 'one more value'],
                    'value': 1},
           'funcName': '<module>'},
 'levelname': 'INFO',
 'msg': 'MESSAGE',
 'time': '2018-02-05 21:30:08,837'}
```

**Note.**

Be careful, entry values of dict-like obj if they have similar keys on one level **will be rewritten** on value of latest obj.

Also in addition to Logger object attribetes there are several keys that define some values:
* _time_ is for formatted time
* _exctype_ is for name of class of exception
* _excvalue_ is for exception args attribute (usualy one contains exception message)
* _exctrace_ is for formatted exception traceback

All of them use default formatting from Formatter class

### Remap default Logger keys
JSON map requires to set keys defined in Logger class, like `levelname` or `msg` for retriving appropriate value from Logger object. But those keys can be remapped by using `remap` dict-like obj so that JSON message will contain defined in `remap` keys instead any keys in JSON map. E. g.

```python
REMAP = {
  'time': 'Time of issue',
  'levelname': 'LEVEL',
  'funcName': 'function'}

fmt = JSONMapFormatter(jsonmap=newJSONMap, remap=REMAP)

```
_Output:_

_(output was formatted, original is ordinary flat string)_

```json
{'LEVEL': 'INFO',
 'Time of issue': '2018-02-10 21:25:15,482',
 'created': 1518287115.4829462,
 'extra': {'data': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                    '4th': 4,
                    'args': ['more value', 'one more value'],
                    'value': 1},
           'function': '<module>'},
 'msg': 'MESSAGE'}

```

**Note.**

Maybe you have a question: why would you not use JSON map for structure of JSON message and remap for defining Logger keys that has to be changed? E. g. 
```python
JSONMAP = {
  'Time':'',
  'LEVEL':'',
  'extra':
    'Message':''}

REMAP = {
  'Time': 'time',
  'LEVEL': 'levelname',
  'Message': 'msg'}

```
Answer is pretty simple this is more complicated.

### Custom extrakeys and argskey
By default for storing extra data _extra: {data: {}}_ path is used (_extra: {data: {args: {}}}_ for non dict-like args) that behavior can be changed. Use `extrakeys` for dict-like obj and `argskey` for non dict-like args). E.g. `fmt = JSONMapFormatter(jsonmap=newJSONMap, extrakeys=['newExtrapath', 'subpath'], argskey=['newArgspath'])` gives:

_Output:_

_(output was formatted, original is ordinary flat string)_

```json
{'created': 1517856642.977184,
 'extra': {'funcName': '<module>'},
 'levelname': 'INFO',
 'msg': 'MESSAGE',
 'newExtrapath': {'subpath': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                              '4th': 4,
                              'newArgspath': ['more value', 'one more value'],
                              'value': 1}},
 'time': '2018-02-05 21:50:42,977'}
 ```

**Note.**

`extrakeys` is parent path for `argskey` that means non dict-like args stores in common extra path.


### Remap time and exception keys:
For some reason additional keys for time and exception defined in separate dict-like obj. By default those keys and values are:
* _time_ for formatted time (default formatting from Formatter class)
* _exctype_ for exception class
* _excvalue_ exception arguments, usually message
* _exctrace_ exception traceback

All of them or just part can be changed. Also JSONMap has to changed for new keys. E.g. 

```python

AUXMAP = {
    'exctype': 'type',
    'excvalue': 'value',
    'exctrace': 'traceback'
}


JSONMAP = OrderedDict({
    'time': '',
    'levelname': '',
    'name': '',
    'msg': '',
    'extra': OrderedDict({
            'exception': OrderedDict({
                'type': '',
                'value': '',
                'traceback': ''
            })
    })
})

fmt = JSONMapFormatter(jsonmap=JSONMAP, auxmap=AUXMAP)

```

_Output:_

_(output was formatted, original is ordinary flat string)_

```json

{'extra': {'exception': {'traceback': 'Traceback (most recent call last):\n'
                                      '  File "./test.py", line 57, in '
                                      '<module>\n'
                                      '    1/0\n'
                                      'ZeroDivisionError: division by zero',
                         'type': 'ZeroDivisionError',
                         'value': ['division by zero']}},
 'levelname': 'ERROR',
 'msg': 'division by zero',
 'name': 'root',
 'time': '2018-02-19 15:35:41,990'}
```

### Stripping empty values
By default all values defined in JSON map will be added even some of them are empty, to change this behavior set `strip` variable to `True`. That prevents appearance of empty values in message. But it does not prevent empty values if they are added via _args_.

```python

newJSONMap = OrderedDict([('time', ''),
   ('levelname', ''),
   ('EMPTY', OrderedDict()),
   ('msg', ''),
   ('extra', OrderedDict([('funcName', '')])),
   ('created', '')])

fmt = JSONMapFormatter(jsonmap=newJSONMap, extrakeys=['newExtrapath', 'subpath'], argskey=['newArgspath'], strip=True)
```

_Output:_

_(output was formatted, original is ordinary flat string)_

```json
{'created': 1517906994.2913642,
 'extra': {'funcName': '<module>'},
 'levelname': 'INFO',
 'msg': 'MESSAGE',
 'newExtrapath': {'subpath': {'1st': {'2nd': {'3rd': {'value': 3}}, 'value': 2},
                              '4th': 4,
                              'newArgspath': ['more value', 'one more value'],
                              'value': 1}},
 'time': '2018-02-06 11:49:54,291'}
```

As you can see there is not `EMPTY` key in output above.
