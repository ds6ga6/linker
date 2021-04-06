import sys
import os
import json
import re
import random
import time
import shutil
import copy

import subprocess
import psutil

WAYTOGETCOMMAND = 'text_from_file'

MDFILEPATH = 'data_user\\mdfiles\\' # 放 0.md, 1.md 的地方
DIRPATH = 'data_user\\mddirs\\' # 放 1, 2, 3, 文件夹的地方
OPENEDPATH = '..\\..\\mdfiles\\' # 放打开的 md 文件的地方
TEMPPATH = 'data_source\\.temp\\' # 放 temp 文件的地方

PKPATH = 'data_source\\maps\\pk.json' # 放 id 与 pk 的映射表
FNPATH = 'data_source\\maps\\fn.json' # 放 id 与 filename 的映射表
DNPATH = 'data_source\\maps\\dn.json' # 放 id 与 dirname 的映射表

RECORDPATH = 'core\\record.json' # 放 nextid 之类的

TASK_TEMP_PATH = 'data_source\\tasks.json'
TASKS_PATH = '..\\..\\.vscode\\tasks.json'

BACKUPPATH = 'data_source\\.backup\\'


assert len(sys.argv) == 13
args = {
	"workspaceFolder"			: sys.argv[1],	#	/home/your-username/your-project
	"workspaceFolderBasename"	: sys.argv[2],	#	your-project
	"file"						: sys.argv[3],	#	/home/your-username/your-project/folder/file.ext
	"fileWorkspaceFolder"		: sys.argv[4],	#	/home/your-username/your-project
	"relativeFile"				: sys.argv[5],	#	folder/file.ext
	"relativeFileDirname"		: sys.argv[6],	#	folder
	"fileBasename"				: sys.argv[7],	#	file.ext
	"fileBasenameNoExtension"	: sys.argv[8],	#	file
	"fileDirname"				: sys.argv[9],	#	/home/your-username/your-project/folder
	"fileExtname"				: sys.argv[10],	#	.ext
	"lineNumber"				: int(sys.argv[11]),
	"pathSeparator"				: sys.argv[12]	#	/ on macOS or linux, \\ on Windows
}

def removeSecure(filepath, backupload=BACKUPPATH):
	with open(filepath, 'rb') as f:
		data = f.read()
	with open(backupload + filepath.split('\\')[-1], 'wb') as f:
		f.write(data)
	os.remove(filepath)
def writeSecure(text, filepath, backupload=BACKUPPATH):
	with open(filepath, 'rb') as f:
		data = f.read()
	with open(backupload + filepath.split('\\')[-1], 'wb') as f:
		f.write(data)
	with open(filepath, 'w', encoding='utf-8') as f:
		f.write(text)

def printInColor(text, color):
	colorDict = {
		'black'		: '30',
		'red'		: '31',
		'green'		: '32',
		'yellow'	: '33',
		'blue'		: '34',
		'purple'	: '35',
		'white'		: '37',
		'default'	: '38'
	}
	print("\033[" + colorDict[color] + "m" + text + "\033[0m")
def dictGetKey(dicty, value):
	for key in dicty.keys():
		if(value == dicty[key]):
			return key
def printErrorInfor(text, color):
	text += " | func: " + sys._getframe().f_back.f_code.co_name + ", line: " + str(sys._getframe().f_back.f_lineno)
	printInColor(text, color)

def exec_cmd(command):
	if(command.split(' ', 1)[0] == 'start' or command == ''):
		with open(TASK_TEMP_PATH, 'r', encoding='utf-8') as f:
			task_data = json.load(f)
		task_data['tasks'][0]["command"] = command
		with open(TASKS_PATH, "w", encoding='utf-8') as f:
			json.dump(task_data, f, ensure_ascii=False, indent='\t')
	else:
		os.system(command)
	

