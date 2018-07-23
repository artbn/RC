import praw
import re
import sqlite3
from datetime import datetime
import argparse

# Counting subreddit
SUBREDDIT = 'counting'

# List of thread names, you can add or remove threads to track
THREAD_NAME = 'main'
# Base regex for base 10 threads
BASE_REGEX = r'^\W*(\d+(\W*\d+)*|\d+)'

class Thread(object):
	
	def __init__(self,
		name='NoName',
		search=False, tid=False, exception=[], ignoreDupes=False,
		base=10, group=0, flags=0, regex=BASE_REGEX, parse=False):
		
		self.name = name
		
		self.search = search
		self.tid = tid
		self.exception = exception
		self.ignoreDupes = ignoreDupes
		
		self.base = base
		self.group = group
		self.flags = flags
		self.regex = re.compile(regex, flags=flags)
		
		self.threads = []
		
		if parse and callable(parse):
			self.parse = parse
		
		cur.execute('CREATE TABLE IF NOT EXISTS `{}`(id TEXT, value TEXT, parsed TEXT, author TEXT, time DATETIME, tid TEXT)'.format(name))
	
	def match(self, text):
		return self.regex.match(text)
	
	def parse(self, matches):
		return int(re.sub(r'\W', '', matches.group(self.group)), self.base)
	
	def search_thread(self, r):
		threads = []
		if self.tid:
			if type(self.tid) == list:
				for id in self.tid:
					threads.append(r.submission(id=id))
			else:
				threads.append(r.submission(id=self.tid))
		else:
			for search in r.subreddit(SUBREDDIT).search(self.search, sort='new'):
				tid = search.id
				if tid in self.exception:
					continue
					
				threads.append(search)
			
		return threads

# Thread options
THREAD_OPTIONS = {
	'main': {
		'search': 'title:Counting Thread',
		'tid': ['3xiune']
	},
	'alphanumeric': {
		'search': 'title:Alphanumerics',
		'regex': '^\W*([0-9A-Z]+)',
		'tid': ['3je4es']
	},
	'sheep':{
		'search':'title:Sheep',
		'tid': ['3fzm7p']
	},
	'letters': {
		'search':'title:letters',
		'regex': '^\W*([A-Z]+)'
	},
	'updown': {
		'search':'((title:up down) OR (title:increment decrement) OR (title:tug of war)) NOT (title:2D)',
		'regex': r'^[^-\W]*((-\W*)?(\d+([^-\w]*\d+)*|\d+))',
		'tid': ['3tiryi'],
		'ignoreDupes': True
	},
	'palindrome': {
		'search':'title:palindrome NOT (title:hexadecimal OR title:hex OR title:binary)',
		'exception': ['3x5bcr']
	},
	'hexadecimal': {
		'search':'(title:hexadecimal OR title:hex) NOT title:palindrome',
		'regex': r'^\W*(?:0[xX])?([0-9a-fA-F]+)',
		'tid': ['3w00h0'],
		'base': 16
	},
	'palindrome-hex': {
		'search':'title:hexadecimal palindrome OR title:hex palindrome',
		'regex': r'^\W*(?:0[xX])?([0-9a-fA-F]+)',
		'base': 16
	},
	'time': {
		'search':'title:time counting thread',
		'regex': r'^\W*(\d{1,2})\W*(\d{1,2})\W*(\d{1,2})\W*(AM|PM)?',
		'parse': lambda matches: int(matches.group(1)) * 3600 + int(matches.group(2)) * 60 + int(matches.group(3))
	},
	'binary': {
		'search': 'title:binary NOT (title:palindrome OR title:alphabet OR title:prime OR title:collatz)',
		'regex': r'^\W*([01,\.\s]+)',
		'base': 2
	},
	'ternary': {
		'search': 'title:ternary counting thread',
		'regex': r'^\W*([012,\.\s]+)',
		'tid': ['3unkpu'],
		'base': 3
	},
	'roman': {
		'tid': '3smutv',
		'regex': '^[~`#*_\\s\\[>~]*([\u2182\u2181MDCLXVI\\W]+)'
	},
	'12345': {
		'search': 'title:12345',
		'regex': '^\W*((?:\D*1\D*2\D*3\D*4\D*5)(\D*=\W*(\d+(\W*\d+)*|\d+))?)',
		'exception': ['3vzjuy'],
		'parse': lambda matches: re.sub('\W', '', matches.group(3)) if matches.group(3).isdigit() else matches.group(0)
	},
	'fourfours': {
		'regex': '^\W*((?:\D*4){4}(\D*=\W*(\d+(\W*\d+)*|\d+))?)',
		'tid': ['3109vi'],
		'parse': lambda matches: re.sub('\W', '', matches.group(3)) if matches.group(3).isdigit() else matches.group(0)
	},
	'gr8b8m8': {
		'regex':'^\W*(gr\W*\d+\W*b\W*\d+\W*m\W*\d+)',
		'tid': '3mwb6g',
		'group': 1,
		'flags': re.I
	},
	'rational': {
		'regex': '^\W*((?:\d*\W*\/\W*\d*\W*)*)?(\d*)\W*\/\W*(\d*)',
		'search': 'title:rational',
		'parse': lambda matches: int(matches.group(2)) / int(matches.group(3))
	}
}

