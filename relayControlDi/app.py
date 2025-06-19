from flask import Flask, render_template, jsonify, request
import minimalmodbus
import time
from readerwriterlock import rwlock

app = Flask(__name__)

# Modbus RTU configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to your serial port (COM3 for Windows)
BAUD_RATE = 9600
MODBUS_ADDRESS = 1

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
	
	try:
		# Read coils 0-7 (relay states)
		with rwlock.gen_rlock():
			states = device.read_bits(registeraddress=0, number_of_bits=8, functioncode=1)
			print(states)        
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
			
			return jsonify({'success': True, 'error': None})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/get_digitalInput_state')
def get_digitalInput_state():
	if not device:
		return jsonify({'error': 'Modbus connection not established'}), 500
	try:
		with rwlock.gen_rlock():
			states = device.read_bits(registeraddress=0, number_of_bits=8, functioncode=2)
			print(states)
			# states = device.read_coils(0, 8)
			return jsonify({
				'states': [bool(state) for state in states],
				'error': None
			})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

	
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)
