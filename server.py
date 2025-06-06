from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

# internal imports
import dbConnection  # Import database setup
from user_controllers import auth, profile, cli  # Import auth routes
from provider_controllers import telemetry, vm_crud
from ui_cli_controllers import provider_get_requests, provider_post_requests, vms_get_request ,vms_post_request ,wg,provider_server
from middlewares.auth_middleware import ui_login_required
from prometheus_controller import prometheus_dump_data, prometheus_metrics
from ui_cli_controllers import hdfs

app = Flask(__name__)
CORS(app,supports_credentials=True)  # Enable CORS
bcrypt = Bcrypt(app)  # Initialize Bcrypt with app

load_dotenv()

dbConnection.setupConnection()

@app.route('/')
def home():
    """

    """
    return "Namaste, Welcome to the management server",200

# Prometheus metrics route
app.add_url_rule('/prometheus/query/<path:subpath>', 'metrics', prometheus_metrics.query_prometheus, methods=["GET"])
# app.add_url_rule('/prometheus/update_config', 'update_config', prometheus_conf_file_update.remove_prometheus_target, methods=["POST"]) #this was just for testing
app.add_url_rule('/prometheus/dumpData', 'dumpData', prometheus_dump_data.dump_data, methods=["GET"])



# provider server telemetry routes 
# app.add_url_rule('/heartbeat','provider-heartbeat',telemetry.heartbeat,methods=['POST'])


# vm telemetry
app.add_url_rule('/ui/<provider_id>/<path:subpath>', 'dynamic_proxy', telemetry.vm_telemetry, methods=['GET', 'POST', 'PUT', 'DELETE'])
# <path> (without subpath) captures only the first segzment after /vm/.
                                                        # UI Routes
# User Routes
app.add_url_rule('/register', 'register', auth.register, methods=['POST'])
app.add_url_rule('/login', 'login', auth.login, methods=['POST'])

# wg routes
app.add_url_rule('/cli/wg/connect','connect-wg',ui_login_required(wg.connect_wg),methods=['POST'])

                                        # CLI and UI common routes
# vms routes
app.add_url_rule('/vms/<path:subpath>','cli_vms',ui_login_required(vms_get_request.vmStatus),methods=['GET'])
app.add_url_rule('/vms/launch','cli_launch_vm',ui_login_required(vms_post_request.launchVm),methods=['POST'])

# provider routes
app.add_url_rule('/providers/<path:subpath>','cli_ui_providers',ui_login_required(provider_get_requests.providers),methods=['GET'])
app.add_url_rule('/providers/query','cli_ui_provider_query',ui_login_required(provider_post_requests.providers_query),methods=['POST'])
app.add_url_rule('/ui/providers/update_config','cli_ui_update_provider_config',ui_login_required(provider_post_requests.update_provider_conf),methods=['POST'])
app.add_url_rule('/ui/providers/providerClientDetails', 'providerClientDetails', ui_login_required(provider_get_requests.provider_client_details), methods=['GET'])
app.add_url_rule('/ui/providers/userProviderDetails', 'userProviderDetails', ui_login_required(provider_get_requests.get_user_provider_details), methods=['GET'])

# client/cli routes
app.add_url_rule('/ui/getAllCliSessionDetails', 'getAllCliDetails', ui_login_required(cli.get_all_cli_details), methods=['GET'])
app.add_url_rule('/ui/deleteCliSession', 'deleteCli', ui_login_required(cli.delete_cli_session), methods=['GET'])
app.add_url_rule('/ui/getCliVerificationToken', 'getCliVerificationToken', ui_login_required(cli.get_cli_verification_token), methods=['GET'])

# auth token verifications
app.add_url_rule('/cli/profile/verifyCliToken', 'verifyCliToken', cli.verify_cli_token, methods=['POST'])


app.add_url_rule('/providerServer/verifyProviderToken', 'verifyProviderToken',provider_server.verify_provider_token, methods=['POST'])
app.add_url_rule('/providerServer/getConfig', 'getConfig', provider_server.get_config, methods=['POST'])


# profile routes
app.add_url_rule('/ui/profile/getUserDetails', 'getUserDetails', ui_login_required(profile.get_user_details), methods=['GET'])
app.add_url_rule('/ui/profile/updateUserDetails', 'updateUserDetails', ui_login_required(profile.update_user_details), methods=['POST'])

# hdfs routes
app.add_url_rule('/hdfs/uploadFileFolder', 'upload_file_folder', ui_login_required(hdfs.upload_file_folder), methods=['POST'])
app.add_url_rule('/hdfs/list', 'list_file_folder', ui_login_required(hdfs.list_files_folders), methods=['GET'])
app.add_url_rule('/hdfs/mkdir', 'create_directory', ui_login_required(hdfs.make_directory), methods=['POST'])
app.add_url_rule('/hdfs/delete', 'delete_file_folder', ui_login_required(hdfs.delete), methods=['POST'])
app.add_url_rule('/hdfs/rename', 'rename_file_folder', ui_login_required(hdfs.rename_file_folder), methods=['POST'])

# vm operations (provider)
# app.add_url_rule('/ui/requestvm','requesting-vm-creation',vm_crud.vm_creation,methods=['POST'])
# app.add_url_rule('/vm/activate','activating-inactive-vm',ui_login_required(vm_crud.activate_vm),methods=['POST'])
# app.add_url_rule('/ui/vm/deactivate','deactivating-active-vm',vm_crud.deactivate_vm,methods=['POST'])
# app.add_url_rule('/ui/vm/delete','deleting-inactive-vm',vm_crud.delete_vm,methods=['POST'])

# getting port form env

if __name__ == '__main__':
    try:
        port = int(os.getenv("PORT") or 5000)
        print(f"Starting the server on port {port}...")
        app.run(debug=True, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error: {str(e)}")


# db- provider_id,timestarted,last_received_heartbeat

# first_time(provider_id is not in this table) , need to insesrt the provider_id and starting timestamp in the table. keep the same timestamp in last_received_heartbeat for the first time.
# If the provider_id is already in the table-
# Either update the last_received_heartbeat with the current timestamp if the difference between the current timestamp and last_received_heartbeat is less than 5 seconds.
# else if the time diff is more than 5 seconds then add one more entry to the table with as if entering for the first time.

# when the user wants all the active vms list- fetch all the associated provider_ids from the db and then for each provider_id fetch the enrolled vms by that user in that provider using the provider_id. And then fetch all the active_vms of that provider_id from the db and then match the already fetched vms list with the active_vms list. If the vm is not in the active_vms list then that vm is inactive or might associated with some other user.
# when the user wants all the inactive and active vms list- fetch all the associated provider_ids from the db and then for each provider_id fetch the enrolled vms by that user in that provider using the provider_id. And then fetch all the active_vms of that provider_id from the db and then match the already fetched vms list with the active_vms list. If the vm is not in the active_vms list then that vm is inactive or might associated with some other user. And then return the list of active and inactive vms.