# Filter database
FILTER = ''

print('Opening SQL Database')
sql = sqlite3.connect('sql.db', detect_types=sqlite3.PARSE_DECLTYPES)

sql.create_function('contains_69', 1, lambda n: '69' in n)
sql.create_function('ends_69', 1, lambda n: n[-2:] == '69')
sql.create_function('palindrome', 1, lambda n: n[::-1] == n)

cur = sql.cursor()

def setup_thread(name):
	global thread
	if name in THREAD_OPTIONS:
		thread = Thread(name, **THREAD_OPTIONS[name])
	else:
		print('Option for', name, 'does not exist.')

def setup_reddit():
	# Good to go
	import login
	r = praw.Reddit(client_id=login.client_id,
                     client_secret=login.secret,
                     password=login.PASSWORD,
                     user_agent=login.USERAGENT,
                     username=login.USERNAME)
	return r

def replybot():
	""" Bot """
	reddit = setup_reddit()
	posts = thread.search_thread(reddit)
	
	for post in posts:
		valid = skipped = deleted = duplicates = bad = 0
		authorsByValues = {}
		
		print(post)

		comments = post.comments
		for comment in comments:
			
			if isinstance(comment, praw.objects.MoreComments):
				comments.extend(comment.comments())
				continue
			
			comments.extend(comment.replies)
			
			pid = comment.id
			pbody = comment.body
			pdate = int(comment.created_utc)

			try:
				pauthor = comment.author.name
			except AttributeError:
				# Author is deleted. We don't care about this post.
				deleted += 1
				continue
			
			cur.execute('SELECT 1 FROM `{}` WHERE ID=?'.format(thread.name), [pid])
			if cur.fetchone():
				# Post is already in the database
				continue
			
			matches = thread.match(pbody)
				
			if not matches:
				skipped += 1
				print('Skipped:', pbody.encode('utf8'))
				continue
			#value = pbody
			
			try:
				value = thread.parse(matches)
			except ValueError as e:
				bad += 1
				print(e)
				continue
			
			if not thread.ignoreDupes:
				cur.execute('SELECT 1 FROM `{}` WHERE parsed=?'.format(thread.name), [value])
				if (value in authorsByValues) or cur.fetchone():
					duplicates += 1
					continue
			
			valid += 1
			authorsByValues[value] = {
				'tid': post.id,
				'pid': pid,
				'body': pbody,
				'value': value,
				'author': pauthor,
				'created': datetime.fromtimestamp(pdate),
			}
		
		print('Comment proccessed:', len(comments))
		print('Valid comments:', valid)
		print('Bad comments:', bad)
		print('Duplicated comments:', duplicates)
		print('Deleted comments:', deleted)
	
		print('Saving....')
		for key, value in authorsByValues.items():
			cur.execute('INSERT INTO `{}` VALUES(:pid,:body,:value,:author,:created,:tid)'.format(thread.name), value)
		
		sql.commit()

