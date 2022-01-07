[comment]: # "Auto-generated SOAR connector documentation"
# Git

Publisher: Splunk  
Connector Version: 2\.0\.8  
Product Vendor: Generic  
Product Name: Git  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 4\.9\.39220  

This app integrates with git and supports common git actions

[comment]: # " File: readme.md"
[comment]: # "  Copyright (c) 2017-2021 Splunk Inc."
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
username and password are required, however, these won't be verified unless they are explicitly
needed to perform the action. If you were to connect to a public repo, for example, the username and
password would only be needed on a **git push** action. When connecting with SSH, the username
should be part of the URI ( **git** @gitrepo).  
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


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Git asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**repo\_uri** |  required  | string | Repo URI
**branch\_name** |  required  | string | Branch Name \(Default\: master\)
**username** |  optional  | string | Username
**password** |  optional  | password | Password
**repo\_name** |  optional  | string | Repo Name

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate credentials provided for connectivity  
[configure ssh](#action-configure-ssh) - Create an RSA Key pair for SSH connectivity  
[list repos](#action-list-repos) - List repos configured/pulled  
[update file](#action-update-file) - Update \(overwrite\) contents of a file in the working directory  
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

This action will generate a new RSA key pair to enable connecting via SSH\. It will return the public key, which you should add to the repo that you wish to connect to\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**force\_new** |  optional  | Force create a new key pair | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.force\_new | boolean | 
action\_result\.data | string | 
action\_result\.summary\.rsa\_pub\_key | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'list repos'
List repos configured/pulled

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.repo\_dirs | string | 
action\_result\.data\.\*\.repos | string | 
action\_result\.summary\.total\_repos | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'update file'
Update \(overwrite\) contents of a file in the working directory

Type: **generic**  
Read only: **False**

This action will overwrite the contents of the existing file with the specified input in the local working directory\.<br>If <b>vault\_id</b> is specified the contents are overwritten from the file in the vault, else from the data in the <b>contents</b> parameter\. The <b>contents</b> parameter can only contain textual data\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file\_path** |  required  | File path in repo to update | string |  `file path` 
**contents** |  optional  | Contents \(text\) of the file | string | 
**vault\_id** |  optional  | Vault ID | string |  `vault id` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.contents | string | 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.parameter\.vault\_id | string |  `vault id` 
action\_result\.data\.\*\.file\_path | string |  `file path` 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'git status'
Get the result of git status

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.staged\.deleted | string |  `file path` 
action\_result\.data\.\*\.staged\.modified | string |  `file path` 
action\_result\.data\.\*\.staged\.new\_file | string |  `file path` 
action\_result\.data\.\*\.staged\.renamed | string | 
action\_result\.data\.\*\.str | string | 
action\_result\.data\.\*\.unstaged\.modified | string |  `file path` 
action\_result\.data\.\*\.untracked\_files | string |  `file path` 
action\_result\.summary\.status | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'delete file'
Delete a file from the local working directory

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file\_path** |  required  | File path in repo to delete | string |  `file path` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.data\.\*\.file\_path | string |  `file path` 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'add file'
Create a file in the local working directory

Type: **generic**  
Read only: **False**

This action will create in the working directory a file with the specified input data\.<br>If <b>vault\_id</b> is specified the contents are picked from the file in the vault, else from the data in the <b>contents</b> parameter\. The <b>contents</b> parameter can only contain textual data\.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**file\_path** |  required  | File path in repo to add | string |  `file path` 
**contents** |  optional  | Contents \(text\) of the file | string | 
**vault\_id** |  optional  | Vault ID | string |  `vault id` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.contents | string | 
action\_result\.parameter\.file\_path | string |  `file path` 
action\_result\.parameter\.vault\_id | string |  `vault id` 
action\_result\.data\.\*\.file\_path | string |  `file path` 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'git commit'
Commit changes

Type: **generic**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**message** |  required  | Commit message \(Default\: committed from phantom\) | string | 
**push** |  optional  | Push to remote after commit | boolean | 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.message | string | 
action\_result\.parameter\.push | boolean | 
action\_result\.data\.\*\.branch\_name | string | 
action\_result\.data\.\*\.commit\_message | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'git push'
Push commits to the remote server

Type: **generic**  
Read only: **False**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.branch\_name | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'git pull'
Pull the repo

Type: **investigate**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.branch\_name | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.data\.\*\.response | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'delete repo'
Delete a cloned repository

Type: **generic**  
Read only: **False**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'clone repo'
Clone the repo

Type: **generic**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.branch\_name | string | 
action\_result\.data\.\*\.repo\_dir | string | 
action\_result\.data\.\*\.repo\_name | string | 
action\_result\.summary | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 