class IDDICT():
	def __init__(self):
		self.pkload = PKPATH
		self.fnload = FNPATH
		self.dnload = DNPATH
		self.readfile()
	def __del__(self):
		self.writefile()
		print("已成功保存结果。")

	# 初始化 pk 文件
	def init_pk(self):
		pkset =  set()
		for i in range(0, 26):
			for j in range(0, 26):
				pkch = chr(ord('a') + i) + chr(ord('a') + j)
				pkset.add(pkch)
		self.pkdict = {
			"unusedpk": list(pkset),
			"pkidmap": {}
		}
	# 把 pk, fn 文件中的内容读到 self.pkdict, self.fndict
	def readfile(self):
		# 读 pk.json
		if(os.path.exists(self.pkload)):
			with open(self.pkload, 'r') as f:
				self.pkdict = json.load(f)
		else:
			self.init_pk()
		# 读 fn.json
		if(os.path.exists(self.fnload)):
			with open(self.fnload, 'r', encoding='utf-8') as f:
				self.fndict = json.load(f)
		else:
			self.fndict = {}
		# 读 dn.json
		if(os.path.exists(self.dnload)):
			with open(self.dnload, 'r', encoding='utf-8') as f:
				self.dndict = json.load(f)
		else:
			self.dndict = {}
	# 把 self.pkdict, self.fndict 保存到 pk 文件中
	def writefile(self):
		text = json.dumps(self.pkdict, indent='\t')
		writeSecure(text, self.pkload)
		text = json.dumps(self.fndict, indent='\t', ensure_ascii=False)
		writeSecure(text, self.fnload)
		text = json.dumps(self.dndict, indent='\t', ensure_ascii=False)
		writeSecure(text, self.dnload)
	# 分配出一个 pk，并更新列表
	def get_pk(self, uid):
		if(uid in self.pkdict['pkidmap'].values()): # pk 列表中有对应的 uid
			return dictGetKey(self.pkdict['pkidmap'], uid)
		else:
			if(len(self.pkdict['unusedpk']) == 0): # pk没有了，遍历打开的文件，把没用的都删掉
				old_pkidmap = self.pkdict['pkidmap']
				init_pk()
				new_pkset = set(self.pkdict['unusedpk'])
				for filename in self.fndict.keys():
					with open(OPENEDPATH + filename + '.md', 'r', encoding='utf-8') as f:
						pkunits = re.findall('\|`[a-z][a-z]`\|', f.read())
					for pkunit in pkunits:
						pkunit = pkunit[2:-2]
						if(pkunit in new_pkset):
							new_pkset -= pkunit
							self.pkdict['pkidmap'][pkunit] = old_pkidmap[pkunit]
				self.pkdict['unusedpk'] = list(new_pkset)
				printInColor("pk overflow. please run the command again", "blue")
				exit(0) # 因为更新了，又没法自动重新开始（没有goto），干脆让用户重运行次命令
			else:
				pkunit = random.choice(self.pkdict['unusedpk']) # 随机抽取 pk
				pkset = set(self.pkdict['unusedpk']) - set(pkunit) # 更新没使用的 pk 列表
				self.pkdict['unusedpk'] = list(pkset)
				self.pkdict['pkidmap'][pkunit] = uid
				return pkunit

iddict = IDDICT()

# pkstr: "|`pk`|commandstr|"
def uid_to_pkstr(uid):
	# 得到 commandstr
	with open(MDFILEPATH + str(uid) + '.md', 'r', encoding='utf-8') as f:
		commandstr = re.findall("\n@commands: [^\n]*\n", f.read())
	if(commandstr == []):
		commandstr = ""
	else:
		commandstr = commandstr[0][len('\n@commands: '):-1]
	# 得到 pk
	pkunit = iddict.get_pk(uid)
	return "|`" + pkunit + "`|" + commandstr + "|"
# name: 就是 id.md 文件首行的内容
def uid_to_name(uid):
	with open(MDFILEPATH + str(uid) + '.md', 'r', encoding='utf-8') as f:
		name = f.readline()
	if(name[-1] == '\n'):
		name = name[:-1]
	return name
# 在 0.md 中登记
def reg_in_0md(context):
	if(0 in iddict.fndict.values()):
		path0 = OPENEDPATH + dictGetKey(iddict.fndict, 0) + ".md"
		with open(path0, 'r', encoding='utf-8') as f:
			data0 = f.read()
		data0 = data0.replace("\n【END】", "\n" + context + "\n【END】")
		writeSecure(data0, path0)
# 删除 0.md 中的记录
def del_in_0md(context):
	if(0 in iddict.fndict.values()):
		path0 = OPENEDPATH + dictGetKey(iddict.fndict, 0) + ".md"
		with open(path0, 'r', encoding='utf-8') as f:
			data0 = f.read()
		# 提取 beg ... end 中的 data，只修改这里面的
		beg_end = re.findall("【BEG】[\s\S]*\n【END】", data0)[0]
		beg_end = beg_end.replace("\n" + context, "")
		data0 = re.sub("【BEG】[\s\S]*\n【END】", beg_end, data0)
		writeSecure(data0, path0)

