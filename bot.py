import config
import praw
import json
import time
import datetime

from hoc import calculate_hoc

sizes = [100,250,500,1000]
default_size = 250


def bot_login():
	print("Logging In...")
	login = praw.Reddit(username = config.username,
				password = config.password,
				client_id = config.client_id,
				client_secret = config.client_secret,
				user_agent = config.user_agent)
	print("Logged in!")
	return login

reddit = bot_login()

def get_hoc_by_size(data, size):
	with open('header.txt') as h:
		header = h.readlines()
		add = len(header)

	data_size_list = data[:size+add]
	data_size = "".join(data_size_list)

	return data_size

def update_wiki(data, wiki_name):
	wiki_page = reddit.subreddit('SomeCountingStuff').wiki[wiki_name]
	wiki_page.edit(data, "Updated to: %s" % datetime.date.today())

	print("Updated %s" % wiki_name)

def run_bot():
	
	calculate_hoc()
	print("Calculated HoC!")

	# Get the hoc data
	with open('hoc.txt') as hoc:
		data = hoc.readlines()

	# Update the full list
	full_list = "".join(data)
	#update_wiki(full_list, 'rc_hoc')

	# Loop through each sized wiki and update it
	for size in sizes:
		wiki_name = "rc_hoc_%s" % size
		hoc = get_hoc_by_size(data, size)
		update_wiki(hoc, wiki_name)

	# Update the /r/counting wiki
	default_hoc = get_hoc_by_size(data, default_size)
	wiki_page = reddit.subreddit('counting').wiki['hoc']
	wiki_page.edit(default_hoc, "Updated to: %s" % datetime.date.today())
	print("Updated /r/counting hoc")

run_bot()