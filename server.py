from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt

# internal imports
import dbConnection  # Import database setup
from user_controllers import auth  # Import auth routes
from provider_controllers import telemetry, vm_crud
from cli_controllers import provider_get_requests, vms_get_request ,vms_post_request ,wg

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)  # Initialize Bcrypt with app

dbConnection.setupConnection()

@app.route('/')
def home():
    return "Hello, Welcome to the management server",200

# provider server telemetry routes 
app.add_url_rule('/heartbeat','provider-heartbeat',telemetry.heartbeat,methods=['POST'])

                                                        # UI Routes
# User Routes
app.add_url_rule('/ui/register', 'register', auth.register, methods=['POST'])
app.add_url_rule('/ui/login', 'login', auth.login, methods=['POST'])

# auth token verification
app.add_url_rule('/ui/getCliVerificationToken', 'getCliVerificationToken', auth.get_cli_verificationToken, methods=['GET'])



# vm operations (provider)
app.add_url_rule('/ui/requestvm','requesting-vm-creation',vm_crud.vm_creation,methods=['POST'])
app.add_url_rule('/ui/vm/activate','activating-inactive-vm',vm_crud.activate_vm,methods=['POST'])
app.add_url_rule('/ui/vm/deactivate','deactivating-active-vm',vm_crud.deactivate_vm,methods=['POST'])
# app.add_url_rule('ui/vm/delete','deleting-inactive-vm',vm_crud.delete_vm,methods=['POST'])


# vm telemetry
app.add_url_rule('/ui/<provider_id>/<path:subpath>', 'dynamic_proxy', telemetry.vm_telemetry, methods=['GET', 'POST', 'PUT', 'DELETE'])
# <path> (without subpath) captures only the first segzment after /vm/.

# wg routes
app.add_url_rule('/ui/wg/connect','connect-wg',wg.connect_wg,methods=['POST'])




                                                        # CLI routes
app.add_url_rule('/cli/vms/<path:subpath>','cli_vms',vms_get_request.vmStatus,methods=['GET'])
app.add_url_rule('/cli/vms/launch','cli_launch_vm',vms_post_request.launchVm,methods=['POST'])
app.add_url_rule('/cli/providers/<path:subpath>','cli_providers',provider_get_requests.providers,methods=['GET'])

# auth token verification
app.add_url_rule('/cli/verifyCliToken', 'verifyCliToken', auth.verify_cli_token, methods=['POST'])

if __name__ == '__main__':
    try:
        app.run(debug=True,port=5000)
    except Exception as e:
        print(f"Error: {str(e)}")