# 打开文件
def op(uid, loadfile):
	uid_filename = MDFILEPATH + str(uid) + '.md'
	with open(uid_filename, 'r', encoding='utf-8') as f:
		data = f.read()
	# 得到文件名
	filename = data.split('\n', 1)[0]
	if(filename in iddict.fndict.keys()):
		# printInColor("This file is exist", "red")
		exec_cmd('code ' + '"' + OPENEDPATH + filename + '.md' + '"')
		return
	# 更改 |`id`|| 为 |`pk`||
	for uidstr in re.findall('\\|`\\d+`\\|', data):
		subuid = int(uidstr[2:-2])
		data = data.replace(uidstr, uid_to_pkstr(subuid))
	# 更改 road
	if(os.path.exists(loadfile)):
		with open(loadfile, 'r', encoding='utf-8') as f:
			oldroad = re.findall('\n@road: [^\n]*\n', f.read())
			temp = '|`' + iddict.get_pk(uid) + '`|'
			if(oldroad == []):
				newload = "\n@road: " + uid_to_pkstr(uid) + filename + '\n'
			elif(temp in oldroad[0]): # 返回的是上级目录
				newload = re.sub(temp.replace('|', '\|') + "[^\n]*\n", uid_to_pkstr(uid) + filename, oldroad[0]) + '\n'
			else:
				oldroad = oldroad[0][:-1]
				if(len(oldroad) >= len("\n@road: ")):
					oldroad += " -> "
				newload = oldroad + uid_to_pkstr(uid) + filename + '\n'
	data = data.replace("\n@road: ", newload)
	# 在 0.md 中登记
	temp = '[](' + filename + '.md)'
	reg_in_0md(temp)
	# 新建文件
	if(uid == 0): # 如果新建的是特殊的 0.md
		temp = ""
		# 写入文件
		for key in iddict.fndict.keys():
			temp += "\n" + '[](' + key + '.md)'
		# 写入文件夹
		for key in iddict.dndict.keys():
			temp += '\n`explorer "' + DIRPATH + key + '"`'
		data = re.sub("【BEG】[\\s\\S]*\n【END】", "【BEG】" + temp.replace('\\', '\\\\') + "\n【END】", data)
	with open(OPENEDPATH + filename + '.md', 'w', encoding='utf-8') as f:
		f.write(data)
	# 加入 fndict
	iddict.fndict[filename] = uid
	# 打开新建的文件供编辑
	exec_cmd('code ' + '"' + OPENEDPATH + filename + '.md' + '"')
# 打开文件夹
def opendir(uid):
	# 取到对应的 name
	name = uid_to_name(uid)
	# 判断是否打开
	if(name not in iddict.dndict.keys()): # 没打开
		# 更改文件夹的名字
		os.rename(DIRPATH + str(uid), DIRPATH + name)
		# 更改 dndict
		iddict.dndict[name] = uid
		# 更改 0.md，如果 0.md 已打开
		temp = '`explorer "' + DIRPATH + name + '"`'
		reg_in_0md(temp)
	else:
		exec_cmd('explorer "' + DIRPATH + name + '"')
