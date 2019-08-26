import re

class CommandlineParser():
  '''
  [condition]
  パラメータcmd_argvはスペース区切りされた文字列
  （with_cmdをFalseに設定するとcmd_argvを初めからパースする）

  [usage]
  # インスタンスの準備
  cp = CommandlineParser()
  # 設定の追加
  cp.add_setting('keyword', shorthand='k')
  # パースの実行
  cp.parse(sys.argv)
  # すべての引数を取得
  arguments = cp.get_arguments()
  # 特定の引数を取得
  arg_keyword = cp['keyword']

  [ex]
  cmd arg
  cmd arg=val    (keyword='arg', pre='',  sep='=')
  cmd --arg val  (keyword='arg', pre='-', sep=' ')
  cmd -a v       (keyword='arg', pre='-', sep=' ',  shorthand='a')
  cmd --arg=val  (keyword='arg', pre='-', sep='=')
  cmd -a=val     (keyword='arg', pre='-', sep='=', shorthand='a')
  cmd --arg      (keyword='arg', pre='-', sep='')
  cmd -a         (keyword='arg', pre='-', sep='', shorthand='a')
  cmd --arg      (keyword='arg', pre='-', switch=True)
  cmd -a         (keyword='arg', pre='-', shorthand='a', switch=True)

  [note]
  settings = {
    keyword:
      default: None (default is not defined)
      shorthand: 'k'
      converter: int (default='str')
      pre: '-' (default='-')
      sep: ' ' (default=' ')
      description: 'xxxx' (default='')
  }
  '''

  def __init__(self):
    self.argv = {}
    self.settings = {}
  
  def __getitem__(self, key):
    return self.argv[key]
  
  def get_arguments(self):
    return self.argv

  def add_setting(self, keyword, default=None, shorthand=None, converter=str, prefix='-', sep=' ', switch=False, description=''):
    if shorthand is not None and shorthand in [s['shorthand'] for s in self.settings.values()]:
      raise Exception('shorthand:{} has already been used.'.format(shorthand))
    if switch:
      sep = ''
    pre = '{pre}{{1,2}}(?!{pre})'.format(pre=prefix) if prefix != '' else ''
    key = '(({keyword})|({shorthand}))'.format(keyword=keyword, shorthand=shorthand) if shorthand is not None else keyword
    sep_re = sep+'.*?' if (sep != '' and sep != ' ') else ''
    re_str = '^{pre}{key}{sep}$'.format(pre=pre,key=key,sep=sep_re)
    self.settings[keyword] = {
      'shorthand': shorthand,
      'converter': converter,
      'pre': prefix,
      'sep': sep,
      'description': description,
      'cmpl': re.compile(re_str),
    }
    if default is not None:
      self.argv[keyword] = default
    elif sep == '':
      self.argv[keyword] = False
  
  def parse(self, cmd_argv, with_cmd=True):
    if len(self.settings) == 0:
      self.argv = {key:key for key in cmd_argv}
    else:
      i = 1 if with_cmd else 0 #スクリプトコマンドはスキップ
      counter = 0
      while i < len(cmd_argv):
        check = {keyword:s['cmpl'].match(cmd_argv[i]) is not None for keyword, s in self.settings.items()}
        if True in check.values():
          keyword = {value:key for key, value in check.items()}[True]
          s = self.settings[keyword]
          if s['sep'] == '':
            self.argv[keyword] = True
          elif s['sep'] == ' ':
            try:
              self.argv[keyword] = s['converter'](cmd_argv[i+1])
            except:
              raise Exception('keyword:{} convertion failed by {}'.format(cmd_argv[i+1], s['converter']))
            i += 1
          else:
            try:
              self.argv[keyword] = s['converter'](cmd_argv[i].split(s['sep'])[1])
            except:
              raise Exception('keyword:{} convertion failed by {}'.format(cmd_argv[i].split(s['sep'])[1], s['converter']))
        else:
          self.argv[counter] = cmd_argv[i]
          counter += 1
        i += 1
    return self.argv
  
  def help(self):
    '''
    [sample]
    --argument [VAL], -a [VAL]  (int)    this is commandline argument
    --Argument=[VAL], -A=[VAL]  (int)    this is another commandline argument

    [note]
    if max command strings is larger than 40 characters,
    help message becomes double lines.
    '''
    if len(self.settings) == 0:
      return 'commandline settings not found...'
    arg_str = [
      {
      'arg': '{}{}{}{}{}'.format(
        s['pre']*2 + keyword + s['sep'],
        '[VAL]' if s['sep'] != '' else '',
        ', ' + s['pre'] + s['shorthand'] + s['sep'] if s['shorthand'] is not None else '',
        '[VAL]' if s['shorthand'] is not None and s['sep'] != '' else '',
        '  ({})'.format(s['converter']) if s['converter'] is not str else '',
      ),
      'description': s['description']
      }
      for keyword, s in self.settings.items()
    ]
    max_str_number = max([len(a['arg']) for a in arg_str]) + 4
    help_str = ''
    for a in arg_str:
      pad = ' ' * (max_str_number - len(a['arg'])) if max_str_number < 40 else '\n    '
      if a['description'] == '':
        pad = ''
      help_str += '{arg}{pad}{desc}\n'.format(arg=a['arg'],pad=pad,desc=a['description'])
    return help_str

def test():
  '''
  cmd --arg arg -a argRewrite --arg2 2 arg3=3 --arg4=4 -f=44 nop --switch
  ===> {
    0: 'nop',
    'arg': 'argRewrite',
    'arg2': '2',
    'arg3': '3',
    'arg4': 44,
    'arg5': 'default',
    'switch': True,
  }
  '''
  cp = CommandlineParser()
  cp.add_setting('arg', shorthand='a', description='desc')
  cp.add_setting('arg2', description='desc')
  cp.add_setting('arg3', prefix='', sep='=', description='desc')
  cp.add_setting('arg4', shorthand='f', sep='=', description='desc', converter=int)
  cp.add_setting('arg5', default='default')
  cp.add_setting('switch', switch=True)
  cp.add_setting('dummyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy', description='desc')
  print(cp.help())
  test_argv = 'cmd --arg arg -a argRewrite --arg2 2 arg3=3 --arg4=4 -f=44 nop --switch'.split(' ')
  cp.parse(test_argv)
  print(cp.get_arguments())
  print(cp['arg'])
  print(cp['arg2'])
  print(cp['arg3'])
  print(cp['arg4'])
  print(cp[0])

if __name__ == '__main__':
  test()