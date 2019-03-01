# Social_networks
Draw graphs of relationships between users based on recursive scraping of follower / following status.

## Usage

This package scrapes the twitter IDS of all a user's twitter followers. For each follower, all of their followers are then also gathered. All user information is stored in a MySQL database to be pulled from `graph_constructor.py`. 

## Graph construction

All data is pulled from tables using `pymysql` and relationships are matched using `networkx`. The clustering coefficient / degree of each user is calculated. If the a node is determined to be important enough, their username and screen name are pulled from twitter. All data is exported to a .graphml file to be rendered using a service such as SNAP or Gephi.

## Example Graph

![](https://i.imgur.com/FozgmCl.jpg)
