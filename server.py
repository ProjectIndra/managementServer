from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt

# internal imports
import dbConnection  # Import database setup
from user_controllers import auth  # Import auth routes
from provider_controllers import telemetry, vm_crud

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)  # Initialize Bcrypt with app

dbConnection.setupConnection()

@app.route('/')
def home():
    return "Hello, Welcome to the management server"

# User Routes
app.add_url_rule('/register', 'register', auth.register, methods=['POST'])
app.add_url_rule('/login', 'login', auth.login, methods=['POST'])

# vm operations
app.add_url_rule('/requestvm','requesting-vm-creation',vm_crud.vm_creation,methods=['POST'])
app.add_url_rule('/vm/activate','activating-inactive-vm',vm_crud.activate_vm,methods=['POST'])
app.add_url_rule('/vm/deactivate','deactivating-active-vm',vm_crud.deactivate_vm,methods=['POST'])
# app.add_url_rule('/vm/delete','deleting-inactive-vm',vm_crud.delete_vm,methods=['POST'])

# provider server telemetry routes
app.add_url_rule('/heartbeat','provider-heartbeat',telemetry.heartbeat,methods=['POST'])
app.add_url_rule('/<provider_id>/<path:subpath>', 'dynamic_proxy', telemetry.vm_telemetry, methods=['GET', 'POST', 'PUT', 'DELETE'])
# <path> (without subpath) captures only the first segment after /vm/.



if __name__ == '__main__':
    app.run(debug=True,threaded=True)
