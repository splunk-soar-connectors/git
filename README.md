[comment]: # "Auto-generated SOAR connector documentation"
# Git

Publisher: Splunk  
Connector Version: 3.0.0  
Product Vendor: Generic  
Product Name: Git  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.0.2  

This app integrates with git and supports common git actions

[comment]: # " File: README.md"
[comment]: # "  Copyright (c) 2017-2024 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
This app supports connecting with both HTTP(S) and SSH. When connecting with HTTP(S) both the
username and password are required in case of private repository. For public repository, username
and password are not required, however, these won't be verified unless they are explicitly needed to
perform the action. If you were to connect to a public repo, for example, the username and password
would only be needed on a **git push** action. When connecting with SSH, the username should be part
of the URI ( **git** @gitrepo).  
The **repo_name** parameter will be the name given to the cloned repository.

  

As of this writing, the repository will be saved in the location
`     ${PHANTOM_HOME_DIR}/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/<repo_name>    `

## Connecting via SSH

This app supports connecting to git through SSH instead of HTTP. In order to make this easy to do,
there is a **configure ssh** action. Running this action will create an RSA key pair, and return the
public key. After that, you will need to manually add the public key to the git repo.

Though not recommended, it is also possible to add an existing private key for this app to read, as
well. Add the private key file to

    ${PHANTOM_HOME_DIR}/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/.ssh-<asset_id>/id_rsa

Then set it so that

    phantom-worker

is the owner, and set the file permissions to

    600

If you do connect with SSH, both the username and password parameters will be ignored.

## Playbook Backward Compatibility