# 新建文件
def nw(commandstr):
	# 获得 new_uid
	with open(RECORDPATH, 'r', encoding='utf-8') as f:
		record = json.load(f)
	new_uid = record['nextid']
	record['nextid'] += 1
	writeSecure(json.dumps(record, ensure_ascii=False, indent='\t'), RECORDPATH)
	# 新建文件
	with open(MDFILEPATH + str(new_uid) + '.md', 'w', encoding='utf-8') as f:
		f.write('untitled' + str(new_uid) + '\n')
		f.write('@data: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
		f.write('\n\n@road: \n')
		if(commandstr != ''):
			f.write('@commands: ' + commandstr + '\n\n')
	# 根据 commandstr 进行完善
	if('D' in commandstr): # 自带字典
		os.mkdir(DIRPATH + str(new_uid))
	
	return new_uid

# 保存文件
def sv(uid):
	uname = dictGetKey(iddict.fndict, uid)
	with open(OPENEDPATH + uname + '.md', 'r', encoding='utf-8') as f:
		data = f.read()
	# 判断 filename 是否改变，有则更新
	old_filename = dictGetKey(iddict.fndict, uid)
	new_filename = data.split('\n', 1)[0]
	if(old_filename != new_filename):
		# 给文件改名
		oldpath = OPENEDPATH + old_filename + '.md'
		newpath = OPENEDPATH + new_filename + '.md'
		os.rename(oldpath, newpath)
		# 在 fndict 中改名
		del iddict.fndict[old_filename]
		iddict.fndict[new_filename] = uid
	# 处理 |||
	temps = re.findall('\|\|[a-zA-Z]*\|', data)
	for temp in temps:
		tcommandstr = temp[2:-1]
		tuid = nw(tcommandstr)
		data = data.replace(temp, '|`' + iddict.get_pk(tuid) + '`|' + tcommandstr + '|', 1)
	# 更改已打开的文件
	writeSecure(data, OPENEDPATH + new_filename + '.md')
	
	# 处理 @road
	data = re.sub('@road: [^\n]*\n', '@road: ', data)
	# 把 pk 还原为 id
	temps = re.findall('\|`[a-z][a-z]`\|[a-zA-Z]*\|', data)
	for temp in temps:
		tuid = iddict.pkdict['pkidmap'][temp[2:4]]
		ntemp = '|`' + str(tuid) + '`|'
		data = data.replace(temp, ntemp)
	# 同步到 id.md
	writeSecure(data, MDFILEPATH + str(uid) + '.md')
	
	# 处理特殊的 0.md 文件，这里可以用来关闭文件
	if(uid == 0):
		beg_end = re.findall("【BEG】[\s\S]*\n【END】", data)[0]
		opened_filename = []
		opened_dirname = []
		for line in beg_end.split('\n'):
			if(re.match("\[\]\([\s\S]*\)", line)): # 文件
				opened_filename.append(line[3:-4])
			elif(re.match('`explorer "' + DIRPATH.replace('\\', '\\\\') + '[\s\S]*"`', line)): # 文件夹
				opened_dirname.append(line[len('`explorer "' + DIRPATH):-2])
		filenames = list(iddict.fndict.keys())
		for filename in filenames:
			if(filename not in opened_filename and iddict.fndict[filename] != 0):
				sv(iddict.fndict[filename])
				cl(iddict.fndict[filename])
		dirnames = list(iddict.dndict.keys())
		for dirname in dirnames:
			if(dirname not in opened_dirname):
				cldir(iddict.dndict[dirname])
# 关闭文件，建议调用前先用 sv 保存
def cl(uid):
	# 关闭文件
	filename = dictGetKey(iddict.fndict, uid)
	os.remove(OPENEDPATH + filename + '.md')
	# 修改 fndict
	del iddict.fndict[filename]
	# 删除 0.md 中的记录
	temp = '[](' + filename + '.md)'	
	del_in_0md(temp)
# 关闭文件夹
def cldir(uid):
	# 关闭文件夹
	dirname = dictGetKey(iddict.dndict, uid)
	os.rename(DIRPATH + dirname, DIRPATH + str(uid))
	# 修改 dndict
	del iddict.dndict[dirname]
	# 删除 0.md 中的记录
	temp = '`explorer "' + DIRPATH + dirname + '"`'
	del_in_0md(temp)

# 移动位置
def gt(uid, loadfile):
	old_filename = loadfile.split('\\')[-1].rsplit('.', 1)[0]

	# 检查 loadfile 是否是 mdfiles 中的文件
	assert os.path.relpath(loadfile).rsplit('\\', 1)[0] + '\\' == OPENEDPATH
	assert loadfile.split('\\')[-1].rsplit('.', 1)[1] == 'md'
	assert old_filename in iddict.fndict.keys()
	# 打开 new_file
	op(uid, loadfile)
	# 保存 loadfile, 并关闭
	tuid = iddict.fndict[old_filename]
	sv(tuid)
	cl(tuid)

# 执行命令
def exe_command(uid, ch):
	# commands 在 id.md 中以 "\ncommand @ch\n" 的形式存在
	with open(MDFILEPATH + str(uid) + '.md', 'r', encoding='utf-8') as f:
		temp = f.read()
		commandstr = re.findall("\n[^\n]+ @" + ch +'\n', temp)[0]
		commandstr = commandstr[1:-4]
	exec_cmd(commandstr)

# 初始化 source_data，回到什么都没有打开的状态
def reset():
	# 初始化 mdfiles（全部移到 backup）
	for filename in os.listdir(OPENEDPATH):
		filepath = os.path.join(OPENEDPATH, filename)
		removeSecure(filepath)
		print("del " + filename)
	# 初始化 mddirs（改名）
	for dirname in iddict.dndict.keys():
		if(os.path.exists(DIRPATH + dirname)):
			os.rename(DIRPATH + dirname, DIRPATH + str(iddict.dndict[dirname]))
		else:
			printErrorInfor("warning: can't rename " + DIRPATH + dirname + " to " + DIRPATH + str(iddict.dndict[dirname]) + ". "
				+ "Because" + DIRPATH + dirname + "isn't exists already", "blue")
		print("rename " + dirname)
	# 初始化 maps
	iddict.init_pk()
	iddict.fndict = {}
	iddict.dndict = {}
# 这会初始化所有文件，仅在调试时使用
def allreset():
	t = input("此操作将清楚包括用户数据的所有文件，确定吗？（需要输入“yes”）： ")
	if(t == "yes"):
		reset()
		# 清除 mddirs
		shutil.rmtree(DIRPATH)
		os.mkdir(DIRPATH)
		# 清除 mdfiles，初始化 0.md
		for filename in os.listdir(MDFILEPATH):
			filepath = os.path.join(MDFILEPATH, filename)
			os.remove(filepath)
			print("del " + filename)
		with open(MDFILEPATH + '0.md', 'w', encoding='utf-8') as f:
			f.write("管理中心\n\n\n\n")
			f.write("【BEG】\n【END】")
		# 更改 record.json 的 nextid = 0
		with open(RECORDPATH, 'r') as f:
			temp = json.load(f)
		temp['nextid'] = 1
		with open(RECORDPATH, 'w') as f:
			json.dump(temp, f, indent='\t')



if(__name__=='__main__'):
	# 清空 tasks.json
	exec_cmd('')

	# 得到 command
	if(WAYTOGETCOMMAND == 'text_from_file'):
		with open(args['file'], 'r', encoding='utf-8') as f:
			command = f.readlines()[args['lineNumber']-1]
		if(command[-1]=='\n'):
			command = command[:-1]
		if(command.count("`") == 2):
			command = re.findall("`[\s\S]*`", command)[0][1:-1]
	elif(WAYTOGETCOMMAND == 'commandline'):
		command = input()
	
	print(command)
	isfinish = True

	# 针对一些特殊情况
	if(re.match("\|\|[a-zA-Z]*\|", command)):
		sv(iddict.fndict[args['fileBasenameNoExtension']])
	else:
		isfinish = False
	
	if(isfinish):
		exit(0)
	else:
		isfinish = True

	# 解析 commands
	commandsplited = command.split(' ')
	if(commandsplited[0]=='open'): # 打开 md
		if(len(commandsplited)==1):
			op(0, args['file'])
		elif(len(commandsplited)==2):
			op(iddict.pkdict['pkidmap'][commandsplited[1]], args['file'])
		else:
			isfinish = False
	
	elif(commandsplited[0] == 'save'):
		if(len(commandsplited)==1):
			sv(iddict.fndict[args['fileBasenameNoExtension']])
		elif(len(commandsplited==2)):
			save(iddict.pkdict['pkidmap'][commandsplited[1]])
	
	elif(re.match('[a-z][a-z]$', commandsplited[0])):
		if(len(commandsplited) == 1): # 移到 md
			gt(iddict.pkdict['pkidmap'][commandsplited[0]], args['file'])
		elif(len(commandsplited) == 2): # 调用 pk 的 commandspliteds
			if(commandsplited[1] == 'D'): # 打开 pk 对应的文件夹
				opendir(iddict.pkdict['pkidmap'][commandsplited[0]])
			elif(re.match("[a-z]$", commandsplited[1])):
				exe_command(iddict.pkdict['pkidmap'][commandsplited[0]], commandsplited[1])
			else:
				isfinish = False
		else:
			isfinish = False

	elif(commandsplited[0] == 'reset' and len(commandsplited) == 1):
		reset()
	elif(commandsplited[0] == 'allreset' and len(commandsplited) == 1):
		allreset()
	
	else:
		isfinish = False
	
	if(isfinish):
		exit(0)
	else:
		isfinish = True

	# 执行终端命令
	exec_cmd(command)