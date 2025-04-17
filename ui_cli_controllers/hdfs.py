import requests
from flask import request, jsonify
from datetime import datetime as dateTime
import os
from dotenv import load_dotenv
from models.hdfsModel import hdfs_collection


def file_path_translation(original_path,username):
    """
    Translate the original path to the desired format.
    """
    # prepend the username to the path
    new_path = f"""{username}/{original_path}"""
    return new_path


def upload_file_folder(user):
    try:

        type = request.form.get("type")

        if not type:
            return jsonify({"error": "Missing type"}), 400
        if type not in ["file", "folder"]:
            return jsonify({"error": "Invalid type. Must be 'file' or 'folder'"}), 400

        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files.get('file')
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        path = request.form.get('path')
        

        user_id = user.get('user_id')
        username= user.get('username')   

        new_path = file_path_translation(path,username)
     

        load_dotenv()
        HDFS_SERVER = os.getenv("HDFS_SERVER")
        if not HDFS_SERVER:
            return jsonify({'error': 'HDFS_SERVER not configured in .env'}), 500

        # Send the file to the actual HDFS server
        files = {'file': (file.filename, file.stream, file.mimetype)}

        if type == "file":
            res = requests.post(f"{HDFS_SERVER}/upload", files=files, data={"path": new_path})
            if res.status_code != 200:
                return jsonify({"message": "File upload to HDFS failed","error":res.json().get("error")}), res.status_code
        
        elif type == "folder":
            res = requests.post(f"{HDFS_SERVER}/uploadFolder", files=files, data={"path": new_path})
            if res.status_code != 200:
                return jsonify({"error": "Folder creation in HDFS failed","error":res.json().get("error")}), res.status_code
            # No need to upload files for folders, just create the folder
            return jsonify({"message": "Folder created successfully"}), 200
        else:
            return jsonify({"error": "Invalid type. Must be 'file' or 'folder'"}), 400


        hdfs_details = {
            "name": file.filename,
            "path": new_path,
            "type": "FILE",
            "description": request.form.get("description", ""),
            "permission": request.form.get("permission", ""),
            "user_id": user_id,
            "size": len(file.read()),  # Size in bytes
            "createdAt": dateTime.now(),
            "lastModified": dateTime.now()
        }

        # Rewind file stream if needed again
        file.stream.seek(0)

        hdfs_collection.insert_one(hdfs_details)

        return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "File upload failed due to server error"}), 500


def list_files_folders(user):
    """
    List files and folders in a given path.
    """
    try:
        path=request.args.get("path")
        user_id = user.get("user_id")
        username = user.get("username")

        if user_id is None:
            return jsonify({"error": "Missing user_id"}), 400
        if path is None:
            return jsonify({"error": "Missing path"}), 400

        load_dotenv()
        HDFS_SERVER = os.getenv("HDFS_SERVER")

        new_path = file_path_translation(path, username)

        res = requests.post(f"{HDFS_SERVER}/list", json={"path": new_path})
        if res.status_code != 200:
            if res.status_code == 400:
                print("path",path)
                if path == "":
                    res = requests.post(f"{HDFS_SERVER}/mkdir", json={"path": username})
                    hdfs_details = {
                    "name": username,
                    "path": username,
                    "type": "DIRECTORY",
                    "description": "",
                    "permission": "",
                    "user_id": user_id,
                    "size": "-",
                    "createdAt": dateTime.now(),
                    "lastModified": dateTime.now()
                }
        
                hdfs_collection.insert_one(hdfs_details)
                return jsonify({"message":"Files and folders doesn't exists. Upload files or create folders.","contents":[]}), 200
            
            return jsonify({"message": "Failed to list contents from HDFS","error":res.json()}), res.status_code
        contents = res.json().get("contents", [])
        # removing the first element i.e. usename which was prepended from file_path_translation
        for content in contents:
                newPath = "/".join(content["path"].split("/")[2:])
                content["path"] = newPath
        # print(contents)
        return jsonify({"message": "Contents listed successfully", "contents": contents}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to list contents"}), 500

def rename_file_folder(user):
    """
    Rename a file or folder in HDFS.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        old_path = data.get("old_path")
        new_name = data.get("new_name")
        user_id = user.get("user_id")
        username = user.get("username")
        if not old_path or not new_name or not user_id:
            return jsonify({"error": "Missing required parameters"}), 400
        load_dotenv()
        HDFS_SERVER = os.getenv("HDFS_SERVER")
        old_path = file_path_translation(old_path, username)
        new_path = "/".join(old_path.split("/")[:-1] + [new_name])

        print("old_path",old_path)
        print("new_path",new_path)

        res = requests.post(f"{HDFS_SERVER}/rename", json={"old_path": old_path, "new_path": new_path})
        if res.status_code != 200:
            print("res",res.json())
            return jsonify({"error": "Failed to rename file/folder in HDFS"}), res.status_code
        # Update the database with the new name
        hdfs_collection.update_one(
            {"path": old_path, "user_id": user_id},
            {"$set": {"path": new_path, "name": new_name}},
            upsert=False
        )
        return jsonify({"message": "File/Folder renamed successfully", "new_path": new_path}), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to rename file/folder"}), 500
    
def make_directory(user):
    try:
        data = request.get_json()
        path = data.get("path")
        user_id = user.get("user_id")
        username = user.get("username")

        if not path or not user_id:
            return jsonify({"error": "Missing path or user_id"}), 400

        load_dotenv()
        HDFS_SERVER = os.getenv("HDFS_SERVER")

        new_path = file_path_translation(path, username)
        res = requests.post(f"{HDFS_SERVER}/mkdir", json={"path": new_path})

        if res.status_code != 200:
            return jsonify({"message":"Failed to create Folder/Directory","error": res.json()}), 500


        dir_name = new_path.split("/")[-1]

        hdfs_details = {
            "name": dir_name,
            "path": new_path,
            "type": "DIRECTORY",
            "description": data.get("description"),
            "permission": data.get("permission"),
            "user_id": user_id,
            "size": "-",
            "createdAt": dateTime.now(),
            "lastModified": dateTime.now()
        }

        hdfs_collection.insert_one(hdfs_details)
        return jsonify(res.json()), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to create directory"}), 500


def delete(user):
    try:
        data = request.get_json()
        paths_array = data.get("paths")
        user_id = user.get("user_id")
        username = user.get("username")

        if not paths_array or not user_id:
            return jsonify({"error": "Missing paths or user_id"}), 400

        load_dotenv()
        HDFS_SERVER = os.getenv("HDFS_SERVER")

        results = []
        for path in paths_array:
            new_path = file_path_translation(path, username)
            print(paths_array)
            res = requests.post(f"{HDFS_SERVER}/delete", json={"path": new_path})

            if res.status_code != 200:
                try:
                    error_response = res.json()
                except ValueError:
                    error_response = {"error": "Non-JSON response from HDFS"}
                return jsonify({
                    "message": "Failed to delete one of the paths",
                    "error": error_response,
                    "failed_path": path
                }), res.status_code

            # # Mark the item as deleted in DB
            # hdfs_collection.update_one(
            #     {"path": path, "user_id": user_id},
            #     {"$set": {"is_deleted": True}},
            #     upsert=False
            # )

            results.append({"path": path, "status": "deleted"})

        return jsonify({"message": "All files and folders deleted successfully", "results": results}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to delete path(s)"}), 500
