from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt

# internal imports
import dbConnection  # Import database setup
from user_controllers import auth  # Import auth routes
from provider_controllers import telemetry, vm_crud
from ui_cli_controllers import provider_get_requests, vms_get_request ,vms_post_request ,wg
from middlewares.auth_middleware import ui_login_required

app = Flask(__name__)
CORS(app,supports_credentials=True)  # Enable CORS
bcrypt = Bcrypt(app)  # Initialize Bcrypt with app


dbConnection.setupConnection()

@app.route('/')
def home():
    return "Hello, Welcome to the management server",200

# provider server telemetry routes 
app.add_url_rule('/heartbeat','provider-heartbeat',telemetry.heartbeat,methods=['POST'])

                                                        # UI Routes
# User Routes
app.add_url_rule('/register', 'register', auth.register, methods=['POST'])
app.add_url_rule('/login', 'login', auth.login, methods=['POST'])

# auth token verification
app.add_url_rule('/ui/getCliVerificationToken', 'getCliVerificationToken', ui_login_required(auth.get_cli_verification_token), methods=['GET'])



# vm operations (provider)
app.add_url_rule('/ui/requestvm','requesting-vm-creation',vm_crud.vm_creation,methods=['POST'])
# app.add_url_rule('/vm/activate','activating-inactive-vm',ui_login_required(vm_crud.activate_vm),methods=['POST'])
app.add_url_rule('/ui/vm/deactivate','deactivating-active-vm',vm_crud.deactivate_vm,methods=['POST'])
# app.add_url_rule('ui/vm/delete','deleting-inactive-vm',vm_crud.delete_vm,methods=['POST'])


# vm telemetry
app.add_url_rule('/ui/<provider_id>/<path:subpath>', 'dynamic_proxy', telemetry.vm_telemetry, methods=['GET', 'POST', 'PUT', 'DELETE'])
# <path> (without subpath) captures only the first segzment after /vm/.

# wg routes
app.add_url_rule('/ui/wg/connect','connect-wg',wg.connect_wg,methods=['POST'])


                                                        # CLI routes
app.add_url_rule('/vms/<path:subpath>','cli_vms',ui_login_required(vms_get_request.vmStatus),methods=['GET'])
app.add_url_rule('/vms/launch','cli_launch_vm',vms_post_request.launchVm,methods=['POST'])
app.add_url_rule('/providers/<path:subpath>','cli_providers',provider_get_requests.providers,methods=['GET'])

# auth token verification
app.add_url_rule('/cli/verifyCliToken', 'verifyCliToken', auth.verify_cli_token, methods=['POST'])

if __name__ == '__main__':
    try:
        app.run(debug=True,port=5000)
    except Exception as e:
        print(f"Error: {str(e)}")


# db- provider_id,timestarted,last_received_heartbeat

# first_time(provider_id is not in this table) , need to insesrt the provider_id and starting timestamp in the table. keep the same timestamp in last_received_heartbeat for the first time.
# If the provider_id is already in the table-
# Either update the last_received_heartbeat with the current timestamp if the difference between the current timestamp and last_received_heartbeat is less than 5 seconds.
# else if the time diff is more than 5 seconds then add one more entry to the table with as if entering for the first time.

# when the user wants all the active vms list- fetch all the associated provider_ids from the db and then for each provider_id fetch the enrolled vms by that user in that provider using the provider_id. And then fetch all the active_vms of that provider_id from the db and then match the already fetched vms list with the active_vms list. If the vm is not in the active_vms list then that vm is inactive or might associated with some other user.
# when the user wants all the inactive and active vms list- fetch all the associated provider_ids from the db and then for each provider_id fetch the enrolled vms by that user in that provider using the provider_id. And then fetch all the active_vms of that provider_id from the db and then match the already fetched vms list with the active_vms list. If the vm is not in the active_vms list then that vm is inactive or might associated with some other user. And then return the list of active and inactive vms.