def gold():
	""" Crawl gold comments """
	r = setup_reddit()
	subreddit = r.subreddit(SUBREDDIT)
	gilded = subreddit.comments(limit=None, gilded_only=True)
	
	cur.execute('CREATE TABLE IF NOT EXISTS gold(id TEXT, body TEXT, author TEXT, time DATETIME, tid TEXT)')
	for comment in gilded:
		id = comment.id
		cur.execute('SELECT 1 FROM gold WHERE ID=?', [id])
		if cur.fetchone():
			continue
		
		try:
			author = comment.author.name
			body = comment.body.strip()
		except AttributeError:
			author = '[deleted]'
			body = '[deleted]'
		
		try:
			tid = comment.submission.id
		except AttributeError:
			continue
		
		time = int(comment.created_utc)
		
		cur.execute('INSERT INTO gold VALUES(:id,:body,:author,:time,:tid)',
		{
			'author': author,
			'body': body,
			'id': id,
			'tid': tid,
			'time': datetime.fromtimestamp(time)
		})
		
		print(id)
	
	sql.commit()

def contrib_gold():
	""" Dump gilded comments statistics """
	from collections import Counter
	
	cur.execute('SELECT author FROM gold')
	table = cur.fetchall()
	
	if not table:
		print('Table gold is empty.')
		exit()
	
	with open('stats_gilded.txt', 'w') as file:
		file.write('Rank|Username|gold\n'
				'---|---|---\n')
		
		counts = Counter()
		for row in table:
			author = row[0]
			counts[author] += 1

		print(counts)
		
		n = 1
		for row in counts.most_common():
			name = row[0]
			value = row[1]
			
			file.write('|'.join([str(n), name, str(value)]) + '\n')
			n += 1
		
		file.write('\nDate completed: {} UTC'.format(datetime.utcnow()))
		
		print('Stats file written.')

def contrib():
	""" Dump thread's contribution """
	from collections import Counter, defaultdict
	
	query = ('SELECT t1.parsed, t1.author,'
			' round(86400*(julianday(t1.time)-julianday(t2.time))) AS diff'
			' FROM `{0}` t1, `{0}` t2'
			' WHERE t2.parsed = t1.parsed - 1'
			' AND diff > 0').format(thread.name)
		
	if FILTER:
		query += ' AND ' + FILTER + '(t1.value)'
		
	cur.execute(query)
	print('Contributions in', thread.name)
		
	table = cur.fetchall()
	counts = Counter()
	seconds = defaultdict(Counter)

	if not table:
		print('Table', thread.name, 'is empty.')
		return
	
	for row in table:
		author = row[1]
		counts[author] += 1
		
		s = int(row[2])
		if s == 3:
			# Filter <2000 users
			cur.execute(('SELECT 1 FROM `stats_{}` WHERE counts > 2000 AND author=?').format(thread.name), [author])
			result = cur.fetchone()
				
			if result:
				continue

		if s < 3:
			seconds[author][s] += 1

	n = 1
	print('Rank|Username|Counts\n'
		'---|---|---')
	for count in counts.most_common():
		name = count[0]
		value = count[1]
		
		if name in seconds:
			name += ' (' + ','.join([('{0} {1}s').format(v, k) for k, v in seconds[name].items()]) + ')'
			
		print(n, '|', name, '|', value)
		n += 1
	
def dump():
	""" Dump thread """
	query = 'SELECT * FROM `{0}`'.format(thread.name)
		
	if FILTER:
		query += (' WHERE {}(value)'.format(FILTER))
	
	cur.execute(query)
	
	filename = thread.name + '.txt'
	table = cur.fetchall()
		
	with open(filename, 'w', encoding='utf-8') as file:
		for row in table:
			file.write(str(row) + '\n')
	
	print('File', filename, 'written')

def clean():
	""" Delete database files """
	if input('Are you really sure to clean database?').lower() != 'y':
		return
	
	if FILTER:
		cur.execute('DELETE FROM `{0}` WHERE {1}(value)'.format(thread.name, FILTER))
	else:
		cur.execute('DELETE FROM `{}`'.format(thread.name))
	sql.commit()
	print('Deleted all comments in', thread.name)

