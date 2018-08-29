# -*- coding: utf-8 -*-
# Creating a Cryptocurrency
"""
Created on Mon Aug 6, 2018
@author: chase
"""
# Importing libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
# Part 1 - Building a Blockchain
class Blockchain:
	
	# create blockchain list and genisis block with previous hash set to 0
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
	# create block by taking in 4 keys and appending to chain and show data
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 	'timestamp': str(datetime.datetime.now()),
                 	'proof': proof,
                 	'previous_hash': previous_hash,
                  'transactions': self.transactions}          
        self.transactions = []
        self.chain.append(block)
        return block
	# get index of previous block
    def get_previous_block(self):
        	return self.chain[-1]
	
	# set up mining problem by making new proof(nonce) and creating equation with previous proof
	# need to add .encode() for sha256
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]== '0000':
                	check_proof = True
            else:
                	new_proof += 1
        return new_proof
    	
	# create hash of block using all information in block in JSON format
    def hash(self, block):
        	encoded_block = json.dumps(block, sort_keys = True).encode()
        	return hashlib.sha256(encoded_block).hexdigest()
        	
	# check that chain is valid by itterating through each block on the chain
	# checking a) the previous hash in the block is actually the previous hash
	# and b) the proof has the correct # of leading 0s
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                	return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                	return False
            previous_block = block
            block_index += 1
        return True
     #create transaction format and append to list of transaction
    def add_transaction(self, sender, receiver, amount):
         self.transactions.append({'sender': sender, 
                                   'receiver': receiver, 
                                   'amount': amount})
         previous_block = self.get_previous_block()
         return previous_block('index') + 1
    	
    def add_node(self, address):
         parsed_url = urlparse(address)
         self.nodes.add(parsed_url.netloc)
         
    def replace_chain(self):
         network = self.nodes
         longest_chain = None
         max_length = len(self.chain)
         for nodes in network:
             response = requests.get(f'http://{nodes}/get_chain')
             if response.status_code == 200:
                 length = response.json()['length']
                 chain = response.json()['chain']
                 if length > max_length and self.is_chain_valid(chain):
                     max_length = length
                     longest_chain = chain
         if longest_chain:
             self.chain = longest_chain
             return True
         return False
                
    	
# Part 2 - Mining our Blockchain
# Creating a Web App (Flask based)
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','')

# Creating a Blockchain (object)
blockchain = Blockchain()
# mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction( sender = node_address, receiver = 'Peter', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulaions, you just mined a block!',
            	'index': block['index'],
            	'timestamp': block['timestamp'],
            	'proof': block['proof'],
            	'previous_hash': block['previous_hash'],
              'transactions': block['transactions']}
    return jsonify(response), 200
# get the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
	response = {'chain': blockchain.chain,
            	'length': len(blockchain.chain)}
	return jsonify(response), 200
# check Blockchain validity
@app.route('/is_valid', methods=['GET'])
def is_valid():
	response = {'valid': str(blockchain.is_chain_valid(blockchain.chain))
        	}
	return jsonify(response), 200
#Adding a new transaction
@app.route('/add_transaction', methods=['POST'])
def add_transaction():    
    json = request.get_json
    transaction_keys = ('sender', 'receiver', 'amount')
    if not all (keys in json for keys in transaction_keys):
        return 'One or more elements in the transaction are missing', 400
    index = blockchain.add_transactions(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to block {index}.'}
    return json[response], 201

# Part 3 - Decentralizing the Blockchain

#Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "no node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are connected. Now the Smallcoin blockchain now contains the following nodes.',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

#Updating chains with the longest chain when necessary
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest chain.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the longest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200
# running the app
app.run(host='0.0.0.0', port = 5002)