-   The behavior of the clone repo and delete repo actions have been modified due to the change in
    the naming convention of repo.

      

    -   In previous version, repo was saved as **reponame** In the new version, repo will be saved
        as **\_**


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Git asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**repo_uri** |  optional  | string | Repo URI
**branch_name** |  optional  | string | Branch Name (Default: master)
**username** |  optional  | string | Username
**password** |  optional  | password | Password
**repo_name** |  optional  | string | Repo Name

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate credentials provided for connectivity  
[configure ssh](#action-configure-ssh) - Create an RSA Key pair for SSH connectivity  
[list repos](#action-list-repos) - List repos configured/pulled  
[update file](#action-update-file) - Update (overwrite) contents of a file in the working directory  
[git status](#action-git-status) - Get the result of git status  
[delete file](#action-delete-file) - Delete a file from the local working directory  
[add file](#action-add-file) - Create a file in the local working directory  
[git commit](#action-git-commit) - Commit changes  
[git push](#action-git-push) - Push commits to the remote server  
[git pull](#action-git-pull) - Pull the repo  
[delete repo](#action-delete-repo) - Delete a cloned repository  
[clone repo](#action-clone-repo) - Clone the repo  

## action: 'test connectivity'
Validate credentials provided for connectivity

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'configure ssh'
Create an RSA Key pair for SSH connectivity

Type: **generic**  
Read only: **False**

This action will generate a new RSA key pair to enable connecting via SSH. It will return the public key, which you should add to the repo that you wish to connect to.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**force_new** |  optional  | Force create a new key pair | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.force_new | boolean |  |   True  False 
action_result.data | string |  |  
action_result.summary.rsa_pub_key | string |  |   ssh-rsa <key> 
action_result.message | string |  |   Rsa pub key 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'list repos'
List repos configured/pulled

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.repo_dirs | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repos | string |  |   test_repo 
action_result.summary.total_repos | numeric |  |   2 
action_result.message | string |  |   Total repos: 2 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'update file'
Update (overwrite) contents of a file in the working directory

Type: **generic**  
Read only: **False**

This action will overwrite the contents of the existing file with the specified input in the local working directory.<br>If <b>vault_id</b> is specified the contents are overwritten from the file in the vault, else from the data in the <b>contents</b> parameter. The <b>contents</b> parameter can only contain textual data.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** |  required  | File path in repo to update | string |  `file path` 
**contents** |  optional  | Contents (text) of the file | string | 
**vault_id** |  optional  | Vault ID | string |  `vault id` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.contents | string |  |   Contents to write in the file 
action_result.parameter.file_path | string |  `file path`  |   b 
action_result.parameter.vault_id | string |  `vault id`  |   75881c96a30cd1f07d596059388368836b6b1b74 
action_result.data.\*.file_path | string |  `file path`  |   b 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   File file1 updated successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'git status'
Get the result of git status

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.staged.deleted | string |  `file path`  |   deleted_file 
action_result.data.\*.staged.modified | string |  `file path`  |   modified_file 
action_result.data.\*.staged.new_file | string |  `file path`  |   new_file 
action_result.data.\*.staged.renamed | string |  |   old_file -> new_file 
action_result.data.\*.str | string |  |   On branch master
Your branch is up-to-date with 'origin/master'.
nothing to commit, working directory clean 
action_result.data.\*.unstaged.modified | string |  `file path`  |   modified_file 
action_result.data.\*.untracked_files | string |  `file path`  |   untracked_file 
action_result.summary.status | string |  |   Your branch is up-to-date with 'origin/master'. 
action_result.message | string |  |   Status: Your branch is up-to-date with 'origin/master'. 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'delete file'
Delete a file from the local working directory

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** |  required  | File path in repo to delete | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.file_path | string |  `file path`  |   n1 
action_result.data.\*.file_path | string |  `file path`  |   n1 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   File file1 deleted successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'add file'
Create a file in the local working directory

Type: **generic**  
Read only: **False**

This action will create in the working directory a file with the specified input data.<br>If <b>vault_id</b> is specified the contents are picked from the file in the vault, else from the data in the <b>contents</b> parameter. The <b>contents</b> parameter can only contain textual data.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file_path** |  required  | File path in repo to add | string |  `file path` 
**contents** |  optional  | Contents (text) of the file | string | 
**vault_id** |  optional  | Vault ID | string |  `vault id` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.contents | string |  |   new content 
action_result.parameter.file_path | string |  `file path`  |   n1 
action_result.parameter.vault_id | string |  `vault id`  |   75881c96a30cd1f07d596059388368836b6b1b74 
action_result.data.\*.file_path | string |  `file path`  |   n1 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   File file1 added successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'git commit'
Commit changes

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**message** |  required  | Commit message (Default: committed from splunk soar) | string | 
**push** |  optional  | Push to remote after commit | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.message | string |  |   committed from phantom 
action_result.parameter.push | boolean |  |   True  False 
action_result.data.\*.branch_name | string |  |   master 
action_result.data.\*.commit_message | string |  |   committed from phantom 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   Commit to repo test_repo completed successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'git push'
Push commits to the remote server

Type: **generic**  
Read only: **False**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.branch_name | string |  |   master 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   Repo test_repo pushed successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'git pull'
Pull the repo

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.branch_name | string |  |   master 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.data.\*.response | string |  |   Already up-to-date. 
action_result.summary | string |  |  
action_result.message | string |  |   Repo test_repo pulled successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'delete repo'
Delete a cloned repository

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**repo_url** |  optional  | Repository URL | string |  `github repo` 
**branch** |  optional  | Branch | string |  `github branch` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.repo_url | string |  `github repo`  |  
action_result.parameter.branch | string |  `github branch`  |  
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.summary | string |  |  
action_result.message | string |  |   Successfully deleted repository 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'clone repo'
Clone the repo

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**repo_url** |  optional  | Repository URL | string |  `github repo` 
**branch** |  optional  | Branch | string |  `github branch` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.parameter.repo_url | string |  `github repo`  |  
action_result.parameter.branch | string |  `github branch`  |  
action_result.data.\*.branch_name | string |  |   master 
action_result.data.\*.repo_dir | string |  `file path`  |   /opt/phantom/local_data/app_states/ff116964-86f7-4e29-8763-4462ce0d39a7/test_repo 
action_result.data.\*.repo_name | string |  |   repo2 
action_result.summary | string |  |  
action_result.message | string |  |   Repo test_repo cloned successfully 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1 