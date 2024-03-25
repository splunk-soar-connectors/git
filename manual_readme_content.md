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
