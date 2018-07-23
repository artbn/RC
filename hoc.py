import numpy as np
from math import ceil
from string import Template

def calculate_hoc():
	# Load CSV file containing all counts
	number, author, unix, cid, tid = np.loadtxt('r_counting_master_list.csv', dtype="S25", delimiter=",", unpack=True).astype(str)
	# Load banned or deleted users
	banned_or_deleted = np.loadtxt('banned_or_deleted.txt', dtype="S25").astype(str)
	# Load alts
	with open('alts.txt') as alts:
		alt_dic = {}
		for line in alts:
			line = line.split("\t")
			for i, name in enumerate(line):
				if i != 0:
					alt_dic[name.strip('\n')] = line[0]

	# Replace alts with main
	for i, name in enumerate(author):
		if name in alt_dic:
			author[i] = alt_dic[name]

	# Remove banned users from list
	mask = np.in1d(author, banned_or_deleted, invert=True)
	author = author[mask]

	# Create an unsorted HoC
	author, counts = np.unique(author, return_counts=True)

	# Sort HoC
	index = counts.argsort()
	sorted_author = author[index[::-1]]
	sorted_counts = counts[index[::-1]]

	# Calculate to which k HoC is accurate to
	accurate = ceil(len(number) / 1000)

	with open('header.txt') as template, open('current_header.txt', 'w') as out:
		src = Template(template.read())
		current_header = src.substitute({'k':accurate})
		out.write(current_header)

	# Create HoC File
	with open("hoc.txt", 'w') as hoc, open('current_header.txt') as ch:
		# Header
		header = ch.read()
		hoc.write(header)
		# Table
		for i in range(len(author)):
			hoc.write("%s|/u/%s|%s\n" % (i+1, sorted_author[i], sorted_counts[i]))

if __name__ == '__main__':
	calculate_hoc()