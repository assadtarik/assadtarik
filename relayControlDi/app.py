from flask import Flask, render_template, jsonify, request
import minimalmodbus
import time
from readerwriterlock import rwlock

app = Flask(__name__)

# Modbus RTU configuration
SERIAL_PORT = 'COM3'  # Change to your serial port (COM3 for Windows)
BAUD_RATE = 9600
MODBUS_ADDRESS = 1

CACHE_DURATION = 1


cache = {
	"relay_states": None,
	"relay_timestamp": 0,
	"digitalinput_states": None,
	"digitalinput_timestamp": 0,
}



# Initialize Modbus device
try:
	device = minimalmodbus.Instrument(SERIAL_PORT, MODBUS_ADDRESS)
	device.serial.baudrate = BAUD_RATE
	device.serial.timeout = 0.5
	print("Connected to Modbus RTU device")
	rwlock = rwlock.RWLockWrite()
except Exception as e:
	print(f"Failed to connect to Modbus RTU device: {e}")
	device = None

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/get_relay_states')
def get_relay_states():
	if not device:
		return jsonify({'error': 'Modbus connection not established'}), 500

	now = time.time()
	with rwlock.gen_rlock():
		if cache["relay_states"] is not None and (now - cache["relay_timestamp"] < CACHE_DURATION):
			return jsonify({
				'states': [bool(state) for state in cache['relay_states']],
				'error': None
			})

	try:
		# Read coils 0-7 (relay states)
		with rwlock.gen_rlock():
			now = time.time()

			states = device.read_bits(registeraddress=0, number_of_bits=8, functioncode=1)
			
			cache['relay_states'] = states
			cache["relay_timestamp"] = now
			
			print("relay states", states)        
			return jsonify({
				'states': [bool(state) for state in states],
				'error': None
			})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/set_relay', methods=['POST'])
def set_relay():
	if not device:
		return jsonify({'error': 'Modbus connection not established'}), 500
	
	data = request.json
	relay = data.get('relay')
	state = data.get('state')
	
	if relay is None or state is None:
		return jsonify({'error': 'Missing relay or state parameter'}), 400

	try:       
		with rwlock.gen_wlock(): 
			device.write_bit(relay, int(state), functioncode=5)

			cache["relay_states"] = None
			cache['relay_timestamp'] = 0	
			
			return jsonify({'success': True, 'error': None})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/get_digitalInput_state')
def get_digitalInput_state():
	if not device:
		return jsonify({'error': 'Modbus connection not established'}), 500

	now = time.time()
	with rwlock.gen_rlock():
		if cache["digitalinput_states"] is not None and (now - cache["digitalinput_timestamp"] < CACHE_DURATION):
			return jsonify({
				'states': [bool(state) for state in cache['digitalinput_states']],
				'error': None
			})


	try:
		with rwlock.gen_rlock():
			now = time.time()

			# states = device.read_coils(0, 8)
			states = device.read_bits(registeraddress=0, number_of_bits=8, functioncode=2)

			cache['digitalinput_states'] = states
			cache['digitalinput_timestamp'] = now

			print("digitalinput states", states)
						
			return jsonify({
				'states': [bool(state) for state in states],
				'error': None
			})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

	
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=False)
