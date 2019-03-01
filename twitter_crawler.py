import pymysql
import networkx as nx
import time
import os
import tweepy

def utfcon():
	conn = pymysql.connect(host='localhost', user='root', password='pass', db='nodes2', charset='utf8')
	cursor = conn.cursor()
	return conn, cursor
def authenticate():
	cons_key = ''
	cons_sec = ''
	access_token = ''
	access_secret = ''

	auth = tweepy.OAuthHandler(cons_key, cons_sec)
	auth.set_access_token(access_token, access_secret)
	api = tweepy.API(auth)
	api.wait_on_rate_limit = True

	return api

class network_graph():
	def __init__(self,edges, nodes, base_user):
		self.degree = 1
		self.base = base_user
		self.G = nx.Graph()
		self.G.add_nodes_from(nodes)
		self.G.add_edges_from(edges)
	def filter(self, min_degree=1):
		# this function totally removes nodes from the graph if they are less than the min degree
		self.degree = min_degree + 1
		remove = [node for node, degree in self.G.degree() if degree <= min_degree]
		self.G.remove_nodes_from(remove)
	def export(self, base='graphdata'):
		# save the cleaned data to a file
		base += '.graphml'
		path = os.path.join(r'C:\Users\Brooks\Desktop', base)
		nx.write_graphml(self.G,path)
	def stats(self):
		# get statistics on the current state of the graph
		print('minimum degree to be on graph: %s\nnumber of nodes: %s\nnumber of edges: %s\n' % (self.degree, len(self.G.nodes), len(self.G.edges)))
		return ([len(self.G.nodes), len(self.G.edges)])
	def get_username(self, min_degree):
		# get username data from twitter and store in mysql
		api = authenticate()
		conn, cursor = utfcon()
		get_names = [node for node, degree in self.G.degree() if degree >= min_degree]

		length = len(get_names)
		print(length)

		cursor.execute('select user_id, screen_name from nodes')
		already_found = cursor.fetchall()
		if already_found:
			print(already_found)
			user_ids, screen_names = list(zip(*already_found))

		counter = 0
		for id in get_names:
			print(' ')
			counter += 1
			print(str(100* counter / length)[:6] + ' percent done done')
			print('getting id for ', id)
			if already_found:
				if id in user_ids:
					name = screen_names[user_ids.index(id)]
					self.G.node[id]['name'] = name
					continue
				else:
					pass

			# this block checks whether the user is a string which would mean its a screen name already
			no_letter = True
			for letter in str(id):
				if letter.isalpha() and no_letter:
					print(id, 'is already a screen name')
					name = id
					self.G.node[id]['name'] = name
					cursor.execute('insert into `nodes` (`user_id`, `screen_name`, `original_user`) VALUES (%s, %s, %s)',
								   (id, name, self.base))
					conn.commit()
					no_letter = False
			if no_letter == False:
				continue

			# this code runs if the id was not already stored or is not a screen name
			try:
				user = api.get_user(user_id=id)
				name = user.screen_name
			except Exception as e:
				if 'not found' in str(e):
					print(e)
					print('probably not found error, going to insert username as is,', id)
					name = id
			cursor.execute('insert into `nodes` (`user_id`, `screen_name`, `original_user`) VALUES (%s, %s, %s)', (id, name, self.base))
			self.G.node[id]['name'] = name
			conn.commit()


def main(user,node_min_for_username,statistics, filter_val):
	conn, cursor = utfcon()

	# gets the combined data
	cursor.execute('select user_id,user_follower_id from edges where original_user=%s', user)
	edges = cursor.fetchall()
	user_ids, follower_ids = list(zip(*edges))

	nodes = list(set(follower_ids + user_ids))

	print('number of users data collected: ', len(list(set(user_ids))))
	print()
	data = network_graph(edges, nodes, user)
	print('base stats before changes: ')
	k = data.stats()[0]

	if statistics:
		i = 0
		while k > 0:
			data.filter(i)
			k = data.stats()[0]
			i += 1
	else:
		print('filtering data with filter val of %s\nNew stats for graph' % filter_val)
		data.filter(filter_val)
		data.stats()
		data.get_username(node_min_for_username)
		data.export('%s_filter_%s_user_%s' % (user, filter_val, node_min_for_username))


if __name__ == '__main__':
	# username as it is in mysql
	user = 'UNLVGammaPhi'
	# the number of edges attached to a node to recieve a name on the graph
	node_min_for_username = 30
	# for testing the number of nodes on the graph
	# True: Print out cutoffs for each filter value
	# False: Export .graphml file
	statistics = False
	# minimum edges to have a node appear on the graph
	filter_val = 5

	node_min_for_username -= filter_val

	main(user,node_min_for_username,statistics, filter_val)