def stats():
	""" Writes statistics to a file """
	cur.execute('SELECT * FROM `stats_{}` ORDER BY counts DESC'.format(thread.name))
		
	table = cur.fetchall()
		
	with open('stats_{}.txt'.format(thread.name), 'w') as file:
		file.write('Rank|Username|Counts\n'
			'---|---|---\n')
			
		n = 1
		for row in table:
			file.write(' | '.join([str(n), row[0], str(row[1])]) + '\n')
			n += 1
			
		file.write('\nDate completed: {} UTC'.format(datetime.utcnow()))
		
	print('Stats file written.')

def update_stats():
	""" Updates stat database for thread """
	cur.execute('CREATE TABLE IF NOT EXISTS `stats_{}`(author TEXT, counts INT)'.format(thread.name))
	
	if FILTER:
		cur.execute('SELECT author FROM `{0}` WHERE {1}(parsed)'.format(thread.name, FILTER))
	else:
		cur.execute('SELECT author FROM `{}`'.format(thread.name))
	
	table = cur.fetchall()
	
	for row in table:
		author = row[0]

		cur.execute('SELECT counts FROM `stats_{}` WHERE author=?'.format(thread.name), [author])
		result = cur.fetchone()

		if result:
			counts = result[0]
		else:
			cur.execute('INSERT INTO `stats_{}` VALUES(?, 0)'.format(thread.name), [author])
			counts = 0
		
		cur.execute('UPDATE `stats_{}` SET counts=? WHERE author=?'.format(thread.name), [counts + 1, author])
	
	sql.commit()

def convert_asa(file):
	""" Converts from anothershittyalt's format to my format """
	import csv
	
	deleted = 0
	
	with open(file, 'r') as csvfile:
		reader = csv.reader(csvfile)
		
		next(reader, None) # skip the headers
		for row in reader:
			value = row[0]
			parsed = int(row[1])
			author = row[2]
			time = datetime.fromtimestamp(int(row[3]))
			pid = row[4]
			tid = row[5]
			
			if author == '[deleted]':
				deleted += 1
			
			cur.execute('INSERT INTO `{}` VALUES(?,?,?,?,?,?)'.format(thread.name), [pid, value, parsed, author, time, tid])
		
		sql.commit()
	
	print('Converted successfully.')
	print('Deleted comments:', deleted)

def main():
	parser = argparse.ArgumentParser(description='Process counting statistics.')
	
	parser.add_argument('-T', '--thread', help='select thread to crawl', action='store')
	parser.add_argument('-F', '--filter', help='set filter threads in database', action='store')
	parser.add_argument('-L', '--limit', help='limit 1000 counts starting from n.', action='store', type=int)
	parser.add_argument('-G', '--gold', help='crawl all gilded comments', action='store_true')
	
	parser.add_argument('-Cl', '--clean', help='clean threads in database.', action='store_true')
	parser.add_argument('-D', '--dump', help='dump all threads in database', action='store_true')
	
	parser.add_argument('-C', '--contrib', help='print contributions for threads in database.', action='store_true')
	parser.add_argument('-S', '--stats', help='display stats in database', action='store_true')
	parser.add_argument('-Su', '--stats-update', help='update stats in database', action='store_true')
	
	parser.add_argument('-Ca', '--convert-asa', help="converts anothershittyalt's format to SQL format", action='store')
	
	args = parser.parse_args()
	
	if args.thread:
		global THREAD_NAME
		THREAD_NAME = args.thread
	
	setup_thread(THREAD_NAME)
	
	global FILTER
	if args.filter:
		FILTER = args.filter
	
	if args.limit:
		start = args.limit
		final = args.limit + 1000
		
		# terrible hack i know
		FILTER = 'L'
		sql.create_function('L', 1, lambda n: start < int(n) < final)
	
	if args.clean:
		clean()
	elif args.dump:
		dump()
	
	elif (args.contrib or args.stats) and (args.gold or THREAD_NAME == 'gold'):
		contrib_gold()
	elif args.gold or THREAD_NAME == 'gold':
		gold()
	
	elif args.contrib:
		contrib()
	elif args.stats:
		stats()
	elif args.stats_update:
		update_stats()

	elif args.convert_asa:
		convert_asa(args.convert_asa)
	
	else:
		replybot()

if __name__ == '__main__':
	main()