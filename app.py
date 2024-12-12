from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

conan_profile_dir = os.path.expanduser("~/.conan/profiles/")

@app.route('/')
def index():
    profiles = [f for f in os.listdir(conan_profile_dir) if os.path.isfile(os.path.join(conan_profile_dir, f))]
    return render_template('index.html', profiles=profiles)

@app.route('/get-versions', methods=['GET'])
def get_versions():
    package_name = "vbs"  # 假设包名是固定的
    remote_name = "liconan-release-local"  # 假设远程名是固定的

    command = f"conan search {package_name} -r {remote_name}"
    try:
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        versions = parse_versions(result)
        return jsonify({"status": "success", "versions": versions})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "data": str(e)})

def parse_versions(result):
    lines = result.split('\n')
    versions = []
    for line in lines:
        if line.startswith("vbs/"):
            # 提取版本号部分
            version = line.split('/')[1].split('@')[0]
            versions.append(version)
    return versions

@app.route('/search', methods=['POST'])
def conan_search():
    profile_name = request.form['profile_name']
    package_name = request.form['package_name']
    version = request.form['version']
    user_name = request.form['user_name']
    channel_name = request.form['channel_name']
    remote_name = request.form['remote_name']

    profile_path = os.path.join(conan_profile_dir, profile_name)
    query_str = parse_profile_to_query(profile_path)

    command = f"conan search {package_name}/{version}@{user_name}/{channel_name} --query=\"{query_str}\" -r {remote_name}"
    print("Executing command:", command)
    
    command2 = f"conan search {package_name}/{version}@{user_name}/{channel_name} --query=\"{query_str}\" -r {remote_name} --revisions"
    print("Executing command:", command2)
    
    try:
        result = subprocess.check_output(command, shell=True, universal_newlines=True)
        print("result1:", result)
        result2 = subprocess.check_output(command2, shell=True, universal_newlines=True)
        print("result2:", result2)
        
        revision_id = parse_revision_id(result2)
        
        return jsonify({"status": "success", "data": result, "revision_id": revision_id, "command": command, "command2": command2})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "data": str(e), "command": command, "command2": command2})

def parse_revision_id(result):
    lines = result.split('\n')
    for line in lines:
        if '(' in line and ')' in line:
            revision_id = line.split('(')[0].strip()
            return revision_id
    return None

def parse_profile_to_query(profile_path):
    with open(profile_path, 'r') as file:
        lines = file.readlines()

    query_parts = []
    for line in lines:
        line = line.strip()
        if line.startswith("os=") or \
           line.startswith("compiler=") or \
           line.startswith("compiler.version=") or \
           line.startswith("compiler.libcxx=") or \
           line.startswith("compiler.vendor=") or \
           line.startswith("compiler.abi=") or \
           line.startswith("arch="): \
        #    line.startswith("build_type="):
            query_parts.append(line)

    return " AND ".join(query_parts)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=36535, debug=True)